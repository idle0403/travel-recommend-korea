"""
장소 검증 서비스

네이버 검색을 통한 실제 장소 존재 여부 검증 및 DB 저장
"""

import asyncio
from typing import Dict, Any, List, Optional
from app.services.naver_service import NaverService
from app.services.google_maps_service import GoogleMapsService

class PlaceVerificationService:
    def __init__(self):
        self.naver_service = NaverService()
        self.google_service = GoogleMapsService()
        # 검증된 장소 캐시 (실제로는 DB 사용)
        self.verified_places_cache = {}
        self.invalid_places_cache = set()
    
    async def verify_place_exists(self, place_name: str, location: str = "Seoul") -> Dict[str, Any]:
        """네이버 검색을 통한 장소 존재 여부 검증"""
        
        # 캐시 확인
        cache_key = f"{place_name}_{location}"
        if cache_key in self.verified_places_cache:
            return self.verified_places_cache[cache_key]
        
        if cache_key in self.invalid_places_cache:
            return {"exists": False, "reason": "previously_invalid"}
        
        # 네이버 지역 검색
        naver_places = await self.naver_service.search_places(place_name)
        
        # 구글 Places 검색
        google_details = await self.google_service.get_place_details(place_name, location)
        
        # 검증 기준
        verification_data = {
            "place_name": place_name,
            "exists": False,
            "naver_found": bool(naver_places),
            "google_found": bool(google_details and google_details.get('name')),
            "verification_score": 0
        }
        
        # 점수 계산
        score = 0
        if naver_places:
            score += 50  # 네이버에서 발견
            verification_data["naver_info"] = naver_places[0]
        
        if google_details and google_details.get('name'):
            score += 50  # 구글에서 발견
            verification_data["google_info"] = google_details
        
        # 추가 검증: 블로그 후기 존재
        naver_blogs = await self.naver_service.search_blogs(f"{place_name} 후기")
        if naver_blogs and len(naver_blogs) >= 2:
            score += 20  # 블로그 후기 존재
            verification_data["blog_reviews"] = naver_blogs
        
        verification_data["verification_score"] = score
        
        # 존재 판정 (70점 이상)
        if score >= 70:
            verification_data["exists"] = True
            self.verified_places_cache[cache_key] = verification_data
            print(f"✅ 장소 검증 성공: {place_name} (점수: {score})")
        else:
            self.invalid_places_cache.add(cache_key)
            print(f"❌ 장소 검증 실패: {place_name} (점수: {score})")
        
        return verification_data