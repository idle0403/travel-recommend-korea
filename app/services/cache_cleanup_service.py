"""
캐시 정리 서비스 - 8단계 아키텍처 지원
"""

import schedule
import time
from datetime import datetime
from app.services.crawl_cache_service import CrawlCacheService

class CacheCleanupService:
    def __init__(self):
        self.cache_service = CrawlCacheService()
        self.setup_scheduler()
    
    def setup_scheduler(self):
        """매일 자정에 만료된 캐시 정리"""
        schedule.every().day.at("00:00").do(self.cleanup_expired_cache)
    
    def cleanup_expired_cache(self):
        """만료된 캐시 데이터 정리"""
        try:
            expired_count = self.cache_service.cleanup_expired_cache()
            print(f"🧹 캐시 정리 완료: {expired_count}개 만료 데이터 삭제")
        except Exception as e:
            print(f"❌ 캐시 정리 오류: {str(e)}")
    
    def run_scheduler(self):
        """스케줄러 실행"""
        while True:
            schedule.run_pending()
            time.sleep(3600)  # 1시간마다 체크