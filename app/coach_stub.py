# app/coach_stub.py
from __future__ import annotations
import os
import asyncio
from typing import Any, Dict, Optional

_coach_ai = None

def _get_coach():
    global _coach_ai
    if _coach_ai is None:
        from app.coach_model import MindGymCoach
        model_path = os.getenv("COACH_MODEL_PATH", "shinjipark/qwen2.5_14B_coach")
        _coach_ai = MindGymCoach(model_path=model_path)
    return _coach_ai

def _difficulty_1to3(d: int) -> int:
    # persona difficulty(1~5) -> coach 입력(1~3)로 압축
    if d <= 2: return 1
    if d == 3: return 2
    return 3

async def call_coach(user_text: str, state: Dict[str, Any]) -> Dict[str, Any]:
    # 코치 비활성화 모드: 절대 모델 로딩/추론 안 함
    if os.getenv("COACH_ENABLED", "1") != "1":
        return {"intervene": False, "rewrite": "", "examples": [], "signals": []}

    persona_state = state.get("persona", {}) if isinstance(state, dict) else {}
    cfg = persona_state.get("cfg", {}) if isinstance(persona_state, dict) else {}
    transcript = persona_state.get("transcript", []) if isinstance(persona_state, dict) else []

    input_data = {
        "situation_summary": cfg.get("role_description", "상황 정보 없음"),
        "assistant_villain_level": _difficulty_1to3(int(cfg.get("difficulty", 2) or 2)),
        "last_5_turns": transcript[-5:] if transcript else [],
        "current_user_response": user_text,
    }

    coach = _get_coach()

    # GPU 추론은 동기라 이벤트 루프를 막을 수 있으니 thread로 넘김(최소한의 안정성)
    result = await asyncio.to_thread(coach.predict, input_data)

    if not isinstance(result, dict):
        return {"intervene": False, "rewrite": "", "examples": [], "signals": ["coach_parse_fail"]}

    intervene = bool(result.get("intervene", False))
    reason = (result.get("reason") or "").strip()
    feedback = (result.get("feedback") or "").strip()

    # Graph가 기대하는 스키마로 변환
    return {
        "intervene": intervene,
        "rewrite": feedback if intervene else "",
        "examples": [],  # V1이 examples를 따로 안 만들면 빈 배열 유지
        "signals": [reason] if reason else [],
    }
