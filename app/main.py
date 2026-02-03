# app/main.py
from __future__ import annotations

import os
import uuid
import asyncio
from typing import Any, Dict, Optional, List

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse

from persona import load_dotenv_min, ClovaStudioClient, PersonaConfig
from app.state_store import MemoryStateStore, RedisStateStore
from app.persona_adapter import session_from_state, session_to_state
from app.feedback_client import call_final_feedback_clova

# Router client(없으면 None로 동작 가능)
try:
    from app.router_client import ClovaRouterClient
except Exception:
    ClovaRouterClient = None  # type: ignore

# LangGraph
try:
    from app.graph import build_graph
except Exception:
    build_graph = None  # type: ignore


app = FastAPI(title="MindGym GPU Server")

# ---------- 환경 로드 ----------
load_dotenv_min(".env", override=False)

STATE_STORE = os.getenv("STATE_STORE", "memory").strip().lower()
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0").strip()

CLOVA_ENDPOINT = os.getenv("CLOVA_ENDPOINT", "").strip()
CLOVA_API_KEY = os.getenv("CLOVA_API_KEY", "").strip()

# Router env (없으면 router_client=None으로 통과)
CLOVASTUDIO_ROUTER_BASE_URL = os.getenv("CLOVASTUDIO_ROUTER_BASE_URL", "").strip()
CLOVASTUDIO_ROUTER_ID = os.getenv("CLOVASTUDIO_ROUTER_ID", "").strip()
CLOVASTUDIO_ROUTER_VERSION = os.getenv("CLOVASTUDIO_ROUTER_VERSION", "1").strip()

# ---------- Store 초기화 ----------
from redis.asyncio import Redis
REDIS_URL='redis://localhost:6379/0'
redis = Redis.from_url(REDIS_URL, decode_responses=True)
store = RedisStateStore(redis)

# ---------- Clova Persona client ----------
persona_client = None
if CLOVA_ENDPOINT and CLOVA_API_KEY:
    persona_client = ClovaStudioClient(endpoint=CLOVA_ENDPOINT, api_key=CLOVA_API_KEY)
else:
    print("[WARN] CLOVA_ENDPOINT / CLOVA_API_KEY not set. Persona calls will fail.")

# ---------- Router client ----------
router_client = None
if ClovaRouterClient and CLOVASTUDIO_ROUTER_BASE_URL and CLOVASTUDIO_ROUTER_ID and CLOVA_API_KEY:
    try:
        router_client = ClovaRouterClient(
            base_url=CLOVASTUDIO_ROUTER_BASE_URL,
            api_key=CLOVA_API_KEY,
            router_id=CLOVASTUDIO_ROUTER_ID,
            version=CLOVASTUDIO_ROUTER_VERSION,
        )
    except Exception as e:
        print(f"[WARN] Router client init failed -> router disabled. err={e}")
        router_client = None
else:
    router_client = None

# ---------- Coach client ----------
# 아직 코칭 모델 클라이언트가 없으면 None으로 두면 graph 내부에서 stub로 동작하게 설계됨
coach_client = None

# ---------- Persona template (2개) ----------
TEMPLATES: Dict[int, Dict[str, Any]] = {
    1: {
        "persona_name": "친한 친구",
        "role_description": "너는 약속 장소에서 기다리다 화가 난 친구다. 사용자는 늦게 도착했다.",
        "style_notes": "짜증 섞인 말투로 짧게 말한다.",
        "difficulty": 2,
    },
    2: {
        "persona_name": "무뚝뚝한 점원",
        "role_description": "너는 무뚝뚝하지만 규칙을 지키는 점원이다. 사용자는 환불/교환/문의 요청을 한다.",
        "style_notes": "짧고 건조하게 말한다.",
        "difficulty": 2,
    },
}
def _json_safe(obj):
    # dict/list/primitive는 유지, 나머지는 문자열로
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(x) for x in obj]
    return str(obj)


def resolve_persona_fields(
    template_id: Optional[int],
    persona_name: Optional[str],
    role_description: Optional[str],
    difficulty: Optional[int],
    style_notes: Optional[str],
    rules: Optional[List[str]],
) -> Dict[str, Any]:
    """
    우선순위:
    1) request에 직접 값이 있으면 그걸 사용
    2) 없으면 template_id로 채움
    3) 그래도 없으면 에러
    """
    base: Dict[str, Any] = {}
    if template_id is not None and template_id in TEMPLATES:
        base.update(TEMPLATES[template_id])

    # request override
    if persona_name is not None:
        base["persona_name"] = persona_name
    if role_description is not None:
        base["role_description"] = role_description
    if difficulty is not None:
        base["difficulty"] = int(difficulty)
    if style_notes is not None:
        base["style_notes"] = style_notes
    if rules is not None:
        base["rules"] = rules

    missing = [k for k in ("persona_name", "role_description") if not base.get(k)]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required persona fields: {missing}. Provide them or set template_id=1|2.",
        )

    base["difficulty"] = int(base.get("difficulty") or 2)
    base["difficulty"] = max(1, min(5, base["difficulty"]))

    base["style_notes"] = base.get("style_notes") or "한국어로 자연스럽고 간결하게."
    base["rules"] = base.get("rules") or []

    return base


# ---------- LangGraph graph 초기화 ----------
graph = None
graph_init_error: Optional[str] = None

if build_graph and persona_client:
    try:
        graph = build_graph(
            store=store,
            router_client=router_client,
            coach_client=coach_client,
            persona_client=persona_client,
            supervisor_client=persona_client,
        )
    except Exception as e:
        graph_init_error = f"{type(e).__name__}: {str(e)[:200]}"
        graph = None


# ---------- Request schemas ----------
class PersonaRequest(BaseModel):
    session_id: Optional[str] = Field(default=None)
    user_text: str

    template_id: Optional[int] = Field(default=None)
    persona_name: Optional[str] = Field(default=None)
    role_description: Optional[str] = Field(default=None)
    difficulty: Optional[int] = Field(default=2, ge=1, le=5)
    style_notes: Optional[str] = None
    rules: Optional[List[str]] = None


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    user_text: str

    template_id: Optional[int] = None
    persona_name: Optional[str] = None
    role_description: Optional[str] = None
    difficulty: Optional[int] = Field(default=2, ge=1, le=5)
    style_notes: Optional[str] = None
    rules: Optional[list[str]] = None

    end_session: bool = False

    # supervisor 검수 사용 여부 (기본: off)
    use_supervisor: bool = False

    # 추가: 그래프 raw 결과를 응답에 포함할지
    debug_graph_out: bool = False




class StartRequest(BaseModel):
    """세션 시작: 사용자에게서 '상황(파라미터)'을 받고, 페르소나가 먼저 첫 발화를 생성한다."""
    session_id: Optional[str] = None
    template_id: Optional[int] = None
    persona_name: str
    role_description: str
    difficulty: int = Field(default=2, ge=1, le=5)
    style_notes: Optional[str] = None
    rules: Optional[list[str]] = None

    # supervisor 검수 사용 여부 (세션 기본값)
    use_supervisor: bool = False

    # 첫 발화 생성에 추가로 주고 싶은 힌트/상황(선택)
    opening_hint: Optional[str] = None
class FeedbackRequest(BaseModel):
    """웹에서 '대화 종료'를 눌렀을 때 호출 (세션 전체 기반 피드백)."""
    session_id: str

    # persona context가 필요하면 함께 전달 가능(선택)
    template_id: Optional[int] = None
    persona_name: Optional[str] = None
    role_description: Optional[str] = None
    difficulty: Optional[int] = Field(default=2, ge=1, le=5)
    style_notes: Optional[str] = None
    rules: Optional[List[str]] = None



# ---------- 헬스체크 ----------
@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "store": STATE_STORE,
        "clova_ready": bool(persona_client),
        "router_ready": bool(router_client),
        "graph_ready": bool(graph),
        "graph_error": graph_init_error,
    }


# ---------- Persona-only endpoint ----------
@app.post("/persona/message")
async def persona_message(req: PersonaRequest) -> Dict[str, Any]:
    """
    그래프 없이 페르소나만 단독 테스트.
    """
    if persona_client is None:
        raise HTTPException(status_code=500, detail="Clova client not initialized. Set CLOVA_ENDPOINT/CLOVA_API_KEY.")

    session_id = req.session_id or str(uuid.uuid4())

    # 1) load state
    st = await store.load(session_id)
    st.setdefault("meta", {})

    # 2) resolve persona fields
    fields = resolve_persona_fields(
        template_id=req.template_id,
        persona_name=req.persona_name,
        role_description=req.role_description,
        difficulty=req.difficulty,
        style_notes=req.style_notes,
        rules=req.rules,
    )

    cfg = PersonaConfig(
        persona_name=fields["persona_name"],
        difficulty=int(fields["difficulty"]),
        role_description=fields["role_description"],
        style_notes=fields["style_notes"],
        rules=fields["rules"],
    )

    # 3) restore persona session from stored state (cfg는 요청 기준)
    persona_state = st.get("persona") or {}
    persona_session = session_from_state(persona_client, persona_state, cfg)
    persona_session.cfg = cfg

    # 4) call persona (sync -> thread)
    persona_text = await asyncio.to_thread(persona_session.respond, req.user_text)

    # 5) update & save
    st["meta"]["turn"] = int(st["meta"].get("turn", 0)) + 1
    st["meta"]["last_user_text"] = req.user_text
    st["meta"]["last_persona_text"] = persona_text
    st["persona"] = session_to_state(persona_session)

    await store.save(session_id, st)

    return JSONResponse(
        content={
            "session_id": session_id,
            "persona": {"text": persona_text},
            "meta": st.get("meta", {}),
        },
        media_type="application/json; charset=utf-8"
    )


# ---------- LangGraph endpoint ----------


@app.post("/chat/start")
async def chat_start(req: StartRequest):
    """
    세션을 시작한다.
    - user_text 없이 persona_name/role_description/difficulty/style/rules 등 '상황 파라미터'만 받는다.
    - 페르소나가 먼저 첫 발화를 생성해서 반환한다.
    - Redis에 cfg + transcript(assistant 1턴) 저장한다.
    """
    session_id = req.session_id or str(uuid.uuid4())

    # build cfg for persona session
    cfg = {
        "persona_name": req.persona_name,
        "role_description": req.role_description,
        "difficulty": int(req.difficulty),
        "style_notes": req.style_notes or "한국어로 자연스럽고 간결하게.",
        "rules": req.rules or [],
    }

    # load existing state or new
    st = await store.load(session_id)
    st.setdefault("meta", {})
    st.setdefault("persona", {})
    st["session_id"] = session_id

    # create persona session from empty/stored state and overwrite cfg
    persona_state = st.get("persona") or {}
    persona_sess = session_from_state(
        client=persona_client,
        persona_state=persona_state,
        fallback_cfg=PersonaConfig(**cfg),
    )
    persona_sess.cfg = PersonaConfig(**cfg)

    # persona speaks first
    opening_text = await asyncio.to_thread(lambda: persona_sess.open(system_hint=req.opening_hint))

    # update state (do not increment turn; this is pre-turn)
    st["persona"] = session_to_state(persona_sess)
    st["meta"]["turn"] = int(st["meta"].get("turn", 0))  # keep as-is
    st["meta"]["last_user_text"] = ""
    st["meta"]["last_persona_text"] = opening_text
    st["meta"]["use_supervisor_default"] = bool(req.use_supervisor)

    await store.save(session_id, st)

    return {
        "session_id": session_id,
        "persona": {"text": opening_text},
        "debug": {"turn": st["meta"].get("turn", 0), "started": True} if getattr(req, "template_id", None) is not None else {"started": True},
    }
    
@app.post("/chat/message")
async def chat_message(req: ChatRequest, debug: bool = Query(default=False)) -> Dict[str, Any]:
    if graph is None:
        raise HTTPException(status_code=500, detail="LangGraph not initialized. Use /persona/message or configure graph.")
    if persona_client is None:
        raise HTTPException(status_code=500, detail="Clova client not initialized. Set CLOVA_ENDPOINT/CLOVA_API_KEY.")

    session_id = req.session_id or str(uuid.uuid4())

    # 0) 먼저 저장된 상태 로드 (start에서 cfg 저장해두었으므로 여기서 보완)
    st = await store.load(session_id)
    st = st or {}
    persona_state = st.get("persona") or {}
    stored_cfg = persona_state.get("cfg") or {}
    meta = st.get("meta") or {}

    # 1) 세션 기본 supervisor 설정(start에서 저장했으면) 적용
    #    - request에 명시하면 그 값을 우선
    if req.use_supervisor is False and bool(meta.get("use_supervisor_default")):
        # 프론트가 use_supervisor를 명시적으로 false로 내린 게 아니라
        # 기본값(false) 그대로 온 경우에만 세션 기본값을 적용
        req.use_supervisor = True

    # 2) persona 필드 병합 우선순위:
    #    request 명시값 > template_id > stored_cfg
    #    (stored_cfg가 없으면 template/request로 반드시 채워야 함)
    merged: Dict[str, Any] = {}

    # 2-1) stored_cfg 먼저
    if isinstance(stored_cfg, dict):
        merged.update(stored_cfg)

    # 2-2) template 적용(있으면 덮어쓰기)
    if req.template_id is not None and req.template_id in TEMPLATES:
        merged.update(TEMPLATES[req.template_id])

    # 2-3) request 값으로 최종 덮어쓰기
    if req.persona_name is not None:
        merged["persona_name"] = req.persona_name
    if req.role_description is not None:
        merged["role_description"] = req.role_description
    if req.difficulty is not None:
        merged["difficulty"] = int(req.difficulty)
    if req.style_notes is not None:
        merged["style_notes"] = req.style_notes
    if req.rules is not None:
        merged["rules"] = req.rules

    # 3) 필수값 최종 검증
    missing = [k for k in ("persona_name", "role_description") if not merged.get(k)]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required persona fields: {missing}. Provide them, or call /chat/start first, or set template_id=1|2.",
        )

    # 4) 기본값/범위 보정
    merged["difficulty"] = int(merged.get("difficulty") or 2)
    merged["difficulty"] = max(1, min(5, merged["difficulty"]))
    merged["style_notes"] = merged.get("style_notes") or "한국어로 자연스럽고 간결하게."
    merged["rules"] = merged.get("rules") or []

    # 5) graph에 전달할 req_meta 구성
    #    - 그래프에서 load_state가 stored cfg를 쓰더라도, 여기서 merged를 넘기면 더 안정적
    req_meta: Dict[str, Any] = {
        "persona_name": merged["persona_name"],
        "role_description": merged["role_description"],
        "difficulty": int(merged["difficulty"]),
        "style_notes": merged["style_notes"],
        "rules": merged["rules"],
        "use_supervisor": bool(req.use_supervisor),
    }

    out = await graph.ainvoke({
        "session_id": session_id,
        "user_text": req.user_text,
        "req_meta": req_meta,
    }) or {}

    # ---- 1) out에서 파생되는 값들 ----
    coach_out = out.get("coach_out") or out.get("coach") or {}
    supervisor_out = out.get("supervisor_out") or out.get("supervisor") or {}

    # persona_text 추출: (1) direct key -> (2) persona.text -> (3) state transcript tail
    persona_text = out.get("persona_text") or ""
    if not persona_text:
        persona_text = ((out.get("persona") or {}) if isinstance(out.get("persona"), dict) else {}).get("text") or ""

    if not persona_text:
        st2 = out.get("state") or {}
        if isinstance(st2, dict):
            persona_state2 = st2.get("persona") or {}
            if isinstance(persona_state2, dict):
                transcript = persona_state2.get("transcript") or []
                if isinstance(transcript, list) and transcript:
                    last = transcript[-1]
                    if isinstance(last, dict) and last.get("role") == "assistant":
                        persona_text = last.get("content", "") or ""

    # ---- 2) 응답 구성 ----
    resp: Dict[str, Any] = {
        "session_id": session_id,
        "coach": coach_out,
        "persona": {"text": persona_text},
        "supervisor": supervisor_out,
    }

    # --- end-of-session feedback (optional) ---
    if bool(req.end_session):
        # load the latest persisted state (graph saved already)
        st_latest = await store.load(session_id)
        persona_state_latest = (st_latest.get("persona") or {}) if isinstance(st_latest, dict) else {}
        persona_cfg = (persona_state_latest.get("cfg") or {}) if isinstance(persona_state_latest, dict) else {}
        transcript_latest = (persona_state_latest.get("transcript") or []) if isinstance(persona_state_latest, dict) else []
        meta_latest = (st_latest.get("meta") or {}) if isinstance(st_latest, dict) else {}
        coach_history = meta_latest.get("coach_history") if isinstance(meta_latest, dict) else None

        feedback = await asyncio.to_thread(
            call_final_feedback_clova,
            persona_client,
            persona_cfg or {},
            transcript_latest,
            coach_history,
            None,
        )
        resp["final_feedback"] = feedback

    # ---- 3) debug 출력 ----
    if debug:
        st_dbg = out.get("state") or {}
        meta_dbg = st_dbg.get("meta") if isinstance(st_dbg, dict) else None
        persona_state_dbg = (st_dbg.get("persona") or {}) if isinstance(st_dbg, dict) else {}
        transcript_dbg = persona_state_dbg.get("transcript") or []

        resp["debug"] = {
            "turn": (meta_dbg or {}).get("turn"),
            "trace": (meta_dbg or {}).get("_trace", []),
            "transcript_tail": transcript_dbg[-4:],
            "last_coach": (meta_dbg or {}).get("last_coach"),
            "last_supervisor": (meta_dbg or {}).get("last_supervisor"),
        }

    return JSONResponse(
        content=resp,
        media_type="application/json; charset=utf-8"
    )


@app.post("/chat/feedback")
async def chat_feedback(req: FeedbackRequest) -> Dict[str, Any]:
    session_id = req.session_id
    if not session_id:
        raise HTTPException(status_code=422, detail="session_id is required")

    # 1) 세션 상태 로드
    st = await store.load(session_id)
    if not st:
        # 없는 세션이면 피드백 생성 금지
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    persona_state = st.get("persona") or {}
    transcript = persona_state.get("transcript") or []
    cfg = persona_state.get("cfg") or {}

    # 2) transcript 유효성 체크
    if not isinstance(transcript, list) or len(transcript) == 0:
        raise HTTPException(status_code=422, detail="No transcript found for session (empty conversation).")

    # USER 발화가 1개 이상 있는지 체크 (권장)
    user_turns = [m for m in transcript if isinstance(m, dict) and m.get("role") == "user" and (m.get("content") or "").strip()]
    if len(user_turns) == 0:
        raise HTTPException(status_code=422, detail="No user turns found. Feedback requires at least 1 user message.")

    # 3) coach_history(있으면)
    meta = st.get("meta") or {}
    coach_history = meta.get("coach_history")

    # 4) feedback 생성
    feedback = await asyncio.to_thread(
        call_final_feedback_clova,
        persona_client,
        cfg or {},
        transcript,
        coach_history,
        None,
    )

    return JSONResponse(
        content={"session_id": session_id, "final_feedback": feedback},
        media_type="application/json; charset=utf-8"
    )

