import os
import sys
import json
import re
import torch
from unittest.mock import MagicMock

# 1. Unsloth 버그 우회 (기존 로직 유지)
sys.modules["unsloth.models.qwen3"] = MagicMock()
sys.modules["unsloth.models.qwen3_moe"] = MagicMock()

from unsloth import FastLanguageModel


class MindGymCoach:
    _instance = None

    def __new__(cls, *args, **kwargs):
        # 싱글톤 패턴: 인스턴스가 하나만 생성되도록 보장
        if not cls._instance:
            cls._instance = super(MindGymCoach, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_path="shinjipark/qwen2.5_14B_coach_v3"):
        # 이미 모델이 로드되어 있다면 재초기화 방지
        if hasattr(self, "model"):
            return

        print(f"[INFO] MindGym Coach V3 모델 로딩 중... ({model_path})")
        self.device = "cuda"
        self.max_seq_length = 4096

        # 모델 및 토크나이저 로드
        self.model, self.tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_path,
            max_seq_length=self.max_seq_length,
            dtype=torch.float16,
            load_in_4bit=True,
        )
        FastLanguageModel.for_inference(self.model)
        self.model.eval()

        # -----------------------------
        # Heuristic gate settings
        # -----------------------------
        # "이미 충분히 적절한 사용자 답변"이면 intervene를 강제 false로 낮춰
        # 모델 호출 자체를 skip (레이턴시 절감 + 과개입 방지)
        self.good_markers = [
            "죄송", "미안", "실례", "양해", "감사", "고맙",
            "주의하겠습니다", "조심하겠습니다",
            "잘못", "제 책임", "해결하겠", "조치하겠"
        ]

        self.bad_markers = [
            # 반박/도전
            "제가 뭘", "뭘 더", "왜요", "왜 내가", "왜 제가", "말이 되",
            "그럼", "그러니까요?", "뭐가 문제",
            # 무례/공격
            "웃기", "말도 안", "어이가", "진짜", "장난", "까",
            "닥쳐", "꺼져", "미쳤", "헛소리",
            # 협박성(원칙상 강하게 개입)
            "고소", "신고", "경찰", "법적", "소송", "협박",
        ]

        # 서비스에서 rewrite는 feedback만 사용됨(coach_stub가 feedback -> rewrite)
        # signals는 사용하지 않으므로 reason은 빈 문자열로 반환하도록 강제
        self.system_prompt = (
            "당신은 인간 심리와 대화의 뉘앙스를 간파하는 '초고성능 AI 커뮤니케이션 코치'입니다. "
            "사용자의 발화가 단순히 논리적인지를 넘어, 사회적 지능(Social Intelligence)과 품격(Class)을 갖췄는지 심층 분석하세요."
            "\n\n[핵심 목표]"
            "\n- 개입(intervene)은 '자주'가 아니라 '정확히 필요할 때만' 한다."
            "\n- 특히 바로 이전 USER 발화가 이미 적절했고, 현재 USER 발화도 적절하다면 intervene=false로 유지한다."
            "\n- 바로 이전 USER 발화 대비 현재 USER 발화가 '악화'했거나, 명확한 공격성/수동공격/협박이 있을 때만 intervene=true."
            "\n\n[출력 규칙]"
            "\n- JSON 하나만 출력한다. 추가 텍스트/마크다운 금지."
            "\n- service에서는 feedback만 UI에 노출된다."
            "\n- intervene=true일 때 feedback에는 반드시 아래 2가지를 '짧게' 포함한다:"
            "\n  (1) 개입 이유 1줄"
            "\n  (2) 사용자가 그대로 복사해 말할 수 있는 대체 문장 1~2줄"
            "\n- reason 필드는 항상 빈 문자열로 출력한다(서비스에서 signals는 사용하지 않음)."
            "\n- intervene=false면 feedback은 빈 문자열로 출력한다."
            "\n\n[JSON 포맷]"
            "{\n"
            "  \"reason\": \"\",\n"
            "  \"intervene\": true 또는 false,\n"
            "  \"feedback\": \"(intervene=true일 때만) 개입 이유 + 대체 문장\"\n"
            "}"
        )

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

    # -----------------------------
    # Helpers: heuristics
    # -----------------------------
    def _contains_any(self, text: str, markers: list[str]) -> bool:
        t = (text or "").strip()
        if not t:
            return False
        return any(m in t for m in markers)

    def _is_good_enough(self, text: str) -> bool:
        """
        '사과/인정/대안/재발방지' 중심이면 good로 판단.
        너무 공격적인 마커가 섞이면 good로 보지 않는다.
        """
        t = (text or "").strip()
        if not t:
            return False
        if self._contains_any(t, self.bad_markers):
            return False
        return self._contains_any(t, self.good_markers)

    def _is_clearly_bad(self, text: str) -> bool:
        """명확한 공격/반박/협박성 마커가 있으면 bad로 판단."""
        t = (text or "").strip()
        if not t:
            return False
        return self._contains_any(t, self.bad_markers)

    def _get_prev_user_utt(self, turns: list[dict]) -> str:
        """
        last_5_turns 안에서 마지막 USER 발화를 찾는다.
        (current_user_response는 별도 필드로 들어오므로, turns는 이전 히스토리로 보는 게 안전)
        """
        if not isinstance(turns, list):
            return ""
        for m in reversed(turns):
            if not isinstance(m, dict):
                continue
            if (m.get("role") or "").strip() == "user":
                return (m.get("content") or "").strip()
        return ""

    # -----------------------------
    # LLM JSON extraction
    # -----------------------------
    def _extract_json(self, text: str):
        """생성된 텍스트에서 JSON 블록만 안전하게 추출"""
        if not text:
            return None
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            obj = json.loads(text[start : end + 1])
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None

    # -----------------------------
    # Prompt
    # -----------------------------
    def _build_v3_user_prompt(self, data: dict) -> str:
        """
        V3 User Prompt (학습/평가 코드의 헤더형 구조를 서비스에 반영)
        + 바로 이전 USER 발화(prev_user_response) 명시하여,
          '악화했을 때만' intervene하도록 강제.
        """
        situation = data.get("situation_summary", "정보 없음")
        villain_level = data.get("assistant_villain_level", 0)
        turns = data.get("last_5_turns", [])
        current_response = data.get("current_user_response", "")

        prev_user = self._get_prev_user_utt(turns)

        dialogue_txt = "\n".join(
            [
                f"- {'상대방' if t.get('role') == 'assistant' else '사용자'}: {t.get('content', '')}"
                for t in turns
                if isinstance(t, dict)
            ]
        )

        return f"""### [Situation Analysis]
- **Scenario**: {situation}
- **Opponent Intensity**: Lv.{villain_level}

### [Conversation History]
{dialogue_txt}

### [Previous User Response] (immediately before the target)
"{prev_user}"

### [User's Target Response]
"{current_response}"

### [Mission]
Decide intervene=true ONLY IF the [User's Target Response] is clearly problematic OR worse than [Previous User Response].
If the target is already polite/appropriate (apology + responsibility + next action), set intervene=false and output empty feedback.
If intervene=true, provide a short coach message: 1-line reason + 1~2 lines of copyable alternative.
"""

    # -----------------------------
    # Postprocess for service (signals must be empty)
    # -----------------------------
    def _postprocess_for_service(self, obj: dict) -> dict:
        """
        coach_stub는 (reason -> signals), (feedback -> rewrite)로 매핑한다.
        - signals를 비우기 위해 reason은 무조건 ""로 만든다.
        - feedback을 UI에서 바로 쓰는 코치 메시지로 만든다.
        - "이렇게 말해봐:" 같은 접두어가 있으면 제거한다.
        """
        if not isinstance(obj, dict):
            return {"reason": "", "intervene": False, "feedback": ""}

        intervene = bool(obj.get("intervene", False))
        reason = (obj.get("reason") or "").strip()
        feedback = (obj.get("feedback") or "").strip()

        if not intervene:
            return {"reason": "", "intervene": False, "feedback": ""}

        # 접두어 제거 (모델이 임의로 붙이는 케이스 흡수)
        feedback = re.sub(r"^\s*이렇게\s*말해봐\s*[:：]?\s*", "", feedback)

        # reason은 서비스에서 signals로 변환되므로 비우는 대신, feedback에 합쳐서 코치톤 살리기
        if reason and feedback:
            merged = f"개입 이유: {reason}\n{feedback}".strip()
        elif feedback:
            merged = feedback.strip()
        elif reason:
            merged = f"개입 이유: {reason}\n죄송합니다. 제가 놓친 부분이 있었습니다. 다음부터는 이렇게 하겠습니다."
        else:
            merged = "죄송합니다. 제 표현이 거칠었습니다. 상황을 정리해서 다시 말씀드리겠습니다."

        return {"reason": "", "intervene": True, "feedback": merged}

    # -----------------------------
    # Predict
    # -----------------------------
    def predict(self, data: dict) -> dict:
        """
        단일 사용자 데이터를 받아 코칭 결과를 반환합니다.
        data: {
            "situation_summary": str,
            "assistant_villain_level": int,
            "last_5_turns": list,
            "current_user_response": str
        }
        """
        turns = data.get("last_5_turns", []) or []
        current = (data.get("current_user_response") or "").strip()
        prev_user = self._get_prev_user_utt(turns)

        # -----------------------------
        # 1) Heuristic gate (cheap)
        # -----------------------------
        # 현재 답변이 이미 충분히 적절하면: 모델 호출 없이 intervene=false
        # 특히 직전 답변도 적절했고 현재도 적절하면 "개입 과다"를 강하게 줄임
        curr_good = self._is_good_enough(current)
        prev_good = self._is_good_enough(prev_user)
        curr_bad = self._is_clearly_bad(current)

        # 현재가 '좋음'이고(사과/책임/대안), 명확한 bad가 없으면 개입하지 않는다
        if curr_good and not curr_bad:
            return {"reason": "", "intervene": False, "feedback": ""}

        # 직전이 좋았는데 현재가 나빠졌으면(도전/반박/공격), 모델로 정밀 판정
        # (이 케이스에서 intervene가 올라가야 하는 게 자연스러움)
        # 반대로 둘 다 애매하면 모델에게 맡김

        # -----------------------------
        # 2) LLM inference
        # -----------------------------
        user_content = self._build_v3_user_prompt(data)

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_content},
        ]

        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(
            prompt, return_tensors="pt", add_special_tokens=False
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=int(os.getenv("COACH_MAX_NEW_TOKENS", "384")),
                use_cache=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                temperature=float(os.getenv("COACH_TEMPERATURE", "0.01")),
                do_sample=False,
            )

        gen_text = self.tokenizer.decode(
            outputs[0][inputs.input_ids.shape[1] :], skip_special_tokens=True
        )
        obj = self._extract_json(gen_text) or {}

        # -----------------------------
        # 3) Safety: If model tries to over-intervene on okay-ish text, dampen it
        # -----------------------------
        # 모델이 과하게 intervene=true를 주는 경우를 마지막에 한번 더 완화:
        # - current가 bad가 아닌데 intervene=true면, feedback에 "짧은 톤 조정"만 남기거나 false로 내림
        model_intervene = bool(obj.get("intervene", False))
        if model_intervene and (not curr_bad) and curr_good:
            # 이미 적절한데 모델이 개입하려 하면 과개입으로 간주
            return {"reason": "", "intervene": False, "feedback": ""}

        return self._postprocess_for_service(obj)
