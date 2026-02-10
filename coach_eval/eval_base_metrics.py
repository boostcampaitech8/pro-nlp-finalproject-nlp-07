import os
import sys
from unittest.mock import MagicMock

# Unsloth qwen3 버그 우회
sys.modules["unsloth.models.qwen3"] = MagicMock()
sys.modules["unsloth.models.qwen3_moe"] = MagicMock()

import json
import torch
from tqdm import tqdm
from sklearn.metrics import accuracy_score, classification_report
from unsloth import FastLanguageModel

# =========================
# 환경
# =========================

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

MODEL_ID = "unsloth/Qwen2.5-14B-Instruct-bnb-4bit"
TEST_DATA_PATH = "data/test/final_eval_data.jsonl"
OUTPUT_LOG_PATH = "outputs/eval_base_results.jsonl"

MAX_LEN = 4096
DEVICE = "cuda"

# =========================
# v10 SYSTEM PROMPT (train과 완전 동일)
# =========================

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
# train과 동일한 user prompt 구성
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

# =========================
# JSON 파싱 안전
# =========================

import re

def extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except:
        return None

# =========================
# 메인
# =========================

def main():

    print("🔹 load base model")

    model, tokenizer = FastLanguageModel.from_pretrained(
        MODEL_ID,
        max_seq_length=MAX_LEN,
        load_in_4bit=True,
        dtype=torch.float16
    )

    FastLanguageModel.for_inference(model)
    #model.to(DEVICE)
    model.eval()

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # -------------------------

    if not os.path.exists(TEST_DATA_PATH):
        print("❌ eval 파일 없음:", TEST_DATA_PATH)
        return

    with open(TEST_DATA_PATH, encoding="utf-8") as f:
        samples = [json.loads(x) for x in f if x.strip()]

    print("🔹 eval samples:", len(samples))

    y_true = []
    y_pred = []
    logs = []

    # =========================
    # 추론 루프
    # =========================

    for ex in tqdm(samples):

        gt = bool(ex["intervene"])
        y_true.append(gt)

        msgs = [
            {"role":"system","content":SYSTEM_PROMPT},
            {"role":"user","content":build_user_prompt(ex)}
        ]

        prompt = tokenizer.apply_chat_template(
            msgs,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = tokenizer(prompt, return_tensors="pt").to(DEVICE)

        with torch.no_grad():
            out = model.generate(
                **inputs,
                max_new_tokens=320,
                do_sample=False,
                temperature=0.0,
                eos_token_id=tokenizer.eos_token_id,
                pad_token_id=tokenizer.eos_token_id
            )

        gen_text = tokenizer.decode(
            out[0][inputs.input_ids.shape[1]:],
            skip_special_tokens=True
        )

        pred_obj = extract_json(gen_text)

        if pred_obj is None:
            pred_label = False
            reason = "parse_fail"
            feedback = None
        else:
            pred_label = bool(pred_obj.get("intervene"))
            reason = pred_obj.get("reason")
            feedback = pred_obj.get("feedback")

        y_pred.append(pred_label)

        logs.append({
            "situation": ex["situation_summary"],
            "history": ex["last_5_turns"],
            "user_response": ex["current_user_response"],
            "ground_truth": gt,
            "prediction": pred_label,
            "correct": gt == pred_label,
            "reason": reason,
            "feedback": feedback,
            "raw_generation": gen_text
        })

    # =========================
    # 결과 저장
    # =========================

    os.makedirs(os.path.dirname(OUTPUT_LOG_PATH), exist_ok=True)

    with open(OUTPUT_LOG_PATH, "w", encoding="utf-8") as f:
        for row in logs:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # =========================
    # 리포트
    # =========================

    acc = accuracy_score(y_true, y_pred)

    print("\n" + "="*60)
    print("Coach base Evaluation")
    print("samples:", len(y_true))
    print("accuracy:", round(acc,4))
    print("log saved:", OUTPUT_LOG_PATH)
    print("-"*60)

    print(classification_report(
        y_true,
        y_pred,
        target_names=["NoIntervene","Intervene"],
        zero_division=0
    ))

    print("="*60)


# =========================

if __name__ == "__main__":
    main()