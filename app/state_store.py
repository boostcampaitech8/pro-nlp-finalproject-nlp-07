# app/state_store.py - Redis / Memory State 
from __future__ import annotations
import json
from typing import Any, Dict, Optional

try:
    from redis.asyncio import Redis
except Exception:  # 테스트 환경 등
    Redis = object  # type: ignore


DEFAULT_STATE: Dict[str, Any] = {
    "session_id": None,
    "persona": {
        "cfg": None,          # dict
        "transcript": [],     # list[{"role","content"}]
        "memory_summary": "",
    },
    "meta": {
        "turn": 0,
        "last_user_text": "",
        "last_persona_text": "",
        "last_coach": None,
        "last_supervisor": None,
        "coach_history": [],
        "supervisor_history": [],
    },
}


class StateStore:
    async def load(self, session_id: str) -> Dict[str, Any]:
        raise NotImplementedError

    async def save(self, session_id: str, state: Dict[str, Any]) -> None:
        raise NotImplementedError


class RedisStateStore(StateStore): # 운영용 (Redis에 JSON 저장하는 형태)
    def __init__(self, redis: Redis, ttl_sec: int = 6 * 60 * 60):
        self.redis = redis
        self.ttl_sec = ttl_sec

    def _key(self, session_id: str) -> str:
        return f"mindgym:state:{session_id}"

    async def load(self, session_id: str) -> Dict[str, Any]:
        raw = await self.redis.get(self._key(session_id))
        if not raw:
            st = json.loads(json.dumps(DEFAULT_STATE))
            st["session_id"] = session_id
            return st
        try:
            st = json.loads(raw)
        except Exception:
            st = json.loads(json.dumps(DEFAULT_STATE))
        st["session_id"] = session_id
        return st

    async def save(self, session_id: str, state: Dict[str, Any]) -> None:
        await self.redis.set(
            self._key(session_id),
            json.dumps(state, ensure_ascii=False),
            ex=self.ttl_sec,
        )


class MemoryStateStore(StateStore):
    """테스트/로컬 실행용(외부 의존성 없음)."""
    def __init__(self):
        self._db: Dict[str, Dict[str, Any]] = {}

    async def load(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self._db:
            st = json.loads(json.dumps(DEFAULT_STATE))
            st["session_id"] = session_id
            self._db[session_id] = st
        return json.loads(json.dumps(self._db[session_id]))

    async def save(self, session_id: str, state: Dict[str, Any]) -> None:
        self._db[session_id] = json.loads(json.dumps(state))
