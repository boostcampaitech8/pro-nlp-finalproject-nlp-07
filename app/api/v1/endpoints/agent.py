from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import uuid4
from app.schemas.chat import ChatMessageCreate, ChatResponse
from app.db.database import get_db
from app.api.v1.services.agent_service import call_agent_api  # ← 올바른 경로

router = APIRouter()

@router.post("", response_model=ChatResponse)
async def agent(
    request: ChatMessageCreate,
    db: Session = Depends(get_db)
):
    """
    사용자 메시지를 받아 Upstage API에 전송하고,
    응답을 파싱해서 반환하는 엔드포인트
    
    요청: {"message": "안녕하세요"}
    응답: {"message": "Upstage 서버 연결 성공 (안녕하세요)"}
    """
    
    print(f"📨 Agent 요청 메시지: {request.message}")
    
    # 고유한 conversation_id 생성 (각 세션마다)
    conversation_id = str(uuid4())
    
    try:
        # 1. 외부 API 호출
        upstage_response = await call_agent_api(
            conversation_id,
            request.message
        )
        
        # 2. 응답 파싱 및 반환 (기존 ChatResponse 스키마 사용)
        return ChatResponse(
            message=upstage_response.response
        )
    
    except Exception as e:
        print(f"❌ Agent 처리 실패: {str(e)}")
        # 에러 발생 시 에러 메시지 반환
        return ChatResponse(
            message=f"오류 발생: {str(e)}"
        )
