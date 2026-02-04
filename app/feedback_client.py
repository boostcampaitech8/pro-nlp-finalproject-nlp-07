# app/feedback_client.py
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional


# -----------------------------
# Helpers
# -----------------------------

def _extract_assistant_text(resp: Any) -> str:
    if resp is None:
        return ""
    if isinstance(resp, str):
        return resp

    if isinstance(resp, dict):
        # {"choices":[{"message":{"content":"..."}}]} 형태
        try:
            return resp["choices"][0]["message"]["content"] or ""
        except Exception:
            # 기타 변형 대비
            try:
                return resp["result"]["message"]["content"] or ""
            except Exception:
                return ""

    # object 형태(resp.choices[0].message.content)
    try:
        return resp.choices[0].message.content or ""
    except Exception:
        return ""


def _extract_json_object(text: str) -> Optional[str]:
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start:end + 1]


def _repair_llm_broken_segments(text: str) -> str:
    """
    LLM이 자주 만드는 'JSON 비슷하지만 문법 깨진' 패턴을 복구한다.
    """
    if not text:
        return text

    # 코드펜스 제거
    text = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE).strip()

    def repl_arrow(m: re.Match) -> str:
        a = m.group(1)
        b = m.group(2)
        tail = m.group(3) or ""
        return json.dumps(f"{a} -> {b}{tail}", ensure_ascii=False)

    text = re.sub(
        r'"([^"]+)"\s*->\s*"([^"]+)"([^,\]\}]+)?',
        repl_arrow,
        text,
    )

    def repl_instead(m: re.Match) -> str:
        a = m.group(1)
        b = m.group(2)
        tail = m.group(3) or ""
        return json.dumps(f"{a} 대신 {b}{tail}", ensure_ascii=False)

    text = re.sub(
        r'"([^"]+)"\s*대신\s*"([^"]+)"([^,\]\}]+)?',
        repl_instead,
        text,
    )

    return text


def _safe_json_loads(text: str) -> Optional[Dict[str, Any]]:
    # 0) 1차: 그대로
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass

    # 1) {..}만 추출해서
    js = _extract_json_object(text)
    if js:
        try:
            obj = json.loads(js)
            return obj if isinstance(obj, dict) else None
        except Exception:
            pass

    # 2) 복구 후 재시도
    repaired = _repair_llm_broken_segments(text)
    try:
        obj = json.loads(repaired)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass

    js2 = _extract_json_object(repaired)
    if js2:
        try:
            obj = json.loads(js2)
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None

    return None


def _fallback_feedback(non_json: str) -> Dict[str, Any]:
    return {
        "user_profile": {"traits": [], "tendencies": [], "risk_signals": []},
        "conversation_summary": "피드백 생성에 실패했습니다(비정상 응답).",
        "feedback": {
            "user_tendency_summary": "",
            "situation_response_evaluation": {
                "score": 3,
                "good_points": [],
                "improve_points": [],
                "notes": f"non_json: {non_json[:1500]}",
            },
            "sentence_expression_evaluation": {
                "good_points": [],
                "improve_points": [],
                "rewrite_examples": [],
            },
            "next_action_guide": {
                "copyable_lines": [],
                "next_drills": [],
                "homework": [],
            },
        },
    }


def _build_transcript_views(transcript: List[Dict[str, str]], max_turns: int = 40) -> Dict[str, str]:
    """
    전체 맥락은 유지하되, '교정 대상'은 USER 발화로만 강제할 수 있도록
    transcript를 3가지 뷰로 제공한다.

    - mixed: 전체 대화 (맥락용)
    - user_only: USER 발화만 (교정/평가 대상)
    - assistant_only: ASSISTANT(persona) 발화만 (압박/톤/상황 참고용)

    또한 turn 식별을 위해 T번호를 붙인다.
    """
    if not isinstance(transcript, list):
        return {"mixed": "", "user_only": "", "assistant_only": ""}

    tail = transcript[-max_turns:]
    mixed_lines: List[str] = []
    user_lines: List[str] = []
    asst_lines: List[str] = []

    # T번호는 전체 transcript 기준 tail 시작 인덱스 기반으로 부여
    base = max(1, len(transcript) - len(tail) + 1)

    for i, m in enumerate(tail):
        if not isinstance(m, dict):
            continue
        role = (m.get("role") or "").strip()
        content = (m.get("content") or "").strip()
        if not role or not content:
            continue

        tid = f"T{base + i}"
        if role == "assistant":
            line = f"{tid} ASSISTANT(persona): {content}"
            mixed_lines.append(line)
            asst_lines.append(line)
        elif role == "user":
            line = f"{tid} USER: {content}"
            mixed_lines.append(line)
            user_lines.append(line)
        else:
            mixed_lines.append(f"{tid} {role.upper()}: {content}")

    return {
        "mixed": "\n".join(mixed_lines),
        "user_only": "\n".join(user_lines),
        "assistant_only": "\n".join(asst_lines),
    }


def _build_coach_summary_for_prompt(coach_history: Any, max_items: int = 20) -> str:
    if not coach_history:
        return ""
    items: List[str] = []

    if isinstance(coach_history, list):
        for x in coach_history[-max_items:]:
            if not isinstance(x, dict):
                continue
            items.append(
                f"- turn={x.get('turn')}, intervene={x.get('intervene')}, signals={x.get('signals') or []}, "
                f"rewrite={str(x.get('rewrite') or '')[:120]}, examples_cnt={len(x.get('examples') or [])}"
            )
        return "\n".join(items)

    if isinstance(coach_history, dict):
        return (
            f"- turn={coach_history.get('turn')}, intervene={coach_history.get('intervene')}, signals={coach_history.get('signals') or []}, "
            f"rewrite={str(coach_history.get('rewrite') or '')[:120]}, examples_cnt={len(coach_history.get('examples') or [])}"
        )

    return str(coach_history)[:500]


def _build_coach_interventions_compact(coach_history: Any, max_items: int = 3) -> str:
    """
    intervene=true인 코치 개입만 '짧게' 추려서 피드백에 재사용.
    - 너무 길어지지 않게 rewrite/signal을 컷
    """
    if not coach_history:
        return ""

    items: List[Dict[str, Any]] = []
    if isinstance(coach_history, list):
        for x in coach_history:
            if isinstance(x, dict) and bool(x.get("intervene")):
                items.append(x)
    elif isinstance(coach_history, dict) and bool(coach_history.get("intervene")):
        items = [coach_history]

    if not items:
        return ""

    items = items[-max_items:]
    lines: List[str] = []

    for x in items:
        turn = x.get("turn")
        rewrite = (x.get("rewrite") or "").strip()
        signals = x.get("signals") or []

        if len(rewrite) > 160:
            rewrite = rewrite[:160] + "..."

        sig0 = ""
        if isinstance(signals, list) and signals:
            sig0 = str(signals[0])
            if len(sig0) > 140:
                sig0 = sig0[:140] + "..."

        prefix = f"- turn={turn}: " if turn is not None else "- "
        if sig0:
            lines.append(f"{prefix}signal={sig0} | rewrite={rewrite}")
        else:
            lines.append(f"{prefix}rewrite={rewrite}")

    return "\n".join(lines)


# -----------------------------
# Main API
# -----------------------------

def call_final_feedback_clova(
    client: Any,
    persona_cfg: Dict[str, Any],
    transcript: List[Dict[str, str]],
    coach_history: Any = None,
    supervisor_history: Any = None,
) -> Dict[str, Any]:
    persona_name = (persona_cfg or {}).get("persona_name", "")
    role_description = (persona_cfg or {}).get("role_description", "")

    tx = _build_transcript_views(transcript, max_turns=40)
    transcript_mixed = tx["mixed"]
    transcript_user_only = tx["user_only"]
    transcript_asst_only = tx["assistant_only"]

    coach_text = _build_coach_summary_for_prompt(coach_history, max_items=20)
    coach_interventions = _build_coach_interventions_compact(coach_history, max_items=3)

    system = "Return ONLY valid JSON. No markdown. No extra text."

    # 핵심: 맥락은 mixed로 충분히 주되, 교정 대상은 USER-only로 강제
    # 또한 coach 개입 내용을 '짧게' 리캡해서, 피드백을 고도화하되 길어지지 않게 한다.
    user_prompt = f"""
반드시 유효한 JSON 하나만 출력하라. 설명/추가 텍스트/마크다운 금지.

[중요 규칙: 화자 기준]
- 상황 이해는 mixed(전체 대화)를 활용하되, '교정/평가/수정' 대상은 반드시 USER 발화만이다.
- sentence_expression_evaluation.good_points / improve_points / rewrite_examples는 USER 발화만을 대상으로 작성하라.
- ASSISTANT(persona)의 문장을 '고쳐야 할 문장'으로 포함하거나 rewrite_examples에 넣지 마라.
- 상대(ASSISTANT)의 말투/태도는 상황 평가(situation_response_evaluation)에서 참고할 수 있으나, 사용자 교정 대상으로 취급하지 마라.
- 특정 발화를 지칭할 때 문장을 그대로 인용하지 말고 T번호로만 참조하라. 예: T12 USER

[중요 규칙: 출력 품질/길이]
- 점수는 1~5 정수.
- 리스트 필드는 항상 리스트로.
- 문자열 안에 큰따옴표(")를 직접 넣지 마라.
- 변환표현(->, 대신)을 쓰지 마라. rewrite_examples에는 완성 문장만 넣어라.
- next_action_guide.copyable_lines는 최대 2개만 넣어라.
  가능하면 coach 개입 스니펫의 rewrite를 짧게 재사용하되, 반드시 USER가 말할 문장으로 제시하라.

[컨텍스트]
persona_name: {persona_name}
role_description: {role_description}

[대화 로그 (mixed: 전체 맥락)]
{transcript_mixed}

[USER 발화만 (평가/교정 대상)]
{transcript_user_only}

[ASSISTANT 발화만 (맥락 참고용)]
{transcript_asst_only}

[coach 요약 (있으면 참고)]
{coach_text}

[coach 개입 스니펫 (intervene=true, 최대 3개)]
{coach_interventions}

[출력 스키마]
{{
  "user_profile": {{
    "traits": [string],
    "tendencies": [string],
    "risk_signals": [string]
  }},
  "conversation_summary": string,
  "feedback": {{
    "user_tendency_summary": string,
    "situation_response_evaluation": {{
      "score": int,
      "good_points": [string],
      "improve_points": [string],
      "notes": string
    }},
    "sentence_expression_evaluation": {{
      "good_points": [string],
      "improve_points": [string],
      "rewrite_examples": [string]
    }},
    "next_action_guide": {{
      "copyable_lines": [string],
      "next_drills": [string],
      "homework": [string]
    }}
  }}
}}
""".strip()

    # 1차 호출
    resp = client.chat_completions(
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user_prompt}],
        temperature=0.2,
        top_p=0.8,
        max_tokens=1400,
    )
    raw = _extract_assistant_text(resp).strip()
    data = _safe_json_loads(raw)
    if data is not None:
        return data

    # 2차 repair
    repair_prompt = f"""
직전 출력이 JSON 파싱에 실패했다. 유효한 JSON 하나만 다시 출력하라. 설명 금지.

[금지]
- 큰따옴표(")를 문자열 내부에 직접 넣지 마라.
- ->, 대신 같은 변환표현 금지. rewrite_examples는 완성 문장만.
- ASSISTANT(persona)의 문장을 고칠 문장으로 포함하지 마라.

[대화 로그 (mixed)]
{transcript_mixed}

[USER 발화만]
{transcript_user_only}

[직전 출력]
{raw}
""".strip()

    resp2 = client.chat_completions(
        messages=[{"role": "system", "content": system}, {"role": "user", "content": repair_prompt}],
        temperature=0.1,
        top_p=0.8,
        max_tokens=1400,
    )
    raw2 = _extract_assistant_text(resp2).strip()
    data2 = _safe_json_loads(raw2)
    if data2 is not None:
        return data2

    return _fallback_feedback(non_json=raw2 or raw)
