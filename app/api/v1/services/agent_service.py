import httpx
from typing import Optional, Dict, Any
from app.core.config import AGENT_API_HOST, AGENT_API_KEY


class AgentService:
    """AI 에이전트 서비스"""
    
    # ✅ 엔드포인트 정의
    ENDPOINTS = {
        "agent": "/chat/message",
        "start": "/chat/start",
        "feedback": "/chat/feedback",
        "health": "/health"
    }
    
    # 기본 엔드포인트
    DEFAULT_ENDPOINT = ENDPOINTS["agent"]
    
    @staticmethod
    async def get_response(
        user_message: str,
        session_id: str,
        template_id: int = 1,
        use_supervisor: bool = False,
        endpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        외부 Agent API 호출하여 응답 받기
        
        Args:
            user_message: 사용자 메시지
            session_id: 세션 ID
            template_id: 템플릿 ID (1: 친한 친구, 2: 무뚝뚝한 점원)
            use_supervisor: Supervisor 검수 사용 여부
            endpoint: 커스텀 엔드포인트 (기본값: /chat/message)
            
        Returns:
            AI 에이전트 응답 딕셔너리
            {
                "text": "페르소나 응답",
                "coach": {...},
                "supervisor": {...}
            }
        """
        
        # 외부 Agent API 호출 시도
        try:
            return await AgentService._call_external_api(
                user_message, 
                session_id, 
                template_id,
                use_supervisor,
                endpoint
            )
        except Exception as e:
            print(f"⚠️ 외부 API 호출 실패, 폴백 응답 사용: {e}")
            # 폴백: 간단한 응답
            return {
                "text": AgentService._get_fallback_response(user_message, template_id),
                "coach": None,
                "supervisor": None
            }
    
    @staticmethod
    async def _call_external_api(
        user_message: str,
        session_id: str,
        template_id: int,
        use_supervisor: bool,
        endpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        외부 Agent API 호출 (실제 구현)
        """
        # ✅ 엔드포인트 결정
        api_endpoint = endpoint or AgentService.DEFAULT_ENDPOINT
        api_url = f"{AGENT_API_HOST}{api_endpoint}"
        
        print(f"🔗 Agent API 호출: {api_url}")
        print(f"📦 요청 데이터: session_id={session_id}, template_id={template_id}, use_supervisor={use_supervisor}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    api_url,
                    json={
                        "session_id": session_id,
                        "template_id": template_id,
                        "user_text": user_message,
                        "use_supervisor": use_supervisor
                    },
                    headers={
                        "Authorization": f"Bearer {AGENT_API_KEY}",
                        "Content-Type": "application/json"
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                print(f"✅ Agent API 응답: {data}")
                
                # ✅ AI 서버 응답 형식에 맞춰 파싱
                # 응답 예상 형식:
                # {
                #   "session_id": "...",
                #   "persona": {"text": "..."},
                #   "coach": {...},
                #   "supervisor": {...}
                # }
                
                persona_text = ""
                if isinstance(data, dict):
                    # persona.text 추출
                    persona = data.get("persona", {})
                    if isinstance(persona, dict):
                        persona_text = persona.get("text", "")
                    
                    # 응답 구성
                    return {
                        "text": persona_text or data.get("response") or data.get("message") or str(data),
                        "coach": data.get("coach"),
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
    def _get_fallback_response(user_message: str, template_id: int) -> str:
        """
        폴백 응답 생성 (외부 API 실패 시)
        """
        
        # 템플릿별 기본 응답
        fallback_responses = {
            1: {  # 친한 친구
                "greeting": "야, 늦었잖아! 얼마나 기다렸는지 알아?",
                "default": f"'{user_message}'라고? 그래서 뭐?"
            },
            2: {  # 무뚝뚝한 점원
                "greeting": "네, 무엇을 도와드릴까요?",
                "default": f"'{user_message}'에 대해서는 규정을 확인해야 합니다."
            }
        }
        
        # 템플릿별 응답 선택
        responses = fallback_responses.get(template_id, fallback_responses[1])
        
        # 간단한 키워드 매칭
        greetings = ["안녕", "hello", "hi", "안녕하세요", "처음", "시작"]
        if any(keyword in user_message.lower() for keyword in greetings):
            return responses["greeting"]
        
        return responses["default"]
    
    @staticmethod
    async def start_session(
        session_id: str,
        template_id: int = 1,
        use_supervisor: bool = False
    ) -> Dict[str, Any]:
        """
        세션 시작 (AI가 먼저 말을 건다)
        
        Args:
            session_id: 세션 ID
            template_id: 템플릿 ID
            use_supervisor: Supervisor 검수 사용 여부
            
        Returns:
            시작 응답
        """
        api_url = f"{AGENT_API_HOST}{AgentService.ENDPOINTS['start']}"
        
        # 템플릿 정보
        templates = {
            1: {
                "persona_name": "친한 친구",
                "role_description": "너는 약속 장소에서 기다리다 화가 난 친구다. 사용자는 늦게 도착했다.",
                "difficulty": 2
            },
            2: {
                "persona_name": "무뚝뚝한 점원",
                "role_description": "너는 무뚝뚝하지만 규칙을 지키는 점원이다. 사용자는 환불/교환/문의 요청을 한다.",
                "difficulty": 2
            }
        }
        
        template = templates.get(template_id, templates[1])
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    api_url,
                    json={
                        "session_id": session_id,
                        "template_id": template_id,
                        "persona_name": template["persona_name"],
                        "role_description": template["role_description"],
                        "difficulty": template["difficulty"],
                        "use_supervisor": use_supervisor
                    },
                    headers={
                        "Authorization": f"Bearer {AGENT_API_KEY}",
                        "Content-Type": "application/json"
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                # persona.text 추출
                persona = data.get("persona", {})
                persona_text = persona.get("text", "") if isinstance(persona, dict) else ""
                
                return {
                    "text": persona_text,
                    "session_id": data.get("session_id")
                }
                
        except Exception as e:
            print(f"❌ 세션 시작 실패: {e}")
            # 폴백
            fallback_texts = {
                1: "야! 왜 이제 와? 한 시간 넘게 기다렸다고!",
                2: "네, 어서 오세요. 무엇을 도와드릴까요?"
            }
            return {
                "text": fallback_texts.get(template_id, fallback_texts[1]),
                "session_id": session_id
            }
    
    @staticmethod
    async def test_connection(endpoint: Optional[str] = None) -> Dict[str, Any]:
        """
        Agent API 연결 테스트
        """
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
