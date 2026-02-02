# app/feedback_client.py
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from persona import ClovaStudioClient, _extract_assistant_text

FINAL_FEEDBACK_SYSTEM = """\
너는 'Mind Gym'의 대화 종료 피드백 생성기다.
사용자가 롤플레잉 연습을 마치고 웹에서 '대화 종료'를 눌렀다.

너의 출력은 서비스에 그대로 노출된다. 반드시 아래 스키마를 지키고 JSON만 출력하라.

목표:
1) 이번 대화에서 드러난 사용자의 커뮤니케이션 성향(패턴)을 요약한다.
2) 대화 전체 요약을 5~7문장으로 제공한다.
3) 피드백을 4가지 축으로 제공한다.
   - 사용자 대화 성향 요약
   - 상황 대응 평가 (목표 달성/리스크/대안)
   - 문장 표현 평가 (톤, 명확성, 공손성, 공격성, 회피성)
   - 다음 행동을 위한 가이드 (다음 세션에서 바로 쓸 문장 + 연습 과제, 난이도 조절 여부)

중요 규칙:
- persona_name, role_description 등 캐릭터 설정은 평가 대상일 뿐 변경/재설정하지 않는다.
- 사용자를 비난하지 말고, 관찰된 패턴과 그 영향, 개선 루틴을 제시한다.
- 근거는 transcript 기반으로 하되, 원문 인용은 1~2문장 이내로 짧게 한다.
- 가능한 한 "바로 실행" 가능한 형태(체크리스트/짧은 문장/다음 행동)로 쓴다.
- 반드시 한국어로 작성한다.

출력 스키마(반드시 이 형태의 JSON):
{
  "user_profile": {
    "traits": [string, ...],
    "tendencies": [string, ...],
    "risk_signals": [string, ...]
  },
  "conversation_summary": string,
  "feedback": {
    "user_tendency_summary": string,
    "situation_response_evaluation": {
      "score": 1|2|3|4|5,
      "good_points": [string, ...],
      "improve_points": [string, ...],
      "notes": string
    },
    "sentence_expression_evaluation": {
      "good_points": [string, ...],
      "improve_points": [string, ...],
      "rewrite_examples": [string, ...]
    },
    "next_action_guide": {
      "copyable_lines": [string, ...],
      "next_drills": [string, ...],
      "homework": [string, ...]
    }
  }
}
"""


def call_final_feedback_clova(
    client: ClovaStudioClient,
    persona_cfg: Dict[str, Any],
    transcript: List[Dict[str, str]],
    coach_history: Optional[List[Dict[str, Any]]] = None,
    router_meta: Optional[Dict[str, Any]] = None,
    temperature: float = 0.2,
    top_p: float = 0.7,
    max_tokens: int = 700,
) -> Dict[str, Any]:
    """
    Synchronous. Call in asyncio.to_thread(...) if needed.
    """
    payload = {
        "persona_cfg": persona_cfg,
        "transcript": transcript[-60:],  # keep bounded
        "coach_history": (coach_history or [])[-40:],
        "router_meta": router_meta or {},
    }

    resp = client.chat_completions(
        messages=[
            {"role": "system", "content": FINAL_FEEDBACK_SYSTEM},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
    )
    txt = _extract_assistant_text(resp).strip()
    try:
        out = json.loads(txt)
    except Exception:
        out = {
            "user_profile": {"traits": [], "tendencies": [], "risk_signals": []},
            "conversation_summary": "피드백 생성에 실패했습니다(비정상 응답).",
            "feedback": {
                "user_tendency_summary": "",
                "situation_response_evaluation": {"score": 3, "good_points": [], "improve_points": [], "notes": f"non_json: {txt[:200]}"},
                "sentence_expression_evaluation": {"good_points": [], "improve_points": [], "rewrite_examples": []},
                "next_action_guide": {"copyable_lines": [], "next_drills": [], "homework": []},
            },
        }
    return out
