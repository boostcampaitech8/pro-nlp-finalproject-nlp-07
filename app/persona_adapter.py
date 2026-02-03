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
    # cfg도 저장해야 /chat/start 이후 /chat/message에서 persona 필드 없이 진행 가능
    return {
        "cfg": cfg_to_dict(session.cfg),
        "transcript": session.transcript,
        "memory_summary": session.memory_summary,
    }


def session_from_state(client, persona_state: dict, fallback_cfg: PersonaConfig):
    """
    Redis에 cfg가 있으면 그걸 사용하고,
    없으면 fallback_cfg를 사용한다.
    """
    stored_cfg = persona_state.get("cfg") if isinstance(persona_state, dict) else None
    if isinstance(stored_cfg, dict) and stored_cfg.get("persona_name") and stored_cfg.get("role_description"):
        cfg = cfg_from_dict(stored_cfg)
    else:
        cfg = fallback_cfg

    session = PersonaSession(client=client, cfg=cfg)
    session.transcript = (persona_state.get("transcript") or []) if isinstance(persona_state, dict) else []
    session.memory_summary = (persona_state.get("memory_summary") or "") if isinstance(persona_state, dict) else ""
    return session
