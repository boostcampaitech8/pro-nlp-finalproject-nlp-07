import os
import sys
import json
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

        # V3 SYSTEM PROMPT (학습/평가 코드와 동일하게 유지)
        self.system_prompt = (
            "당신은 인간 심리와 대화의 뉘앙스를 간파하는 '초고성능 AI 커뮤니케이션 코치'입니다. "
            "사용자의 발화가 단순히 논리적인지를 넘어, 사회적 지능(Social Intelligence)과 품격(Class)을 갖췄는지 심층 분석하세요."
            "\n\n[분석 프로토콜: 아래 4단계로 사고한 뒤 결과를 도출할 것]"
            "\n1. **Power Dynamics**: 사용자가 상대에게 위축되었거나(Low Status), 반대로 과도하게 공격적인가(Aggressive)?"
            "\n2. **Tone & Manner**: 비꼬기, 냉소, 수동적 공격성(Passive-Aggressive)이 섞여 있는가?"
            "\n3. **Effectiveness**: 이 대처가 갈등을 해결하는가, 아니면 상황을 악화시키는가?"
            "\n\n[Feedback 작성 원칙: 'intervene'이 true일 경우 아래 지침을 엄수할 것]"
            "\n- **De-escalation**: 갈등을 심화시키는 '법적 대응', '신고', '고소', '협박', '경찰' 등의 위협적 표현은 절대 사용하지 않는다."
            "\n- **Soft but Firm**: 상대의 기분을 불필요하게 상하게 하지 않으면서도, 본인의 의사를 명확히 전달하는 'I-Message(나 전달법)'와 '청유형'을 사용한다."
            "\n- **Refinement**: 사용자의 거친 표현(예: '닥쳐', '고소한다')을 사회적으로 용인되는 표현(예: '말씀이 지나치십니다', '사과해 주시겠습니까')으로 순화한다."
            "\n\n[출력 포맷: 반드시 'reason'을 먼저 작성하여 논리를 전개한 후 'intervene'을 결정할 것]\n"
            "{\n"
            "  \"reason\": \"분석 내용 (상대의 의도 파악 -> 사용자 반응의 뉘앙스 분석 -> 개입 필요성 판단 순으로 서술)\",\n"
            "  \"intervene\": true 또는 false,\n"
            "  \"feedback\": \"위 작성 원칙(순화, 비협박)을 철저히 준수한 수정 대화 제안 (intervene이 false면 null)\"\n"
            "}"
        )

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

    def _extract_json(self, text: str):
        """생성된 텍스트에서 JSON 블록만 안전하게 추출"""
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            return None
        try:
            return json.loads(text[start : end + 1])
        except Exception:
            return None

    def _build_v3_user_prompt(self, data: dict) -> str:
        """
        V3 User Prompt (학습/평가 코드의 헤더형 구조를 서비스에 반영)
        """
        situation = data.get("situation_summary", "정보 없음")
        villain_level = data.get("assistant_villain_level", 0)
        turns = data.get("last_5_turns", [])
        current_response = data.get("current_user_response", "")

        dialogue_txt = "\n".join(
            [
                f"- {'상대방' if t.get('role') == 'assistant' else '사용자'}: {t.get('content', '')}"
                for t in turns
            ]
        )

        return f"""### [Situation Analysis]
- **Scenario**: {situation}
- **Opponent Intensity**: Lv.{villain_level}

### [Conversation History]
{dialogue_txt}

### [User's Target Response]
"{current_response}"

### [Mission]
Analyze the [User's Target Response]. If it contains aggression, sarcasm, or legal threats, intervene immediately and provide a polite, refined alternative."""

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
                # V3는 reason을 포함하므로 너무 짧으면 잘릴 수 있어 절충값 사용
                max_new_tokens=int(os.getenv("COACH_MAX_NEW_TOKENS", "384")),
                use_cache=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                temperature=0.01,
                do_sample=False,
            )

        gen_text = self.tokenizer.decode(
            outputs[0][inputs.input_ids.shape[1] :], skip_special_tokens=True
        )
        return self._extract_json(gen_text)
