from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timedelta
from typing import Optional


from app.db.database import get_db
from app.models.message import Message
from app.models.session import ChatSession
from app.schemas.agent import AgentRequest, AgentResponse, SessionStartRequest
from app.api.v1.services.agent_service import AgentService
from app.api.v1.services.session_service import SessionService


router = APIRouter(prefix="/agent", tags=["agent"])

# ✅ 코치 개입 제어 설정 (필요시 조정)
COACH_COOLDOWN_MESSAGES = 6  # 코치 메시지 후 최소 N개 메시지 대기


@router.post("", response_model=AgentResponse)
async def send_message(
    request: AgentRequest,
    db: Session = Depends(get_db)
):
    """에이전트에게 메시지 전송 및 응답 받기"""
    
    # ✅ 1. 세션 소유권 검증
    try:
        session = SessionService.validate_session_ownership(
            session_id=request.session_id,
            user_id=request.user_id,
            db=db
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    
    # ✅ 2. 활성 상태 확인
    if session.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session is not active (status: {session.status})"
        )
    
    # 2. DB에서 persona 정보 가져오기
    persona_name = session.persona_name
    role_description = session.role_description
    difficulty = session.difficulty
    
    print(f"📊 세션 정보 - Persona: {persona_name}, Difficulty: {difficulty}")
    
    # 3. AI 에이전트 응답 생성
    agent_response_data = await AgentService.get_response(
        user_message=request.message,
        session_id=request.session_id,
        persona_name=persona_name,
        role_description=role_description,
        difficulty=difficulty,
        use_supervisor=request.use_supervisor
    )
    
    agent_response_text = agent_response_data.get("text", "")
    coach_data = agent_response_data.get("coach")
    supervisor_data = agent_response_data.get("supervisor")
    
    # coach_data 로그 출력
    if coach_data:
        print(f"🎯 Coach 피드백:")
        print(f"  - intervene: {coach_data.get('intervene')}")
        print(f"  - rewrite: {coach_data.get('rewrite')}")
        print(f"  - signals: {coach_data.get('signals')}")
    
    # ✅ 4. 코치 개입 제어 로직
    coach_should_intervene = False
    
    if coach_data and coach_data.get("intervene"):
        print(f"🎓 코치 개입 감지됨")
        
        # 최근 N개 메시지 조회
        recent_messages = db.query(Message).filter(
            Message.session_id == request.session_id
        ).order_by(
            Message.timestamp.desc()
        ).limit(COACH_COOLDOWN_MESSAGES).all()
        
        # 최근 메시지 중 코치가 있는지 확인
        has_recent_coach = any(msg.role == "coach" for msg in recent_messages)
        
        if has_recent_coach:
            print(f"⏸️ 코치 개입 스킵 (최근 {COACH_COOLDOWN_MESSAGES}개 메시지 내 코치 존재)")
            coach_should_intervene = False
        else:
            print(f"✅ 코치 개입 허용 (최근 {COACH_COOLDOWN_MESSAGES}개 메시지 내 코치 없음)")
            coach_should_intervene = True
    
    # 5. 메시지 저장 (role별로 분리, 순서 보장)
    base_message_id = f"msg_{uuid.uuid4().hex[:12]}"
    base_timestamp = datetime.utcnow()
    
    messages_to_save = []
    
    # ✅ 5-1. User 메시지 저장 (timestamp: base)
    user_message = Message(
        message_id=f"{base_message_id}_user",
        session_id=request.session_id,
        role="user",
        content=request.message,
        timestamp=base_timestamp,
        extra_data={
            "message_number": session.message_count + 1
        }
    )
    messages_to_save.append(user_message)
    
    # ✅ 5-2. Coach 메시지 저장 (조건부: coach_should_intervene=True일 때만)
    if coach_should_intervene:
        coach_content = coach_data.get("rewrite", "")
        coach_signals = coach_data.get("signals", [])
        
        coach_message = Message(
            message_id=f"{base_message_id}_coach",
            session_id=request.session_id,
            role="coach",
            content=coach_content,
            timestamp=base_timestamp + timedelta(milliseconds=1),
            extra_data={
                "signals": coach_signals,
                "message_number": session.message_count + 1
            }
        )
        messages_to_save.append(coach_message)
        print(f"🎓 코치 메시지 저장: {coach_content[:50]}...")
    
    # ✅ 5-3. Persona 메시지 저장 (timestamp: base + 2ms)
    persona_message = Message(
        message_id=f"{base_message_id}_persona",
        session_id=request.session_id,
        role="persona",
        content=agent_response_text,
        timestamp=base_timestamp + timedelta(milliseconds=2),
        extra_data={
            "message_number": session.message_count + 1
        }
    )
    messages_to_save.append(persona_message)
    
    # 일괄 저장
    db.add_all(messages_to_save)
    
    # 6. 세션 메시지 카운트 증가
    SessionService.increment_message_count(session, db)
    
    db.commit()
    
    # ✅ 7. 프론트엔드로 반환 (코치 개입 스킵된 경우 None)
    return {
        "response": agent_response_text,
        "success": True,
        "coach": coach_data if coach_should_intervene else None
    }


@router.post("/start")
async def start_session(
    request: SessionStartRequest,
    db: Session = Depends(get_db)
):
    """세션 시작 - AI가 먼저 말을 건다"""
    
    # ✅ 1. 세션 소유권 검증
    try:
        session = SessionService.validate_session_ownership(
            session_id=request.session_id,
            user_id=request.user_id,
            db=db
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    
    # 2. DB에서 persona 정보 가져오기
    persona_name = session.persona_name
    role_description = session.role_description
    difficulty = session.difficulty
    
    print(f"🎬 세션 시작 - Persona: {persona_name}, Difficulty: {difficulty}")
    
    # 3. AI 세션 시작 (첫 발화 생성)
    start_data = await AgentService.start_session(
        session_id=request.session_id,
        persona_name=persona_name,
        role_description=role_description,
        difficulty=difficulty,
        use_supervisor=request.use_supervisor
    )
    
    opening_text = start_data.get("text", "")
    
    # 4. 시스템 메시지 + 페르소나 첫 발화 저장
    message_id_base = f"msg_{uuid.uuid4().hex[:12]}"
    base_timestamp = datetime.utcnow()
    
    # ✅ 4-1. System 메시지 (timestamp: base)
    system_message = Message(
        message_id=f"{message_id_base}_system",
        session_id=request.session_id,
        role="system",
        content="[세션 시작]",
        timestamp=base_timestamp,
        extra_data={"is_opening": True}
    )
    
    # ✅ 4-2. Persona 첫 발화 (timestamp: base + 1ms)
    persona_message = Message(
        message_id=f"{message_id_base}_persona",
        session_id=request.session_id,
        role="persona",
        content=opening_text,
        timestamp=base_timestamp + timedelta(milliseconds=1),
        extra_data={"is_opening": True}
    )
    
    db.add_all([system_message, persona_message])
    SessionService.increment_message_count(session, db)
    db.commit()
    
    return {
        "session_id": request.session_id,
        "opening_message": opening_text
    }


@router.get("/test-connection")
async def test_agent_connection(
    endpoint: Optional[str] = Query(None, description="테스트할 엔드포인트")
):
    """외부 Agent API 연결 테스트"""
    result = await AgentService.test_connection(endpoint)
    
    if result["status"] == "connected":
        return {
            "message": "✅ Agent API 연결 성공",
            **result
        }
    else:
        return {
            "message": "❌ Agent API 연결 실패",
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
