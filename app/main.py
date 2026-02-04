from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import API_V1_STR, PROJECT_NAME, APP_ENV, DEBUG
from app.api.v1 import router as api_v1_router
from app.db.database import init_db, check_db_connection


app = FastAPI(
    title=PROJECT_NAME,
    description="Mind GYM backend API",
    version="1.0.0",
    debug=DEBUG
)

# 슬래시 리다이렉트 비활성화
app.router.redirect_slashes = False

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(api_v1_router, prefix=API_V1_STR)


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작"""
    print(f"🚀 {PROJECT_NAME} 시작 중...")
    
    # MySQL 연결 확인
    if not check_db_connection():
        raise RuntimeError("❌ MySQL 연결 실패! .env 파일을 확인하세요.")
    
    # 테이블 생성
    init_db()
    
    print(f"✅ {PROJECT_NAME} 시작 완료!")


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료"""
    print(f"👋 {PROJECT_NAME} 종료")


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": f"{PROJECT_NAME}가 정상 작동 중입니다!",
        "version": "1.0.0",
        "environment": APP_ENV,
        "docs": "/docs",
        "endpoints": {
            "sessions": f"{API_V1_STR}/sessions",
            "agent": f"{API_V1_STR}/agent",
            "feedback": f"{API_V1_STR}/feedback"
        }
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    db_connected = check_db_connection()
    
    return {
        "status": "healthy" if db_connected else "degraded",
        "environment": APP_ENV,
        "database": "mysql",
        "db_connected": db_connected
    }
