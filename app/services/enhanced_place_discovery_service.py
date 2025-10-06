"""
향상된 장소 발견 서비스 - 8단계 아키텍처 구현
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.services.naver_service import NaverService
from app.services.google_maps_service import GoogleMapsService
from app.services.blog_crawler_service import BlogCrawlerService
from app.services.weather_service import WeatherService
from app.services.crawl_cache_service import CrawlCacheService
from app.services.city_service import CityService
from app.services.district_service import DistrictService

class EnhancedPlaceDiscoveryService:
    def __init__(self):
        self.naver_service = NaverService()
        self.google_service = GoogleMapsService()
        self.blog_crawler = BlogCrawlerService()
        self.weather_service = WeatherService()
        self.cache_service = CrawlCacheService()
        self.city_service = CityService()
        self.district_service = DistrictService()
    
    async def discover_places_with_weather(self, prompt: str, city: str, travel_dates: List[str]) -> Dict[str, Any]:
        """8단계 아키텍처 구현"""
        
        # 1. 프롬프트 분석 및 키워드 추출
        keywords = self._extract_keywords_from_prompt(prompt)
        
        # 2. 날씨 정보 조회 (지정된 일자)
        weather_data = await self._get_weather_for_dates(city, travel_dates)
        
        # 3. 캐시 확인 후 크롤링 (중복 방지)
        all_places = []
        for keyword in keywords:
            search_key = self.cache_service.generate_search_key(city, keyword)
            
            # 캐시된 데이터 확인
            cached_places = self.cache_service.get_cached_data(search_key)
            if cached_places:
                print(f"✅ 캐시 사용: {search_key} ({len(cached_places)}개)")
                all_places.extend(cached_places)
            else:
                # 새로 크롤링
                print(f"🔍 새 크롤링: {search_key}")
                new_places = await self._crawl_places_by_keyword(city, keyword)
                if new_places:
                    self.cache_service.save_crawled_data(search_key, new_places)
                    all_places.extend(new_places)
        
        # 4. AI 분석 및 추천 (날씨 고려)
        ai_recommendations = await self._ai_analyze_with_weather(all_places, weather_data, prompt)
        
        # 5. 장소 검증 (할루시네이션 제거)
        verified_places = await self._verify_recommended_places(ai_recommendations)
        
        # 6. 최적 동선 계산
        optimized_route = await self._calculate_optimal_route(verified_places, city)
        
        # 7. 장기 여행시 구역별 세분화
        if len(travel_dates) > 1:
            district_recommendations = await self._get_district_recommendations(city, len(travel_dates))
            optimized_route = self._merge_with_districts(optimized_route, district_recommendations)
        
        return {
            "extracted_keywords": keywords,
            "weather_forecast": weather_data,
            "total_places_found": len(all_places),
            "ai_recommendations": ai_recommendations,
            "verified_places": verified_places,
            "optimized_route": optimized_route,
            "travel_dates": travel_dates,
            "cache_usage": self._get_cache_stats(keywords, city)
        }
    
    async def _get_weather_for_dates(self, city: str, dates: List[str]) -> Dict[str, Any]:
        """지정된 일자들의 날씨 정보"""
        weather_code = self.city_service.get_weather_code(city)
        weather_data = {}
        
        for date in dates:
            # 현재는 현재 날씨만 지원, 실제로는 날짜별 예보 필요
            daily_weather = await self.weather_service.get_current_weather(weather_code)
            weather_data[date] = daily_weather
        
        return weather_data
    
    async def _crawl_places_by_keyword(self, city: str, keyword: str) -> List[Dict[str, Any]]:
        """키워드별 장소 크롤링"""
        search_query = f"{city} {keyword}"
        
        # 네이버 검색
        naver_places = await self.naver_service.search_places(search_query, display=15)
        blog_reviews = await self.naver_service.search_blogs(f"{search_query} 후기", display=10)
        
        enhanced_places = []
        for place in naver_places:
            # 구글 정보 추가
            google_details = await self.google_service.get_place_details(
                place.get('name', ''), place.get('address', '')
            )
            
            # 블로그 크롤링
            blog_contents = []
            if blog_reviews:
                blog_urls = [blog.get('link') for blog in blog_reviews[:3]]
                blog_contents = await self.blog_crawler.get_multiple_blog_contents(blog_urls)
            
            enhanced_place = {
                **place,
                'google_info': google_details,
                'blog_reviews': blog_reviews[:5],
                'blog_contents': blog_contents,
                'verified': bool(place.get('name') and google_details.get('name')),
                'crawl_timestamp': datetime.now().isoformat()
            }
            enhanced_places.append(enhanced_place)
        
        return enhanced_places
    
    async def _ai_analyze_with_weather(self, places: List[Dict], weather_data: Dict, prompt: str) -> List[Dict]:
        """AI가 날씨를 고려하여 장소 분석 및 추천"""
        # 날씨 기반 필터링
        weather_filtered = []
        
        for date, weather in weather_data.items():
            if weather.get('is_rainy'):
                # 비오는 날: 실내 장소 우선
                indoor_places = [p for p in places if self._is_indoor_place(p)]
                weather_filtered.extend(indoor_places)
            else:
                # 맑은 날: 모든 장소 가능
                weather_filtered.extend(places)
        
        # 중복 제거 및 평점순 정렬
        unique_places = self._deduplicate_places(weather_filtered)
        return sorted(unique_places, key=lambda x: x.get('google_info', {}).get('rating', 0), reverse=True)[:20]
    
    async def _verify_recommended_places(self, recommendations: List[Dict]) -> List[Dict]:
        """추천된 장소들의 실제 존재 여부 검증"""
        verified = []
        for place in recommendations:
            # 네이버 + 구글 둘 다 확인되면 검증됨
            has_naver = bool(place.get('name'))
            has_google = bool(place.get('google_info', {}).get('name'))
            
            if has_naver and has_google:
                place['verification_status'] = 'verified'
                verified.append(place)
            elif has_naver or has_google:
                place['verification_status'] = 'partial'
                verified.append(place)
        
        return verified
    
    async def _calculate_optimal_route(self, places: List[Dict], city: str) -> Dict[str, Any]:
        """최적 동선 계산"""
        if len(places) < 2:
            return {"places": places, "total_distance": "0km", "total_time": "0분"}
        
        # 구역별 클러스터링
        clustered = self.district_service.create_district_based_itinerary(
            city, "custom", len(places) * 2, None
        )
        
        # Google Maps로 경로 최적화
        locations = [{"lat": p.get('lat', 37.5665), "lng": p.get('lng', 126.9780), "name": p.get('name')} for p in places]
        route_info = await self.google_service.get_optimized_route(locations)
        
        return {
            "places": places,
            "route_info": route_info,
            "clustered_districts": clustered
        }
    
    async def _get_district_recommendations(self, city: str, days_count: int) -> Dict[str, List]:
        """장기 여행시 구역별 세분화 추천"""
        districts = self.district_service.get_districts_by_city(city)
        recommendations = {}
        
        for district_name, district_info in districts.items():
            # 각 구역별로 관광지/맛집/호텔 크롤링
            attractions = await self._crawl_places_by_keyword(city, f"{district_name} 관광지")
            restaurants = await self._crawl_places_by_keyword(city, f"{district_name} 맛집")
            
            if days_count > 2:  # 2박 이상시 호텔 정보도 추가
                hotels = await self._crawl_places_by_keyword(city, f"{district_name} 호텔")
                recommendations[district_name] = {
                    "attractions": attractions[:5],
                    "restaurants": restaurants[:5], 
                    "hotels": hotels[:3]
                }
            else:
                recommendations[district_name] = {
                    "attractions": attractions[:3],
                    "restaurants": restaurants[:3]
                }
        
        return recommendations
    
    def _merge_with_districts(self, route: Dict, districts: Dict) -> Dict:
        """기본 경로와 구역별 추천 병합"""
        route['district_recommendations'] = districts
        return route
    
    def _is_indoor_place(self, place: Dict) -> bool:
        """실내 장소 여부 판단"""
        indoor_keywords = ['카페', '박물관', '미술관', '쇼핑몰', '영화관', '실내', '지하']
        place_info = f"{place.get('name', '')} {place.get('category', '')}"
        return any(keyword in place_info for keyword in indoor_keywords)
    
    def _deduplicate_places(self, places: List[Dict]) -> List[Dict]:
        """중복 장소 제거"""
        seen = set()
        unique = []
        for place in places:
            key = f"{place.get('name', '')}_{place.get('address', '')}"
            if key not in seen:
                seen.add(key)
                unique.append(place)
        return unique
    
    def _extract_keywords_from_prompt(self, prompt: str) -> List[str]:
        """프롬프트에서 키워드 추출"""
        keywords = []
        
        # 기본 키워드 패턴
        if '맛집' in prompt or '음식' in prompt:
            keywords.append('맛집')
        if '관광' in prompt or '명소' in prompt:
            keywords.append('관광지')
        if '카페' in prompt:
            keywords.append('카페')
        if '쇼핑' in prompt:
            keywords.append('쇼핑')
        if '호텔' in prompt or '숙박' in prompt:
            keywords.append('호텔')
        
        return keywords if keywords else ['관광지', '맛집']
    
    def _get_cache_stats(self, keywords: List[str], city: str) -> Dict:
        """캐시 사용 통계"""
        stats = {"cached": 0, "new_crawl": 0}
        for keyword in keywords:
            search_key = self.cache_service.generate_search_key(city, keyword)
            cached_data = self.cache_service.get_cached_data(search_key)
            if cached_data:
                stats["cached"] += 1
            else:
                stats["new_crawl"] += 1
        return stats