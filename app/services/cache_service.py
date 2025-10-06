"""
Redis 캐시 서비스
"""

import os
import json
import redis
from typing import Any, Optional

class CacheService:
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # 연결 테스트
            self.redis_client.ping()
            self.enabled = True
        except:
            print("Redis 연결 실패, 캐시 비활성화")
            self.enabled = False
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 데이터 조회"""
        if not self.enabled:
            return None
        
        try:
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except:
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """캐시에 데이터 저장"""
        if not self.enabled:
            return
        
        try:
            self.redis_client.setex(key, ttl, json.dumps(value))
        except:
            pass
    
    def delete(self, key: str):
        """캐시에서 데이터 삭제"""
        if not self.enabled:
            return
        
        try:
            self.redis_client.delete(key)
        except:
            pass