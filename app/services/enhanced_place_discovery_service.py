"""
향상된 장소 발견 서비스 - 8단계 아키텍처 구현 + 지역 정밀도 향상
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

# 🆕 새로운 지역 정밀도 컴포넌트
from app.services.hierarchical_location_extractor import HierarchicalLocationExtractor
from app.services.context_aware_search_query_builder import ContextAwareSearchQueryBuilder
from app.services.geographic_filter import GeographicFilter
from app.services.local_context_db import LocalContextDB

class EnhancedPlaceDiscoveryService:
    def __init__(self):
        self.naver_service = NaverService()
        self.google_service = GoogleMapsService()
        self.blog_crawler = BlogCrawlerService()
        self.weather_service = WeatherService()
        self.cache_service = CrawlCacheService()
        self.city_service = CityService()
        self.district_service = DistrictService()
        
        # 🆕 새로운 컴포넌트 추가
        self.location_extractor = HierarchicalLocationExtractor()
        self.query_builder = ContextAwareSearchQueryBuilder()
        self.geo_filter = GeographicFilter()
        self.local_context_db = LocalContextDB()  # 🆕 지역 맥락 DB
    
    async def discover_places_with_weather(self, prompt: str, city: str, travel_dates: List[str]) -> Dict[str, Any]:
        """
        8단계 아키텍처 구현 + 지역 정밀도 향상
        
        🆕 개선사항:
        - 계층적 지역 추출 (시 > 구 > 동 > POI)
        - 컨텍스트 인지 검색 쿼리 생성
        - 지리적 필터링 (좌표 기반)
        """
        
        print(f"\n{'='*80}")
        print(f"🚀 향상된 장소 발견 시작")
        print(f"{'='*80}")
        
        # 🆕 Step 0: 계층적 지역 정보 추출
        print(f"\n📍 [Step 0] 계층적 지역 정보 추출")
        location_hierarchy = self.location_extractor.extract_location_hierarchy(prompt)
        
        # 🆕 Step 0.5: 지역 맥락 정보 조회
        print(f"\n🏙️ [Step 0.5] 지역 맥락 DB 조회")
        local_context = {}
        if location_hierarchy.get('neighborhood'):
            local_context = self.local_context_db.enrich_search_with_context(
                location=location_hierarchy['neighborhood'],
                user_request=prompt,
                time_context=location_hierarchy.get('context', {}).get('시간대', []),
                target_context=location_hierarchy.get('context', {}).get('타겟', [])
            )
            
            if local_context.get('enriched'):
                print(f"   ✅ 지역 특성 매칭: {location_hierarchy['neighborhood']}")
                print(f"   특성: {', '.join(local_context.get('location_characteristics', [])[:3])}")
                print(f"   추천 음식: {', '.join(local_context.get('recommended_cuisines', [])[:3])}")
                print(f"   가격대: {local_context.get('target_price_range')}")
                print(f"   분위기: {local_context.get('atmosphere')}")
            else:
                print(f"   ℹ️ {location_hierarchy['neighborhood']} 맥락 정보 없음 (일반 검색)")
        
        # 1. 프롬프트 분석 및 키워드 추출
        print(f"\n🔑 [Step 1] 키워드 추출")
        keywords = self._extract_keywords_from_prompt(prompt)
        
        # 🆕 지역 맥락 기반 키워드 확장
        if local_context.get('enriched'):
            # 추천 음식 종류를 키워드에 추가
            if '맛집' in keywords or '음식' in keywords:
                context_cuisines = local_context.get('recommended_cuisines', [])[:2]
                for cuisine in context_cuisines:
                    if cuisine not in keywords:
                        keywords.append(cuisine)
                        print(f"   🆕 맥락 기반 키워드 추가: {cuisine}")
        
        print(f"   최종 키워드: {keywords}")
        
        # 🆕 Step 1.5: 컨텍스트 인지 검색 쿼리 생성
        print(f"\n🔍 [Step 1.5] 검색 쿼리 생성")
        search_queries = self.query_builder.build_search_queries(location_hierarchy, keywords)
        primary_queries = self.query_builder.get_primary_queries(search_queries, top_n=5)
        
        # 2. 날씨 정보 조회 (지정된 일자)
        print(f"\n🌦️ [Step 2] 날씨 정보 조회")
        weather_data = await self._get_weather_for_dates(city, travel_dates)
        
        # 3. 캐시 확인 후 크롤링 (중복 방지) - 🆕 정밀 검색 쿼리 사용
        print(f"\n💾 [Step 3] 장소 데이터 수집 (캐시 + 크롤링)")
        all_places = []
        
        # 기존 키워드 기반 검색
        for keyword in keywords:
            search_key = self.cache_service.generate_search_key(city, keyword)
            
            cached_places = self.cache_service.get_cached_data(search_key)
            if cached_places:
                print(f"   ✅ 캐시 사용: {search_key} ({len(cached_places)}개)")
                all_places.extend(cached_places)
            else:
                print(f"   🔍 새 크롤링: {search_key}")
                new_places = await self._crawl_places_by_keyword(city, keyword)
                if new_places:
                    self.cache_service.save_crawled_data(search_key, new_places)
                    all_places.extend(new_places)
        
        # 🆕 정밀 검색 쿼리 기반 추가 검색
        for query_info in search_queries[:3]:  # 상위 3개만
            query = query_info['query']
            search_key = self.cache_service.generate_search_key("", query)
            
            cached_places = self.cache_service.get_cached_data(search_key)
            if cached_places:
                print(f"   ✅ 캐시 사용 (정밀): {query} ({len(cached_places)}개)")
                all_places.extend(cached_places)
            else:
                print(f"   🔍 새 크롤링 (정밀): {query}")
                new_places = await self._crawl_places_by_precise_query(query)
                if new_places:
                    self.cache_service.save_crawled_data(search_key, new_places)
                    all_places.extend(new_places)
        
        print(f"   📊 총 수집된 장소: {len(all_places)}개")
        
        # 🆕 Step 3.5: 지리적 필터링 (좌표 기반)
        print(f"\n🗺️ [Step 3.5] 지리적 필터링")
        geo_filtered_places = self.geo_filter.filter_by_distance(
            places=all_places,
            center_lat=location_hierarchy['lat'],
            center_lng=location_hierarchy['lng'],
            radius_km=location_hierarchy['search_radius_km'],
            location_text=location_hierarchy['location_text']
        )
        
        # 🆕 주소 기반 보조 필터링
        if location_hierarchy.get('district'):
            geo_filtered_places = self.geo_filter.filter_by_address(
                places=geo_filtered_places,
                required_district=location_hierarchy.get('district'),
                required_neighborhood=location_hierarchy.get('neighborhood')
            )
        
        # 🆕 거리 + 평점 기반 재정렬
        geo_filtered_places = self.geo_filter.rerank_by_distance_and_rating(
            places=geo_filtered_places,
            distance_weight=0.4,
            rating_weight=0.6
        )
        
        print(f"   ✅ 지리적 필터링 완료: {len(geo_filtered_places)}개")
        
        # 4. AI 분석 및 추천 (날씨 고려)
        print(f"\n🤖 [Step 4] AI 분석 및 추천")
        ai_recommendations = await self._ai_analyze_with_weather(geo_filtered_places, weather_data, prompt)
        
        # 5. 장소 검증 (할루시네이션 제거)
        print(f"\n✅ [Step 5] 장소 검증")
        verified_places = await self._verify_recommended_places(ai_recommendations)
        
        # 6. 최적 동선 계산
        print(f"\n🛣️ [Step 6] 최적 동선 계산")
        optimized_route = await self._calculate_optimal_route(verified_places, city)
        
        # 7. 장기 여행시 구역별 세분화
        if len(travel_dates) > 1:
            print(f"\n📅 [Step 7] 구역별 세분화 (다일 여행)")
            district_recommendations = await self._get_district_recommendations(city, len(travel_dates))
            optimized_route = self._merge_with_districts(optimized_route, district_recommendations)
        
        print(f"\n{'='*80}")
        print(f"✨ 장소 발견 완료!")
        print(f"{'='*80}\n")
        
        return {
            "extracted_keywords": keywords,
            "location_hierarchy": location_hierarchy,  # 🆕 추가
            "local_context": local_context,  # 🆕 지역 맥락 정보
            "search_queries": search_queries,  # 🆕 추가
            "weather_forecast": weather_data,
            "total_places_found": len(all_places),
            "geo_filtered_count": len(geo_filtered_places),  # 🆕 추가
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
        
        enhanced_places = []
        for place in naver_places:
            place_name = place.get('name', '')
            
            # 구글 정보 추가
            google_details = await self.google_service.get_place_details(
                place_name, place.get('address', '')
            )
            
            # ✅ 각 장소별로 개별 블로그 검색
            blog_reviews = await self.naver_service.search_blogs(f"{place_name} 후기", display=5)
            print(f"📝 {place_name}: 블로그 후기 {len(blog_reviews)}개 수집")
            
            # 블로그 크롤링
            blog_contents = []
            if blog_reviews:
                blog_urls = [blog.get('link') for blog in blog_reviews[:3]]
                blog_contents = await self.blog_crawler.get_multiple_blog_contents(blog_urls)
            
            enhanced_place = {
                **place,
                'google_info': google_details,
                'blog_reviews': blog_reviews,  # ✅ 장소별 개별 후기
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
        """
        최적 동선 계산
        
        Returns:
            프론트엔드와 호환되는 경로 정보 (polyline, locations, bounds 포함)
        """
        if len(places) < 2:
            return {
                "places": places,
                "locations": places,  # 프론트엔드 호환성
                "total_distance": "0km",
                "total_time": "0분",
                "polyline": ""
            }
        
        # 구역별 클러스터링
        clustered = self.district_service.create_district_based_itinerary(
            city, "custom", len(places) * 2, None
        )
        
        # Google Maps로 경로 최적화
        locations = [
            {
                "lat": p.get('lat', 37.5665),
                "lng": p.get('lng', 126.9780),
                "name": p.get('name', 'Unknown')
            }
            for p in places
        ]
        route_info = await self.google_service.get_optimized_route(locations)
        
        # 프론트엔드 호환 형식으로 평탄화
        # route_info는 이미 polyline, bounds, locations를 포함하고 있음
        result = {
            "places": places,
            "locations": locations,  # 프론트엔드가 기대하는 필드
            "clustered_districts": clustered
        }
        
        # route_info의 필드들을 최상위로 복사
        if route_info:
            result.update({
                "polyline": route_info.get("polyline", ""),
                "bounds": route_info.get("bounds", {}),
                "total_distance": route_info.get("total_distance", "0km"),
                "total_duration": route_info.get("total_duration", "0분"),
                "route_segments": route_info.get("route_segments", []),
                "optimized_order": route_info.get("optimized_order", []),
                "waypoint_order": route_info.get("waypoint_order", [])
            })
        
        return result
    
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
    
    async def _crawl_places_by_precise_query(self, query: str) -> List[Dict[str, Any]]:
        """
        🆕 정밀 검색 쿼리로 장소 크롤링
        
        Args:
            query: 정밀 검색 쿼리 (예: "서울 강서구 마곡동 맛집")
        
        Returns:
            장소 리스트
        """
        # 네이버 검색
        naver_places = await self.naver_service.search_places(query, display=10)
        
        enhanced_places = []
        for place in naver_places:
            place_name = place.get('name', '')
            
            # 구글 정보 추가
            google_details = await self.google_service.get_place_details(
                place_name, place.get('address', '')
            )
            
            # 블로그 검색 (개별)
            blog_reviews = await self.naver_service.search_blogs(f"{place_name} 후기", display=3)
            
            # 블로그 크롤링
            blog_contents = []
            if blog_reviews:
                blog_urls = [blog.get('link') for blog in blog_reviews[:2]]
                blog_contents = await self.blog_crawler.get_multiple_blog_contents(blog_urls)
            
            enhanced_place = {
                **place,
                'google_info': google_details,
                'blog_reviews': blog_reviews,
                'blog_contents': blog_contents,
                'verified': bool(place.get('name') and google_details.get('name')),
                'crawl_timestamp': datetime.now().isoformat()
            }
            enhanced_places.append(enhanced_place)
        
        return enhanced_places