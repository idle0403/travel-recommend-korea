"""
AWS Lambda 핸들러
FastAPI 앱을 Mangum을 통해 Lambda에서 실행
외부 Redis 연결 지원 (Lambda 내부에서 Redis 시작하지 않음)
"""

import os
import threading
import redis

# Redis 연결 상태 (모듈 레벨 변수)
_redis_started = False
_redis_lock = threading.Lock()

def check_external_redis():
    """외부 Redis 연결 확인"""
    global _redis_started
    
    with _redis_lock:
        if _redis_started:
            return
        
        # 환경 변수에서 Redis 호스트 가져오기
        redis_host = os.environ.get('REDIS_HOST', 'localhost')
        redis_port = int(os.environ.get('REDIS_PORT', 6379))
        
        print(f"🔍 외부 Redis 연결 시도: {redis_host}:{redis_port}")
        
        try:
            r = redis.Redis(host=redis_host, port=redis_port, socket_connect_timeout=2)
            r.ping()
            print(f"✅ Redis 연결 성공: {redis_host}:{redis_port}")
            _redis_started = True
            return
        except Exception as e:
            print(f"⚠️  Redis 연결 실패: {e}")
            print(f"   서비스들이 Redis 없이 메모리 캐시로 동작합니다.")

# Lambda 초기화 시 외부 Redis 연결 확인
check_external_redis()

# FastAPI 앱 로드
from mangum import Mangum  # type: ignore
from app.main import app

# Lambda 핸들러
handler = Mangum(app, lifespan="off")
