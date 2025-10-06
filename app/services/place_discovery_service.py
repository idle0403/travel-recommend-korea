"""
장소 발견 서비스

프롬프트 분석 후 네이버 검색을 통해 실제 장소 데이터를 먼저 수집
"""

import re
from typing import Dict, Any, List
from app.services.naver_service import NaverService
from app.services.google_maps_service import GoogleMapsService
from app.services.blog_crawler_service import BlogCrawlerService

class PlaceDiscoveryService:
    def __init__(self):
        self.naver_service = NaverService()
        self.google_service = GoogleMapsService()
        self.blog_crawler = BlogCrawlerService()
    
    async def discover_places_from_prompt(self, prompt: str, city: str = "Seoul") -> Dict[str, Any]:
        """프롬프트에서 키워드 추출 후 실제 장소 데이터 수집"""
        
        # 1. 프롬프트 분석 및 키워드 추출
        keywords = self._extract_keywords_from_prompt(prompt)
        
        # 2. 각 키워드별로 네이버 검색 실행
        discovered_places = []
        for keyword in keywords:
            search_query = f"{city} {keyword}"
            places = await self._search_places_by_keyword(search_query)
            discovered_places.extend(places)
        
        # 3. 중복 제거 및 품질 필터링
        filtered_places = self._filter_and_deduplicate(discovered_places)
        
        return {
            "extracted_keywords": keywords,
            "total_found": len(discovered_places),
            "filtered_places": filtered_places,
            "search_queries": [f"{city} {kw}" for kw in keywords]
        }
    
    def _extract_keywords_from_prompt(self, prompt: str) -> List[str]:
        """프롬프트에서 여행 관련 키워드 추출"""
        keywords = []
        
        # 음식 관련 키워드
        food_patterns = [
            r'맛집', r'음식', r'식당', r'카페', r'디저트', r'한식', r'양식', r'중식', r'일식',
            r'치킨', r'피자', r'햄버거', r'파스타', r'스테이크', r'초밥', r'라멘', r'떡볶이',
            r'커피', r'베이커리', r'브런치', r'술집', r'바', r'펜션'
        ]
        
        # 관광지 키워드
        attraction_patterns = [
            r'관광지', r'명소', r'궁궐', r'박물관', r'미술관', r'공원', r'타워', r'전망대',
            r'쇼핑', r'시장', r'몰', r'거리', r'마을', r'섬', r'해변', r'산', r'강', r'호수'
        ]
        
        # 활동 키워드
        activity_patterns = [
            r'체험', r'놀이공원', r'테마파크', r'스파', r'온천', r'찜질방', r'영화관',
            r'노래방', r'볼링', r'당구', r'게임', r'VR', r'이스케이프룸'
        ]
        
        all_patterns = food_patterns + attraction_patterns + activity_patterns
        
        for pattern in all_patterns:
            if re.search(pattern, prompt):
                keywords.append(pattern.replace('r\'', '').replace('\'', ''))
        
        # 기본 키워드 (키워드가 없을 경우)
        if not keywords:
            if '데이트' in prompt:
                keywords = ['카페', '맛집', '공원']
            elif '가족' in prompt:
                keywords = ['놀이공원', '박물관', '맛집']
            else:
                keywords = ['관광지', '맛집']
        
        return keywords[:5]  # 최대 5개
    
    async def _search_places_by_keyword(self, search_query: str) -> List[Dict[str, Any]]:
        """키워드로 네이버 장소 검색"""
        try:
            # 네이버 지역 검색
            naver_places = await self.naver_service.search_places(search_query, display=10)
            
            # 네이버 블로그 검색 (후기 확인용)
            blog_reviews = await self.naver_service.search_blogs(f"{search_query} 후기", display=5)
            
            enhanced_places = []
            for place in naver_places:
                # 구글 상세 정보 추가
                google_details = await self.google_service.get_place_details(
                    place.get('name', ''), 
                    place.get('address', '')
                )
                
                # 블로그 내용 크롤링
                blog_contents = []
                if blog_reviews:
                    blog_urls = [blog.get('link') for blog in blog_reviews[:2]]
                    blog_contents = await self.blog_crawler.get_multiple_blog_contents(blog_urls)
                
                enhanced_place = {
                    **place,
                    'google_info': google_details,
                    'blog_reviews': blog_reviews[:3],
                    'blog_contents': blog_contents,
                    'search_keyword': search_query,
                    'verified': bool(place.get('name') and google_details.get('name'))
                }
                enhanced_places.append(enhanced_place)
            
            return enhanced_places
            
        except Exception as e:
            print(f"장소 검색 오류 ({search_query}): {str(e)}")
            return []
    
    def _filter_and_deduplicate(self, places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """중복 제거 및 품질 필터링"""
        seen_names = set()
        seen_addresses = set()
        filtered = []
        
        for place in places:
            name = place.get('name', '').lower()
            address = place.get('address', '').lower()
            
            # 중복 체크
            if name in seen_names or address in seen_addresses:
                continue
            
            # 품질 체크 (네이버 + 구글 둘 다 있어야 함)
            if place.get('verified') and place.get('name'):
                filtered.append(place)
                seen_names.add(name)
                seen_addresses.add(address)
        
        # 평점 순으로 정렬
        filtered.sort(key=lambda x: x.get('google_info', {}).get('rating', 0), reverse=True)
        
        return filtered[:20]  # 최대 20개