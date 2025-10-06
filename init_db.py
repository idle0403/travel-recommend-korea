#!/usr/bin/env python3
"""
데이터베이스 초기화 스크립트
"""

from app.core.database import init_db
from app.services.auth_service import AuthService
from app.core.database import SessionLocal
from app.models.user import User

def create_sample_user():
    """샘플 사용자 생성"""
    db = SessionLocal()
    auth_service = AuthService()
    
    try:
        # 기존 사용자 확인
        existing_user = db.query(User).filter(User.email == "test@example.com").first()
        if existing_user:
            print("샘플 사용자가 이미 존재합니다.")
            return
        
        # 샘플 사용자 생성
        user = auth_service.create_user(
            db=db,
            email="test@example.com",
            username="testuser",
            password="password123",
            full_name="테스트 사용자"
        )
        
        print(f"샘플 사용자 생성 완료: {user.email}")
        
    except Exception as e:
        print(f"사용자 생성 오류: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🗄️ 데이터베이스 초기화 중...")
    
    # 테이블 생성
    init_db()
    print("✅ 데이터베이스 테이블 생성 완료")
    
    # 샘플 사용자 생성
    create_sample_user()
    
    print("🎉 데이터베이스 초기화 완료!")