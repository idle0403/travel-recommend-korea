"""
크롤링 캐시 모델 - 중복 크롤링 방지용 DB 테이블
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Index
from sqlalchemy.sql import func
from .user import Base

class CrawlCache(Base):
    __tablename__ = "crawl_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    search_key = Column(String(255), nullable=False, index=True)  # "서울_맛집" 형태
    place_name = Column(String(200), nullable=False)
    address = Column(String(500))
    category = Column(String(100))
    rating = Column(String(10))
    phone = Column(String(50))
    
    # 크롤링된 데이터 (JSON 형태로 저장)
    naver_data = Column(Text)  # JSON string
    google_data = Column(Text)  # JSON string
    blog_data = Column(Text)   # JSON string
    
    # 메타데이터
    is_verified = Column(Boolean, default=False)
    crawl_date = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))  # 1개월 후 만료
    
    # 인덱스 설정
    __table_args__ = (
        Index('idx_search_key_date', 'search_key', 'crawl_date'),
        Index('idx_expires_at', 'expires_at'),
    )