# tests/test_graph_memory.py
import json
import pytest

from app.state_store import MemoryStateStore
from app.graph import build_graph
from persona import PersonaConfig, PersonaSession


class FakeClovaClient:
    def __init__(self, mode: str):
        self.mode = mode  # "persona" or "supervisor"

    def chat_completions(self, messages, temperature=0.2, top_p=0.7, max_tokens=256):
        sys = messages[0]["content"]
        user = messages[-1]["content"]

        if self.mode == "supervisor":
            # 항상 difficulty=3로 올리라고 지시하는 JSON
            out = {
                "persona_update": {"difficulty": 3, "persona_name": None, "role_description": None, "style_notes": None, "rules": None},
                "notes": "test supervisor",
            }
            return {"result": {"message": {"content": json.dumps(out, ensure_ascii=False)}}}

        # persona: 그냥 고정 응답
        return {"result": {"message": {"content": "FAKE_PERSONA_REPLY"}}}


@pytest.mark.asyncio
async def test_langgraph_end_to_end_memory_store():
    store = MemoryStateStore()
    persona_client = FakeClovaClient("persona")
    supervisor_client = FakeClovaClient("supervisor")

    graph = build_graph(store, persona_client, supervisor_client)

    session_id = "s1"
    out = await graph.ainvoke({
        "session_id": session_id,
        "user_text": "안녕하세요",
        "req_meta": {"persona_name": "친한 친구", "difficulty": 1, "role_description": "친구 역할"},
    })

    assert out["persona_text"] == "FAKE_PERSONA_REPLY"
    assert out["supervisor_out"]["persona_update"]["difficulty"] == 3

    print("=== GRAPH OUTPUT ===")
    print(out)
    
    # 저장된 state 확인
    st = await store.load(session_id)
    print("=== STORED STATE ===")
    print(st)
    assert st["meta"]["turn"] == 1
    assert st["meta"]["last_persona_text"] == "FAKE_PERSONA_REPLY"
    # transcript에 user/assistant가 누적됐는지(기존 PersonaSession.respond가 append) :contentReference[oaicite:4]{index=4}
    assert len(st["persona"]["transcript"]) >= 2
