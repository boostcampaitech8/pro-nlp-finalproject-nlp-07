import sys
from unittest.mock import MagicMock

sys.modules["unsloth.models.qwen3"] = MagicMock()
sys.modules["unsloth.models.qwen3_moe"] = MagicMock()

import os
import json
import torch
from datasets import Dataset
from dataclasses import dataclass
from dotenv import load_dotenv

from unsloth import FastLanguageModel
from transformers import Trainer, TrainingArguments
from huggingface_hub import login

# =========================
# 환경 설정
# =========================

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

REPO_ID = "shinjipark/Qwen2.5_14B_coach_v10"
LOCAL_DIR = "outputs/Qwen2.5_14B_coach_v10"
MAX_LEN = 4096

SYSTEM_PROMPT = """
당신은 대인관계 커뮤니케이션 코치입니다.
주어진 상황과 대화를 분석하여 사용자의 대응이 적절했는지 판단하십시오.

[판단 기준]
다음 중 하나라도 해당하면 intervene = true:

- 상대의 부당한 요구나 압박에 사용자가 위축됨
- 감정적으로 맞대응하거나 공격적 표현 사용
- 갈등을 회피하기 위해 과잉 사과
- 문제를 더 악화시키는 말투 사용
- 사회성이 결여된 대화법

[출력 규칙]

반드시 JSON만 출력하십시오
설명문, 인사말, 코드블록 절대 금지
JSON 외 텍스트 출력 금지
키 이름을 절대 바꾸지 마십시오

[출력 스키마]
{
"intervene": true 또는 false,
"reason": 한 문장 판단 근거,
"feedback": intervene=false이면 null, true이면 2~4문장 코칭 문장
}
""".strip()

# =========================
# 입력 구성
# =========================

def build_user_prompt(ex):
    dialogue = "\n".join(
        f"- {'상대' if t['role']=='assistant' else '사용자'}: {t['content']}"
        for t in ex["last_5_turns"]
    )

    return f"""
[상황]
{ex["situation_summary"]}

[대화]
{dialogue}

[사용자 반응]
{ex["current_user_response"]}
""".strip()


def build_answer(ex):
    payload = {
        "intervene": bool(ex["intervene"]),
        "reason": ex["reason"].strip(),
        "feedback": ex["coach_feedback"] if ex["intervene"] else None
    }
    return json.dumps(payload, ensure_ascii=False)


# =========================
# Prompt Masking Tokenize
# =========================

def tokenize(example, tokenizer):

    user_text = build_user_prompt(example)
    answer_text = build_answer(example)

    full_text = tokenizer.apply_chat_template([
        {"role":"system","content":SYSTEM_PROMPT},
        {"role":"user","content":user_text},
        {"role":"assistant","content":answer_text},
    ], tokenize=False)

    prompt_text = tokenizer.apply_chat_template([
        {"role":"system","content":SYSTEM_PROMPT},
        {"role":"user","content":user_text},
    ], tokenize=False, add_generation_prompt=True)

    full_ids = tokenizer(
    full_text,
    truncation=True,
    max_length=MAX_LEN
    )["input_ids"]

    prompt_ids = tokenizer(
    prompt_text,
    truncation=True,
    max_length=MAX_LEN
    )["input_ids"]
    
    labels = full_ids.copy()

    # prompt masking
    mask_len = min(len(prompt_ids), len(labels))
    for i in range(mask_len):
        labels[i] = -100

    return {
        "input_ids": full_ids,
        "labels": labels,
        "attention_mask": [1]*len(full_ids)
    }


# =========================
# Padding Collator
# =========================

@dataclass
class Collator:
    pad_id:int
    def __call__(self, batch):
        maxlen = max(len(x["input_ids"]) for x in batch)

        def pad(seq, val):
            return seq + [val]*(maxlen-len(seq))

        return {
            "input_ids": torch.tensor([pad(x["input_ids"], self.pad_id) for x in batch]),
            "labels": torch.tensor([pad(x["labels"], -100) for x in batch]),
            "attention_mask": torch.tensor([pad(x["attention_mask"], 0) for x in batch]),
        }


# =========================
# MAIN
# =========================

def main():

    if HF_TOKEN:
        login(token=HF_TOKEN)

    print("🚀 Qwen2.5 14B Coach v10 Training Start")

    model, tokenizer = FastLanguageModel.from_pretrained(
        "unsloth/Qwen2.5-14B-Instruct-bnb-4bit",
        max_seq_length=MAX_LEN,
        load_in_4bit=True,
        dtype=torch.float16
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        lora_alpha=32,
        target_modules=[
            "q_proj","k_proj","v_proj","o_proj",
            "gate_proj","up_proj","down_proj"
        ],
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth"
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # =========================
    # 데이터 로드
    # =========================

    data = [json.loads(l) for l in open("data/train/coach_train_v10.jsonl", encoding="utf-8")]

    ds = Dataset.from_list(data).map(
    lambda x: tokenize(x, tokenizer),
    num_proc=4,
    remove_columns=list(data[0].keys())
    )
    # =========================
    # Trainer
    # =========================

    trainer = Trainer(
        model=model,
        train_dataset=ds,
        data_collator=Collator(tokenizer.pad_token_id),
        args=TrainingArguments(
            output_dir=LOCAL_DIR,
            per_device_train_batch_size=2,
            gradient_accumulation_steps=4,
            learning_rate=6e-5,
            num_train_epochs=4,
            fp16=True,
            logging_steps=20,
            save_strategy="no",
            optim="adamw_8bit",
            report_to="none"
        )
    )

    trainer.train()

    # =========================
    # 로컬 저장
    # =========================

    model.save_pretrained(LOCAL_DIR)
    tokenizer.save_pretrained(LOCAL_DIR)

    # =========================
    # HF 업로드
    # =========================

    model.config.pad_token_id = tokenizer.pad_token_id

    model.push_to_hub(REPO_ID, private=False)
    tokenizer.push_to_hub(REPO_ID, private=False)

    print("Upload Complete")
    print("HF Repo:", REPO_ID)


if __name__ == "__main__":
    main()