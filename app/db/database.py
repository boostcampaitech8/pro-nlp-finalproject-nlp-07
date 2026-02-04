from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import DATABASE_URL, DEBUG

# MySQL 엔진
engine = create_engine(
    DATABASE_URL,
    echo=DEBUG,
    pool_pre_ping=True,  # ✅ 이미 자동 연결 체크 기능
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """데이터베이스 테이블 생성"""
    from app.models import session, message, feedback
    
    try:
        # ✅ create_all이 자동으로 연결 확인
        Base.metadata.create_all(bind=engine)
        print("✅ 데이터베이스 연결 및 테이블 생성 완료")
    except Exception as e:
        print(f"❌ 데이터베이스 초기화 실패: {e}")
        print("📝 확인 사항:")
        print("  - MySQL 서버가 실행 중인지 확인")
        print("  - .env 파일의 DB_HOST, DB_USER, DB_PASSWORD, DB_NAME 확인")
        print("  - 데이터베이스와 사용자가 생성되어 있는지 확인")
        raise


def check_db_connection() -> bool:
    """데이터베이스 연결 확인"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"❌ MySQL 연결 실패: {e}")
        return False
