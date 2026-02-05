import httpx
from typing import Optional, Dict, Any
from app.core.config import AGENT_API_HOST, AGENT_API_KEY


class AgentService:
    """AI 에이전트 서비스"""
    
    ENDPOINTS = {
        "agent": "/chat/message",
        "start": "/chat/start",
        "feedback": "/chat/feedback",
        "health": "/health"
    }
    
    DEFAULT_ENDPOINT = ENDPOINTS["agent"]
    
    @staticmethod
    async def get_response(
        user_message: str,
        session_id: str,
        persona_name: str,
        role_description: str,
        difficulty: int = 2,
        use_supervisor: bool = False,
        endpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """외부 Agent API 호출하여 응답 받기"""
        
        try:
            return await AgentService._call_external_api(
                user_message, 
                session_id, 
                persona_name,
                role_description,
                difficulty,
                use_supervisor,
                endpoint
            )
        except Exception as e:
            print(f"⚠️ 외부 API 호출 실패, 폴백 응답 사용: {e}")
            return {
                "text": AgentService._get_fallback_response(user_message, persona_name),
                "coach": None,
                "supervisor": None
            }
    
    @staticmethod
    async def _call_external_api(
        user_message: str,
        session_id: str,
        persona_name: str,
        role_description: str,
        difficulty: int,
        use_supervisor: bool,
        endpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """외부 Agent API 호출 (실제 구현)"""
        
        api_endpoint = endpoint or AgentService.DEFAULT_ENDPOINT
        # ✅ debug=true 파라미터 추가
        api_url = f"{AGENT_API_HOST}{api_endpoint}?debug=true"
        
        print(f"🔗 Agent API 호출: {api_url}")
        print(f"📦 Persona: {persona_name}, Difficulty: {difficulty}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    api_url,
                    json={
                        "session_id": session_id,
                        # "template_id": 1,
                        "user_text": user_message,
                        "use_supervisor": use_supervisor,
                        # "persona_name": persona_name,
                        # "role_description": role_description,
                        "difficulty": difficulty
                    },
                    headers={
                        "Authorization": f"Bearer {AGENT_API_KEY}",
                        "Content-Type": "application/json"
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                print(f"✅ Agent API 응답 수신")
                
                # ✅ 응답 파싱
                persona_text = ""
                if isinstance(data, dict):
                    persona = data.get("persona", {})
                    if isinstance(persona, dict):
                        persona_text = persona.get("text", "")
                    
                    # ✅ debug.last_coach 파싱
                    coach_detail = None
                    debug_data = data.get("debug", {})
                    if isinstance(debug_data, dict):
                        last_coach = debug_data.get("last_coach", {})
                        if isinstance(last_coach, dict) and last_coach:
                            coach_detail = {
                                "intervene": last_coach.get("intervene", False),
                                "rewrite": last_coach.get("rewrite"),
                                "signals": last_coach.get("signals", [])
                            }
                    
                    return {
                        "text": persona_text or data.get("response") or data.get("message") or str(data),
                        "coach": coach_detail,
                        "supervisor": data.get("supervisor"),
                        "session_id": data.get("session_id")
                    }
                else:
                    return {
                        "text": str(data),
                        "coach": None,
                        "supervisor": None
                    }
                
        except httpx.TimeoutException:
            print(f"❌ Agent API 타임아웃: {api_url}")
            raise
        except httpx.HTTPStatusError as e:
            print(f"❌ Agent API HTTP 에러 {e.response.status_code}: {e.response.text}")
            raise
        except httpx.RequestError as e:
            print(f"❌ Agent API 연결 실패: {api_url} - {e}")
            raise
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
            raise
    
    @staticmethod
    def _get_fallback_response(user_message: str, persona_name: str) -> str:
        """폴백 응답 생성"""
        return f"[{persona_name}] '{user_message}'에 대해 답변드리겠습니다."
    
    @staticmethod
    async def start_session(
        session_id: str,
        persona_name: str,
        role_description: str,
        difficulty: int = 2,
        use_supervisor: bool = False
    ) -> Dict[str, Any]:
        """세션 시작 (AI가 먼저 말을 건다)"""
        
        api_url = f"{AGENT_API_HOST}{AgentService.ENDPOINTS['start']}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    api_url,
                    json={
                        "session_id": session_id,
                        "template_id": 1,
                        "persona_name": persona_name,
                        "role_description": role_description,
                        "difficulty": difficulty,
                        "use_supervisor": use_supervisor
                    },
                    headers={
                        "Authorization": f"Bearer {AGENT_API_KEY}",
                        "Content-Type": "application/json"
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                persona = data.get("persona", {})
                persona_text = persona.get("text", "") if isinstance(persona, dict) else ""
                
                return {
                    "text": persona_text,
                    "session_id": data.get("session_id")
                }
                
        except Exception as e:
            print(f"❌ 세션 시작 실패: {e}")
            return {
                "text": f"[{persona_name}] 안녕하세요!",
                "session_id": session_id
            }
    
    @staticmethod
    async def test_connection(endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Agent API 연결 테스트"""
        api_endpoint = endpoint or AgentService.ENDPOINTS["health"]
        api_url = f"{AGENT_API_HOST}{api_endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(api_url)
                
                return {
                    "status": "connected",
                    "status_code": response.status_code,
                    "host": AGENT_API_HOST,
                    "endpoint": api_endpoint,
                    "full_url": api_url,
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "response": response.json() if response.status_code == 200 else None
                }
                
        except Exception as e:
            return {
                "status": "disconnected",
                "error": str(e),
                "host": AGENT_API_HOST,
                "endpoint": api_endpoint,
                "full_url": api_url
            }
    
    @staticmethod
    def get_api_info() -> Dict[str, Any]:
        """Agent API 설정 정보 반환"""
        return {
            "host": AGENT_API_HOST,
            "available_endpoints": AgentService.ENDPOINTS,
            "default_endpoint": AgentService.DEFAULT_ENDPOINT,
            "default_full_url": f"{AGENT_API_HOST}{AgentService.DEFAULT_ENDPOINT}"
        }
    
    @staticmethod
    def get_endpoint_url(endpoint_key: str) -> str:
        """엔드포인트 키로 전체 URL 가져오기"""
        endpoint = AgentService.ENDPOINTS.get(endpoint_key, AgentService.DEFAULT_ENDPOINT)
        return f"{AGENT_API_HOST}{endpoint}"
