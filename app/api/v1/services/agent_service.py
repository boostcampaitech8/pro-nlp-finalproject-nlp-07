import httpx
import os
from app.schemas.agent import UpstageResponse
from typing import Dict, Any

# Upstage API 설정
AGENT_API_URL = os.getenv(
    "AGENT_API_URL", 
    ""
)
AGENT_API_KEY = os.getenv("AGENT_API_KEY", "")

async def call_agent_api(conversation_id: str, message: str) -> UpstageResponse:
    """
    Upstage API를 호출하고 응답을 파싱
    
    Args:
        conversation_id: 대화 ID
        message: 사용자 메시지
    
    Returns:
        UpstageResponse: 파싱된 응답
    
    Raises:
        Exception: API 호출 실패 시
    """
    
    # 1. 요청 데이터 준비
    payload = {
        "conversation_id": conversation_id,
        "message": message
    }
    
    # 2. 헤더 설정
    headers = {
        "Content-Type": "application/json",
        # "Authorization": f"Bearer {AGENT_API_KEY}"
    }
    
    print(f"📤 Upstage API 호출: {AGENT_API_URL}")
    print(f"📨 요청: {payload}")
    print(f"🆔 Conversation ID: {conversation_id}")
    
    try:
        # 3. 비동기 HTTP 요청
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                AGENT_API_URL,
                json=payload,
                headers=headers
            )
            
            # 4. 상태 코드 확인
            response.raise_for_status()
            
            # 5. 응답 파싱
            response_data = response.json()
            print(f"📥 응답: {response_data}")
            
            # 6. Pydantic 모델로 검증
            upstage_response = UpstageResponse(**response_data)
            
            return upstage_response
            
    except httpx.HTTPStatusError as e:
        print(f"❌ API 오류 (HTTP {e.response.status_code}): {e.response.text}")
        raise Exception(f"Upstage API 오류: {e.response.status_code}")
    
    except httpx.RequestError as e:
        print(f"❌ 네트워크 오류: {str(e)}")
        raise Exception(f"API 연결 실패: {str(e)}")
    
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {str(e)}")
        raise Exception(f"응답 파싱 실패: {str(e)}")
