"""
데이터베이스 설정
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import Base

# 환경변수에서 데이터베이스 URL 가져오기
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password123@localhost:5432/travel_planner")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """데이터베이스 테이블 생성"""
    Base.metadata.create_all(bind=engine)