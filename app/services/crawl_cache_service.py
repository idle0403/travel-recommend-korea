"""
크롤링 캐시 서비스 - 중복 크롤링 방지 및 1개월 캐시
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.crawl_cache import CrawlCache
from app.core.database import SessionLocal

class CrawlCacheService:
    def __init__(self):
        self.cache_duration = timedelta(days=30)  # 1개월
    
    def get_cached_data(self, search_key: str) -> List[Dict[str, Any]]:
        """캐시된 크롤링 데이터 조회"""
        db = SessionLocal()
        try:
            cached_items = db.query(CrawlCache).filter(
                CrawlCache.search_key == search_key,
                CrawlCache.expires_at > datetime.utcnow()
            ).all()
            
            results = []
            for item in cached_items:
                result = {
                    'name': item.place_name,
                    'address': item.address,
                    'category': item.category,
                    'rating': item.rating,
                    'phone': item.phone,
                    'verified': item.is_verified,
                    'cached': True,
                    'cache_date': item.crawl_date.isoformat()
                }
                
                # JSON 데이터 파싱
                if item.naver_data:
                    result['naver_info'] = json.loads(item.naver_data)
                if item.google_data:
                    result['google_info'] = json.loads(item.google_data)
                if item.blog_data:
                    result['blog_reviews'] = json.loads(item.blog_data)
                
                results.append(result)
            
            return results
        finally:
            db.close()
    
    def save_crawled_data(self, search_key: str, places_data: List[Dict[str, Any]]):
        """크롤링 데이터를 캐시에 저장"""
        db = SessionLocal()
        try:
            expires_at = datetime.utcnow() + self.cache_duration
            
            for place in places_data:
                cache_item = CrawlCache(
                    search_key=search_key,
                    place_name=place.get('name', ''),
                    address=place.get('address', ''),
                    category=place.get('category', ''),
                    rating=str(place.get('rating', '')),
                    phone=place.get('phone', ''),
                    naver_data=json.dumps(place.get('naver_info', {})),
                    google_data=json.dumps(place.get('google_info', {})),
                    blog_data=json.dumps(place.get('blog_reviews', [])),
                    is_verified=place.get('verified', False),
                    expires_at=expires_at
                )
                db.add(cache_item)
            
            db.commit()
        finally:
            db.close()
    
    def cleanup_expired_cache(self):
        """만료된 캐시 데이터 정리"""
        db = SessionLocal()
        try:
            expired_count = db.query(CrawlCache).filter(
                CrawlCache.expires_at <= datetime.utcnow()
            ).delete()
            db.commit()
            return expired_count
        finally:
            db.close()
    
    def generate_search_key(self, city: str, keyword: str) -> str:
        """검색 키 생성"""
        return f"{city}_{keyword}".lower().replace(' ', '_')