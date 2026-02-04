import os
from dotenv import load_dotenv

load_dotenv()

# 기본 설정
API_V1_STR = "/api/v1"
PROJECT_NAME = "Chatbot API"

# Agent API 설정
AGENT_API_HOST = os.getenv("AGENT_API_HOST", "http://10.28.228.63:30484")
AGENT_API_KEY = os.getenv("AGENT_API_KEY", "your-api-key-here")

# ✅ MySQL 데이터베이스 설정 (필수)
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# 애플리케이션 설정
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"


def get_database_url() -> str:
    """
    MySQL 데이터베이스 URL 생성
    
    필수 환경변수가 없으면 에러 발생
    """
    if not all([DB_HOST, DB_USER, DB_PASSWORD, DB_NAME]):
        raise ValueError(
            "❌ MySQL 환경변수가 설정되지 않았습니다.\n"
            "필수 값: DB_HOST, DB_USER, DB_PASSWORD, DB_NAME\n"
            ".env 파일을 확인하세요."
        )
    
    return (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        f"?charset=utf8mb4"
    )


# 데이터베이스 URL
DATABASE_URL = get_database_url()

# 프로덕션 환경 여부
IS_PRODUCTION = APP_ENV == "production"


# 설정 출력 (디버그용)
if DEBUG:
    # 비밀번호 마스킹
    masked_url = DATABASE_URL.replace(DB_PASSWORD, "***")
    print(f"📊 데이터베이스: {masked_url}")
    print(f"🤖 Agent API Host: {AGENT_API_HOST}")
    print(f"🌍 환경: {APP_ENV}")
