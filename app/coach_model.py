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

    def __init__(self, model_path="shinjipark/qwen2.5_14B_coach"):
        # 이미 모델이 로드되어 있다면 재초기화 방지
        if hasattr(self, "model"):
            return

        print(f"[INFO] MindGym Coach V1 모델 로딩 중... ({model_path})")
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

        # V1 시스템 프롬프트
        self.system_prompt = (
            "당신은 대인관계와 커뮤니케이션을 코칭하는 AI 전문가입니다. "
            "사용자가 겪고 있는 상황과 대화 내역을 분석하여, 사용자의 마지막 대처가 적절했는지 판단하세요. "
            "상대방에게 휘둘리거나, 감정적으로 대응하거나, 문제를 회피하는 경우 개입(intervene)해야 합니다. "
            "분석 결과는 반드시 아래 JSON 포맷으로만 출력하세요.\n\n"
            "{\n"
            "  \"intervene\": true 또는 false,\n"
            "  \"reason\": \"판단 이유 및 코칭 원칙 (1문장)\",\n"
            "  \"feedback\": \"사용자에게 건넬 구체적인 조언과 수정 제안 (intervene이 false면 null)\"\n"
            "}"
        )

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

    def _extract_json(self, text):
        """생성된 텍스트에서 JSON 블록만 안전하게 추출"""
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1: return None
        try: return json.loads(text[start:end+1])
        except: return None

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
        situation = data.get("situation_summary", "정보 없음")
        villain_level = data.get("assistant_villain_level", 0)
        turns = data.get("last_5_turns", [])
        current_response = data.get("current_user_response", "")

        # 대화 텍스트 조합
        dialogue_txt = "\n".join([
            f"- {'상대방' if t.get('role') == 'assistant' else '사용자'}: {t.get('content', '')}" 
            for t in turns
        ])

        # 사용자 프롬프트 구성
        user_content = f"""[상황 정보]
- 상황 요약: {situation}
- 상대방 난이도(Lv.1~3): {villain_level}

[대화 흐름 (최근 5턴)]
{dialogue_txt}

[사용자의 현재 반응]
"{current_response}"

[과제]
위 [상황 정보]와 [대화 흐름]을 고려할 때, [사용자의 현재 반응]이 적절한지 판단하고 코칭 리포트를 작성하라."""

        # 1. 메시지 구성
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_content},
        ]
        
        # 2. 토크나이징 및 GPU 이동
        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(prompt, return_tensors="pt", add_special_tokens=False).to(self.device)

        # 3. 모델 추론
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=256,
                use_cache=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                temperature=0.01, # 결정론적 답변을 위해 낮게 설정
                do_sample=False
            )

        # 4. 결과 디코딩 및 파싱
        gen_text = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        return self._extract_json(gen_text)