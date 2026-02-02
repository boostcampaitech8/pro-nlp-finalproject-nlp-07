# app/persona_adapter.py - PersonaSession 직렬화/복원 (Redis에 넣기 위해 변환)
from __future__ import annotations
from dataclasses import asdict
from typing import Any, Dict

from persona import PersonaConfig, PersonaSession, ClovaStudioClient


def cfg_to_dict(cfg: PersonaConfig) -> Dict[str, Any]:
    return asdict(cfg)


def cfg_from_dict(d: Dict[str, Any]) -> PersonaConfig:
    return PersonaConfig(**d)


def session_to_state(session: PersonaSession) -> dict:
    # cfg는 저장하지 않거나, 저장해도 "참고용"으로만(권장: 저장 안 함)
    return {
        # "cfg": session.cfg.to_dict(),  # <- 권장: 제거
        "transcript": session.transcript,
        "memory_summary": session.memory_summary,
    }




def session_from_state(client, persona_state: dict, fallback_cfg):
    # cfg는 항상 fallback_cfg만 사용 (Redis cfg 무시)
    session = PersonaSession(client=client, cfg=fallback_cfg)

    session.transcript = (persona_state.get("transcript") or [])
    session.memory_summary = (persona_state.get("memory_summary") or "")
    return session

