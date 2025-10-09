"""
크롤링 캐시 서비스 - 중복 크롤링 방지 및 1개월 캐시 (메모리 기반)
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

class CrawlCacheService:
    def __init__(self):
        self.cache_duration = timedelta(days=30)  # 1개월
        self._memory_cache = {}  # 메모리 캐시
    
    def get_cached_data(self, search_key: str) -> List[Dict[str, Any]]:
        """캐시된 크롤링 데이터 조회 (메모리 기반)"""
        if search_key not in self._memory_cache:
            return []
        
        cache_entry = self._memory_cache[search_key]
        
        # 만료 확인
        if datetime.now() > cache_entry['expires_at']:
            del self._memory_cache[search_key]
            return []
        
        return cache_entry['data']
    
    def save_crawled_data(self, search_key: str, places_data: List[Dict[str, Any]]):
        """크롤링 데이터를 캐시에 저장 (메모리 기반)"""
        expires_at = datetime.now() + self.cache_duration
        
        # 캐시 데이터 정리
        cached_places = []
        for place in places_data:
            cached_place = {
                'name': place.get('name', ''),
                'address': place.get('address', ''),
                'category': place.get('category', ''),
                'rating': place.get('rating', ''),
                'phone': place.get('phone', ''),
                'verified': place.get('verified', False),
                'cached': True,
                'cache_date': datetime.now().isoformat(),
                'naver_info': place.get('naver_info', {}),
                'google_info': place.get('google_info', {}),
                'blog_reviews': place.get('blog_reviews', [])
            }
            cached_places.append(cached_place)
        
        self._memory_cache[search_key] = {
            'data': cached_places,
            'expires_at': expires_at,
            'created_at': datetime.now()
        }
        
        print(f"💾 캐시 저장: {search_key} ({len(cached_places)}개 장소)")
    
    def cleanup_expired_cache(self):
        """만료된 캐시 데이터 정리"""
        expired_keys = []
        current_time = datetime.now()
        
        for key, cache_entry in self._memory_cache.items():
            if current_time > cache_entry['expires_at']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._memory_cache[key]
        
        return len(expired_keys)
    
    def generate_search_key(self, city: str, keyword: str) -> str:
        """검색 키 생성"""
        return f"{city}_{keyword}".lower().replace(' ', '_')
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        total_entries = len(self._memory_cache)
        total_places = sum(len(entry['data']) for entry in self._memory_cache.values())
        
        return {
            'total_cache_entries': total_entries,
            'total_cached_places': total_places,
            'cache_keys': list(self._memory_cache.keys())
        }