"""
여행 계획 모델
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .user import Base

class TravelPlan(Base):
    __tablename__ = "travel_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    city = Column(String(100), nullable=False)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    total_cost = Column(Integer, default=0)
    itinerary_json = Column(Text)  # JSON string
    notion_url = Column(String(500))
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계
    user = relationship("User")
    reviews = relationship("TravelReview", back_populates="travel_plan")

class TravelReview(Base):
    __tablename__ = "travel_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    travel_plan_id = Column(Integer, ForeignKey("travel_plans.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    place_name = Column(String(200), nullable=False)
    rating = Column(Float, nullable=False)
    review_text = Column(Text)
    visit_date = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계
    travel_plan = relationship("TravelPlan", back_populates="reviews")
    user = relationship("User")