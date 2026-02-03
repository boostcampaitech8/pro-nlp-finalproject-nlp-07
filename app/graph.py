# app/graph.py
from __future__ import annotations

import asyncio
from typing import Any, Dict, TypedDict

from langgraph.graph import StateGraph

from persona import PersonaConfig, PersonaSession
from app.persona_adapter import session_from_state, session_to_state
from app.coach_stub import call_coach
from app.supervisor_client import call_supervisor_validate


class GraphState(TypedDict, total=False):
    session_id: str
    user_text: str
    req_meta: Dict[str, Any]

    state: Dict[str, Any]               # persisted state (redis/memory)
    persona_session: PersonaSession

    # supervisor toggle
    use_supervisor: bool
    coach_rerun_count: int
    persona_rerun_count: int

    # coach / persona outputs
    coach_out: Dict[str, Any]
    persona_text: str

    # supervisor output (optional)
    supervisor_out: Dict[str, Any]

    # UI hint for frontend
    ui_flow: Dict[str, Any]


def stamp(s: dict, name: str) -> dict:
    st = s.get("state") or {}
    st.setdefault("meta", {})
    st["meta"]["_trace"] = st["meta"].get("_trace", []) + [name]
    s["state"] = st
    return s


def build_graph(store, router_client, coach_client, persona_client, supervisor_client=None):
    """
    Target execution order (every turn):
      load_state -> coach -> persona -> (optional) supervisor -> save

    Notes
    - router_client is kept in the signature for backward compatibility but is unused.
    - supervisor is a validator: it may rerun persona once and then proceeds.
    """
    g = StateGraph(dict)

    async def load_state_node(s: dict) -> dict:
        st = await store.load(s["session_id"])
        s["state"] = st

        meta = st.setdefault("meta", {})
        meta["_trace"] = []  # turn마다 초기화

        req = s.get("req_meta") or {}

        # persona cfg resolution:
        # - request(req_meta) fields have priority if provided
        # - otherwise fallback to stored cfg in Redis state (from session start or previous turns)
        stored_cfg = (st.get("persona") or {}).get("cfg") if isinstance(st.get("persona"), dict) else None

        def _pick(key: str, default=None):
            if key in req and req.get(key) is not None:
                return req.get(key)
            if isinstance(stored_cfg, dict) and stored_cfg.get(key) is not None:
                return stored_cfg.get(key)
            return default

        persona_name = _pick("persona_name")
        role_description = _pick("role_description")
        difficulty = _pick("difficulty")

        missing = [k for k, v in (("persona_name", persona_name), ("role_description", role_description), ("difficulty", difficulty)) if v is None]
        if missing:
            raise ValueError(f"Missing required persona fields (request or stored): {missing}")

        cfg = PersonaConfig(
            persona_name=str(persona_name),
            role_description=str(role_description),
            difficulty=int(difficulty),
            style_notes=_pick("style_notes", "한국어로 자연스럽고 간결하게."),
            rules=_pick("rules", []) or [],
        )
        persona_state = st.get("persona") or {}
        persona_sess = session_from_state(
            client=persona_client,
            persona_state=persona_state,
            fallback_cfg=cfg,
        )
        # 요청이 우선이므로 cfg를 덮는다.
        persona_sess.cfg = cfg

        s["persona_session"] = persona_sess

        # supervisor toggle (per-request)
        s["use_supervisor"] = bool(req.get("use_supervisor", False))
        s["coach_rerun_count"] = 0
        s["persona_rerun_count"] = 0

        return stamp(s, "load_state")

    async def coach_node(s: GraphState) -> GraphState:
        """coach는 항상 실행."""
        if coach_client is not None:
            coach_out = await coach_client.run(
                user_text=s["user_text"],
                state=s.get("state", {}),
                req_meta=s.get("req_meta", {}),
            )
        else:
            coach_out = await call_coach(s["user_text"], s.get("state", {}))

        s["coach_out"] = coach_out
        return stamp(s, "coach")

    async def persona_node(s: GraphState) -> GraphState:
        """persona는 항상 실행."""
        if "persona_session" not in s:
            raise RuntimeError("persona_session missing: load_state_node did not run or failed")

        persona_sess = s["persona_session"]
        text = await asyncio.to_thread(persona_sess.respond, s["user_text"])
        s["persona_text"] = text
        return stamp(s, "persona")

    async def supervisor_node(s: GraphState) -> GraphState:
        """Optional validator: validate coach/persona separately and rerun each at most once."""

        if not s.get("use_supervisor"):
            s["supervisor_out"] = {"skipped": True}
            return stamp(s, "supervisor")

        if supervisor_client is None:
            s["supervisor_out"] = {"skipped": True, "reason": "no_supervisor_client"}
            return stamp(s, "supervisor")

        st = s.get("state") or {}
        persona_state = st.get("persona") or {}
        persona_cfg = (persona_state.get("cfg") or {}) if isinstance(persona_state, dict) else {}
        transcript_tail = (persona_state.get("transcript") or [])[-10:] if isinstance(persona_state, dict) else []

        sup = await asyncio.to_thread(
            call_supervisor_validate,
            supervisor_client,
            user_text=s.get("user_text", ""),
            persona_cfg=persona_cfg,
            transcript_tail=transcript_tail,
            coach_out=s.get("coach_out"),
            persona_text=s.get("persona_text", ""),
        )
        s["supervisor_out"] = sup

        rerun_executed: Dict[str, bool] = {"coach": False, "persona": False}

        # 1) rerun coach (only if intervene=true)
        coach_block = (sup.get("coach") or {}) if isinstance(sup, dict) else {}
        if bool(coach_block.get("rerun")) and int(s.get("coach_rerun_count", 0)) < 1:
            # coach가 intervene=false면 supervisor_client가 강제로 skip 처리하므로 여기까지 오지 않음
            s["coach_rerun_count"] = int(s.get("coach_rerun_count", 0)) + 1
            hint = coach_block.get("hint")

            # coach 재실행 (힌트는 req_meta로 전달; 실제 coach 모델에서 선택적으로 사용)
            if hint:
                (s.setdefault("req_meta", {}) or {})["coach_system_hint"] = hint

            if coach_client is not None:
                s["coach_out"] = await coach_client.run(
                    user_text=s["user_text"],
                    state=s.get("state", {}),
                    req_meta=s.get("req_meta", {}),
                )
            else:
                s["coach_out"] = await call_coach(s["user_text"], s.get("state", {}))

            rerun_executed["coach"] = True

        # 2) rerun persona
        persona_block = (sup.get("persona") or {}) if isinstance(sup, dict) else {}
        if bool(persona_block.get("rerun")) and int(s.get("persona_rerun_count", 0)) < 1:
            s["persona_rerun_count"] = int(s.get("persona_rerun_count", 0)) + 1

            persona_sess = s["persona_session"]

            # rollback last commit from persona_node (user+assistant)
            try:
                if len(persona_sess.transcript) >= 2:
                    persona_sess.transcript.pop()
                    persona_sess.transcript.pop()
            except Exception:
                pass

            hint = persona_block.get("hint") or "상대역으로만 답하고, 설정/톤을 유지해 다시 말해."
            text = await asyncio.to_thread(persona_sess.respond, s["user_text"], hint)
            s["persona_text"] = text

            rerun_executed["persona"] = True

        if any(rerun_executed.values()):
            s["supervisor_out"] = {**(s.get("supervisor_out") or {}), "rerun_executed": rerun_executed}

        return stamp(s, "supervisor")

    async def update_and_save_node(s: GraphState) -> GraphState:
        st = s.get("state") or {}
        st.setdefault("meta", {})
        st.setdefault("persona", {})

        session_id = s["session_id"]

        st["meta"]["turn"] = int(st["meta"].get("turn", 0)) + 1
        st["meta"]["last_user_text"] = s["user_text"]
        st["meta"]["last_persona_text"] = s.get("persona_text", "")
        # --- keep light histories for end-of-session feedback ---
        coach_out = s.get("coach_out")
        supervisor_out = s.get("supervisor_out")

        st["meta"]["last_coach"] = coach_out
        st["meta"]["last_supervisor"] = supervisor_out

        # Append bounded histories (optional fields; safe for existing stored states)
        meta = st["meta"]
        meta.setdefault("coach_history", [])
        meta.setdefault("supervisor_history", [])

        if coach_out is not None:
            meta["coach_history"].append(coach_out)
            meta["coach_history"] = meta["coach_history"][-30:]

        if supervisor_out is not None and not (isinstance(supervisor_out, dict) and supervisor_out.get("skipped")):
            meta["supervisor_history"].append(supervisor_out)
            meta["supervisor_history"] = meta["supervisor_history"][-30:]

        # Redis에는 멀티턴 유지를 위한 persona transcript/memory만 저장
        st["persona"] = session_to_state(s["persona_session"])

        await store.save(session_id, st)

        # 프론트 UX 힌트: intervene=false면 coach UI는 스킵
        show_order = ["persona"]
        if (s.get("coach_out") or {}).get("intervene"):
            show_order = ["coach", "persona"]

        s["ui_flow"] = {"show_order": show_order, "requires_user_confirm": True}
        s.pop("persona_session", None)
        return stamp(s, "save")

    g.add_node("load_state", load_state_node)
    g.add_node("coach", coach_node)
    g.add_node("persona", persona_node)
    g.add_node("supervisor", supervisor_node)
    g.add_node("save", update_and_save_node)

    g.set_entry_point("load_state")
    g.add_edge("load_state", "coach")
    g.add_edge("coach", "persona")
    g.add_edge("persona", "supervisor")
    g.add_edge("supervisor", "save")

    return g.compile()