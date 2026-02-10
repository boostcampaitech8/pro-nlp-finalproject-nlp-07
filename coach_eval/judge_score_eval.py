import json
import re
from openai import OpenAI

client = OpenAI()

JUDGE_PROMPT = open("judge_prompt.txt").read()


# =========================
# A 점수 — 코드 채점
# =========================

def score_A(row):

    raw = row.get("raw_generation","")

    # JSON 블록 추출
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return 0

    try:
        obj = json.loads(m.group())
    except:
        return 0

    keys = {"intervene","reason","feedback"}

    # 키 불일치
    if set(obj.keys()) != keys:
        return 1

    if not isinstance(obj["intervene"], bool):
        return 1

    if not isinstance(obj["reason"], str):
        return 1

    if obj["feedback"] is not None and not isinstance(obj["feedback"], str):
        return 1

    return 2


# =========================
# Judge 입력 구성
# =========================

def build_case_block(row):
    return f"""
[상황]
{row["situation"]}

[대화]
{row["history"]}

[사용자 반응]
{row["user_response"]}

[모델 출력]
intervene={row["prediction"]}
reason={row["reason"]}
feedback={row["feedback"]}
"""


# =========================
# B/C/D judge
# =========================

def judge_bcd(row):

    msg = JUDGE_PROMPT + "\n" + build_case_block(row)

    r = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role":"user","content":msg}]
    )

    text = r.choices[0].message.content

    try:
        s = text.index("{")
        e = text.rindex("}")+1
        return json.loads(text[s:e])
    except:
        return None


# =========================
# 전체 실행
# =========================

def run(path):

    A_scores = []
    B_scores = []
    C_scores = []
    D_scores = []

    for line in open(path, encoding="utf-8"):
        row = json.loads(line)

        # ---- A ----
        A_scores.append(score_A(row))

        # ---- BCD ----
        s = judge_bcd(row)
        if not s:
            continue

        B_scores.append(s["B"])
        C_scores.append(s["C"])
        D_scores.append(s["D"])

    print("\n====", path, "====")

    print("A avg:", round(sum(A_scores)/len(A_scores),4))
    print("B avg:", round(sum(B_scores)/len(B_scores),4))
    print("C avg:", round(sum(C_scores)/len(C_scores),4))
    print("D avg:", round(sum(D_scores)/len(D_scores),4))


# =========================

run("outputs/eval_base_results.jsonl")
run("outputs/eval_v10_results.jsonl")