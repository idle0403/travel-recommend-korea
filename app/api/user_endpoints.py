"""
사용자 관련 API 엔드포인트
"""

from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.services.cache_service import CacheService
from app.services.budget_calculator_service import BudgetCalculatorService
from app.models.user import User
from app.models.travel_plan import TravelPlan, TravelReview

router = APIRouter()
auth_service = AuthService()
cache_service = CacheService()
budget_service = BudgetCalculatorService()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Pydantic 모델
class UserCreate(BaseModel):
    email: str
    username: str
    password: str
    full_name: str = None

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str = None
    is_active: bool

class TravelPlanCreate(BaseModel):
    title: str
    city: str
    itinerary_json: str
    total_cost: int = 0

class ReviewCreate(BaseModel):
    place_name: str
    rating: float
    review_text: str = None

@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """사용자 회원가입"""
    # 이메일 중복 확인
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다")
    
    # 사용자 생성
    new_user = auth_service.create_user(
        db=db,
        email=user.email,
        username=user.username,
        password=user.password,
        full_name=user.full_name
    )
    
    return new_user

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """로그인 및 토큰 발급"""
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 잘못되었습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = auth_service.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """현재 사용자 정보 조회"""
    # 토큰에서 사용자 정보 추출 (간단화)
    user = db.query(User).filter(User.email == "test@example.com").first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return user

@router.post("/travel-plans")
async def save_travel_plan(plan: TravelPlanCreate, db: Session = Depends(get_db)):
    """여행 계획 저장"""
    # 간단화: 첫 번째 사용자로 저장
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    travel_plan = TravelPlan(
        user_id=user.id,
        title=plan.title,
        city=plan.city,
        itinerary_json=plan.itinerary_json,
        total_cost=plan.total_cost
    )
    
    db.add(travel_plan)
    db.commit()
    db.refresh(travel_plan)
    
    return {"message": "여행 계획이 저장되었습니다", "plan_id": travel_plan.id}

@router.get("/travel-plans")
async def get_travel_plans(db: Session = Depends(get_db)):
    """사용자 여행 계획 목록 조회"""
    # 캐시 확인
    cache_key = "user_travel_plans_1"
    cached_plans = cache_service.get(cache_key)
    if cached_plans:
        return cached_plans
    
    # 데이터베이스에서 조회
    plans = db.query(TravelPlan).limit(10).all()
    result = [
        {
            "id": plan.id,
            "title": plan.title,
            "city": plan.city,
            "total_cost": plan.total_cost,
            "created_at": plan.created_at.isoformat() if plan.created_at else None
        }
        for plan in plans
    ]
    
    # 캐시에 저장
    cache_service.set(cache_key, result, ttl=300)
    
    return result

@router.post("/travel-plans/{plan_id}/reviews")
async def add_review(plan_id: int, review: ReviewCreate, db: Session = Depends(get_db)):
    """여행 후기 작성"""
    # 여행 계획 확인
    plan = db.query(TravelPlan).filter(TravelPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="여행 계획을 찾을 수 없습니다")
    
    # 후기 저장
    travel_review = TravelReview(
        travel_plan_id=plan_id,
        user_id=plan.user_id,
        place_name=review.place_name,
        rating=review.rating,
        review_text=review.review_text
    )
    
    db.add(travel_review)
    db.commit()
    
    return {"message": "후기가 등록되었습니다"}

@router.post("/calculate-budget")
async def calculate_budget(itinerary: List[dict], travel_style: str = "moderate"):
    """여행 예산 계산"""
    budget_result = budget_service.calculate_detailed_budget(itinerary, travel_style)
    return budget_result