"""
Redis 캐시 서비스

메모리 캐시를 대체하여 서버 재시작 후에도 캐시 유지
30일 TTL로 크롤링 데이터 영구 보관
"""

import json
import redis
from datetime import timedelta
from typing import Dict, Any, List, Optional
import os


class RedisCacheService:
    """Redis 기반 캐시 서비스"""
    
    def __init__(self):
        # Redis 연결 설정
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_password = os.getenv('REDIS_PASSWORD', None)
        
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                decode_responses=True,
                socket_connect_timeout=2
            )
            # 연결 테스트
            self.redis_client.ping()
            self.redis_available = True
            print(f"✅ Redis 연결 성공: {redis_host}:{redis_port}")
        except Exception as e:
            print(f"⚠️ Redis 연결 실패: {e}")
            print(f"   메모리 캐시로 폴백합니다.")
            self.redis_available = False
            self._memory_fallback = {}  # 메모리 폴백
        
        self.cache_duration = timedelta(days=30)
        self.ttl_seconds = int(self.cache_duration.total_seconds())
    
    def get_cached_data(self, search_key: str) -> List[Dict[str, Any]]:
        """캐시된 크롤링 데이터 조회"""
        cache_key = f"crawl:{search_key}"
        
        if self.redis_available:
            try:
                cached_json = self.redis_client.get(cache_key)
                if cached_json:
                    data = json.loads(cached_json)
                    print(f"   ✅ Redis 캐시 히트: {search_key}")
                    return data
                else:
                    return []
            except Exception as e:
                print(f"   ⚠️ Redis 조회 오류: {e}, 메모리 폴백")
                return self._memory_fallback.get(search_key, [])
        else:
            # 메모리 폴백
            return self._memory_fallback.get(search_key, [])
    
    def save_crawled_data(self, search_key: str, places_data: List[Dict[str, Any]]):
        """크롤링 데이터를 Redis에 저장 (30일 TTL)"""
        cache_key = f"crawl:{search_key}"
        
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
                'naver_info': place.get('naver_info', {}),
                'google_info': place.get('google_info', {}),
                'blog_reviews': place.get('blog_reviews', [])
            }
            cached_places.append(cached_place)
        
        if self.redis_available:
            try:
                # JSON 직렬화 후 Redis에 저장
                self.redis_client.setex(
                    cache_key,
                    self.ttl_seconds,
                    json.dumps(cached_places, ensure_ascii=False)
                )
                print(f"💾 Redis 캐시 저장: {search_key} ({len(cached_places)}개 장소, TTL: 30일)")
            except Exception as e:
                print(f"   ⚠️ Redis 저장 오류: {e}, 메모리에만 저장")
                self._memory_fallback[search_key] = cached_places
        else:
            # 메모리 폴백
            self._memory_fallback[search_key] = cached_places
            print(f"💾 메모리 캐시 저장: {search_key} ({len(cached_places)}개 장소)")
    
    def cleanup_expired_cache(self) -> int:
        """만료된 캐시 정리 (Redis는 자동 만료되므로 메모리 폴백만)"""
        if not self.redis_available:
            expired_count = len(self._memory_fallback)
            self._memory_fallback.clear()
            return expired_count
        return 0
    
    def generate_search_key(self, city: str, keyword: str) -> str:
        """검색 키 생성"""
        return f"{city}_{keyword}".lower().replace(' ', '_')
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        if self.redis_available:
            try:
                info = self.redis_client.info('stats')
                keys_count = self.redis_client.dbsize()
                
                return {
                    'backend': 'redis',
                    'total_keys': keys_count,
                    'total_commands': info.get('total_commands_processed', 0),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0),
                    'hit_rate': self._calculate_hit_rate(info)
                }
            except Exception as e:
                return {'backend': 'redis', 'error': str(e)}
        else:
            return {
                'backend': 'memory_fallback',
                'total_keys': len(self._memory_fallback)
            }
    
    def _calculate_hit_rate(self, info: Dict) -> float:
        """캐시 히트율 계산"""
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return round(hits / total * 100, 2)
    
    def clear_all_cache(self):
        """모든 캐시 삭제 (개발/디버깅용)"""
        if self.redis_available:
            try:
                # crawl: 접두사를 가진 키만 삭제
                keys = self.redis_client.keys('crawl:*')
                if keys:
                    self.redis_client.delete(*keys)
                    print(f"🗑️ Redis 캐시 삭제: {len(keys)}개 키")
                return len(keys)
            except Exception as e:
                print(f"⚠️ Redis 삭제 오류: {e}")
                return 0
        else:
            count = len(self._memory_fallback)
            self._memory_fallback.clear()
            return count

