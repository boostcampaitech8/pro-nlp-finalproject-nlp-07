from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
from typing import Optional

from app.db.database import get_db
from app.models.agent import AgentMessage
from app.models.session import ChatSession
from app.schemas.agent import AgentRequest, AgentResponse
from app.api.v1.services.agent_service import AgentService
from app.api.v1.services.session_service import SessionService

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("", response_model=AgentResponse)
async def send_message(
    request: AgentRequest,
    db: Session = Depends(get_db)
):
    """
    에이전트에게 메시지 전송 및 응답 받기
    
    - **session_id**: 세션 ID (필수)
    - **message** (또는 user_text): 사용자 메시지
    - **template_id**: 템플릿 ID (1: 친한 친구, 2: 무뚝뚝한 점원)
    - **use_supervisor**: Supervisor 검수 사용 여부
    """
    
    # 1. 세션 유효성 검증
    try:
        session = SessionService.validate_session(request.session_id, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    # 2. ✅ AI 에이전트 응답 생성 (새 파라미터)
    agent_response_data = await AgentService.get_response(
        user_message=request.message,
        session_id=request.session_id,
        template_id=request.template_id,
        use_supervisor=request.use_supervisor
    )
    
    agent_response_text = agent_response_data.get("text", "")
    coach_data = agent_response_data.get("coach")
    supervisor_data = agent_response_data.get("supervisor")
    
    # 3. 메시지 저장
    message_id = f"msg_{uuid.uuid4().hex[:12]}"
    
    agent_message = AgentMessage(
        message_id=message_id,
        session_id=request.session_id,
        user_message=request.message,
        agent_response=agent_response_text,
        timestamp=datetime.utcnow(),
        extra_data={
            "scenario_type": session.scenario_type,
            "message_number": session.message_count + 1,
            "template_id": request.template_id,
            "use_supervisor": request.use_supervisor,
            "coach": coach_data,
            "supervisor": supervisor_data
        }
    )
    
    db.add(agent_message)
    
    # 4. 세션 메시지 카운트 증가
    SessionService.increment_message_count(session, db)
    
    db.commit()
    db.refresh(agent_message)
    
    return {
        "response": agent_response_text,
        "success": True,
        "coach": coach_data,
        "supervisor": supervisor_data
    }


@router.post("/start")
async def start_session(
    session_id: str,
    template_id: int = Query(default=1, ge=1, le=2, description="템플릿 ID"),
    use_supervisor: bool = Query(default=False, description="Supervisor 검수 사용"),
    db: Session = Depends(get_db)
):
    """
    세션 시작 - AI가 먼저 말을 건다
    
    - **session_id**: 세션 ID (필수)
    - **template_id**: 1 (친한 친구) 또는 2 (무뚝뚝한 점원)
    - **use_supervisor**: Supervisor 검수 사용 여부
    """
    
    # 1. 세션 유효성 검증
    try:
        session = SessionService.validate_session(session_id, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    # 2. AI 세션 시작 (첫 발화 생성)
    start_data = await AgentService.start_session(
        session_id=session_id,
        template_id=template_id,
        use_supervisor=use_supervisor
    )
    
    opening_text = start_data.get("text", "")
    
    # 3. 첫 발화 저장 (선택)
    message_id = f"msg_{uuid.uuid4().hex[:12]}"
    agent_message = AgentMessage(
        message_id=message_id,
        session_id=session_id,
        user_message="[세션 시작]",
        agent_response=opening_text,
        timestamp=datetime.utcnow(),
        extra_data={
            "is_opening": True,
            "template_id": template_id,
            "use_supervisor": use_supervisor
        }
    )
    
    db.add(agent_message)
    SessionService.increment_message_count(session, db)
    db.commit()
    
    return {
        "session_id": session_id,
        "opening_message": opening_text,
        "template_id": template_id
    }


@router.get("/test-connection")
async def test_agent_connection(
    endpoint: Optional[str] = Query(None, description="테스트할 엔드포인트")
):
    """
    외부 Agent API 연결 테스트
    """
    result = await AgentService.test_connection(endpoint)
    
    if result["status"] == "connected":
        return {
            "message": "✅ Agent API 연결 성공",
            **result
        }
    else:
        return {
            "message": "❌ Agent API 연결 실패 (폴백 모드 사용)",
            **result
        }


@router.get("/api-info")
async def get_agent_api_info():
    """Agent API 설정 정보 조회"""
    info = AgentService.get_api_info()
    return {
        "message": "Agent API 설정 정보",
        **info
    }


@router.get("/templates")
async def get_templates():
    """사용 가능한 템플릿 목록 조회"""
    return {
        "templates": [
            {
                "id": 1,
                "name": "친한 친구",
                "description": "약속 장소에서 기다리다 화가 난 친구",
                "difficulty": 2
            },
            {
                "id": 2,
                "name": "무뚝뚝한 점원",
                "description": "무뚝뚝하지만 규칙을 지키는 점원",
                "difficulty": 2
            }
        ]
    }
