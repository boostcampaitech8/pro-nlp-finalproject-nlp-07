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

    주요 타겟:
      - "A" -> "B" (문자열 밖 화살표)
      - "A" 대신 "B" 로 ... (문자열 안에 따옴표를 그대로 써서 깨짐)
    전략:
      - 위 패턴이 나오면, 해당 구간(패턴+뒤 꼬리)을 통째로 "하나의 문자열"로 json.dumps로 감싼다.
      - 이렇게 하면 내부 따옴표/화살표가 모두 문자열 내부로 들어가 JSON 파싱이 가능해진다.
    """
    if not text:
        return text

    # 코드펜스 제거
    text = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE).strip()

    # 1) "A" -> "B" + 뒤에 이어지는 꼬리(, ] } 전까지)를 통째로 하나의 JSON 문자열로 만들기
    #    예: "x" -> "y" 로 바꿔 말하기   =>  "x -> y 로 바꿔 말하기"
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

    # 2) "A" 대신 "B" + 꼬리(, ] } 전까지)를 통째로 하나의 JSON 문자열로 만들기
    #    예: "x" 대신 "y" 로 바꿔 말하기 => "x 대신 y 로 바꿔 말하기"
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

    # 3) 혹시 남아있는 '이중 따옴표 조각'을 줄이기 위해, 아래처럼 "A" 로 바꿔 등도 처리 (옵션)
    #    단, 이미 1)2)에서 대부분 잡힘.
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


def _build_transcript_for_prompt(transcript: List[Dict[str, str]], max_turns: int = 40) -> str:
    if not isinstance(transcript, list):
        return ""
    tail = transcript[-max_turns:]
    lines: List[str] = []
    for m in tail:
        if not isinstance(m, dict):
            continue
        role = (m.get("role") or "").strip()
        content = (m.get("content") or "").strip()
        if not role or not content:
            continue
        if role == "assistant":
            tag = "ASSISTANT(persona)"
        elif role == "user":
            tag = "USER"
        else:
            tag = role.upper()
        lines.append(f"{tag}: {content}")
    return "\n".join(lines)


def _build_coach_summary_for_prompt(coach_history: Any, max_items: int = 20) -> str:
    if not coach_history:
        return ""
    items: List[str] = []

    if isinstance(coach_history, list):
        for x in coach_history[-max_items:]:
            if not isinstance(x, dict):
                continue
            items.append(
                f"- intervene={x.get('intervene')}, signals={x.get('signals') or []}, "
                f"rewrite={str(x.get('rewrite') or '')[:120]}, examples_cnt={len(x.get('examples') or [])}"
            )
        return "\n".join(items)

    if isinstance(coach_history, dict):
        return (
            f"- intervene={coach_history.get('intervene')}, signals={coach_history.get('signals') or []}, "
            f"rewrite={str(coach_history.get('rewrite') or '')[:120]}, examples_cnt={len(coach_history.get('examples') or [])}"
        )

    return str(coach_history)[:500]


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

    transcript_text = _build_transcript_for_prompt(transcript, max_turns=40)
    coach_text = _build_coach_summary_for_prompt(coach_history, max_items=20)

    system = "Return ONLY valid JSON. No markdown. No extra text."

    # 프롬프트도 최대한 안전하게: 따옴표/화살표 사용 금지
    user_prompt = f"""
반드시 **유효한 JSON 하나만** 출력하라. 설명/추가 텍스트/마크다운 금지.

[중요 규칙]
- user_profile은 USER 발화만 보고 추론하라. ASSISTANT(persona)의 말투/태도는 user_profile에 포함하지 마라.
- 점수는 1~5 정수.
- 리스트 필드는 항상 리스트로.
- 문자열 안에 큰따옴표(")를 직접 넣지 마라.
- 변환표현(->, 대신)을 쓰지 마라. rewrite_examples에는 "완성 문장"만 넣어라.

[컨텍스트]
persona_name: {persona_name}
role_description: {role_description}

[대화 로그]
{transcript_text}

[coach 요약(있으면 참고)]
{coach_text}

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

    # 2차 repair: JSON만 다시 (그래도 깨지면 파서가 복구)
    repair_prompt = f"""
직전 출력이 JSON 파싱에 실패했다. **유효한 JSON 하나만** 다시 출력하라. 설명 금지.

[금지]
- 큰따옴표(")를 문자열 내부에 직접 넣지 마라.
- ->, 대신 같은 변환표현 금지. rewrite_examples는 완성 문장만.

[대화 로그]
{transcript_text}

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
