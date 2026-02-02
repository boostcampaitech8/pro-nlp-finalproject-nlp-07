# app/coach_stub.py - 코치 모델
from __future__ import annotations
from typing import Any, Dict

async def call_coach(user_text: str, state: Dict[str, Any]) -> Dict[str, Any]:
    # TODO: 로컬 LLM 호출로 교체 - 코칭 모델 호출 자리
    return {
        "intervene": False,
        "rewrite": "",
        "examples": [],
        "signals": [],
    }
