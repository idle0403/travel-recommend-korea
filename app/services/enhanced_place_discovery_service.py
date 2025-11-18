"""
향상된 장소 발견 서비스 - 8단계 아키텍처 구현 + 지역 정밀도 향상
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.services.google_maps_service import GoogleMapsService
from app.services.blog_crawler_service import BlogCrawlerService
from app.services.weather_service import WeatherService
from app.services.crawl_cache_service import CrawlCacheService
# 🆕 Redis 캐시 우선 사용, 없으면 메모리 캐시 폴백
try:
    from app.services.redis_cache_service import RedisCacheService
    USE_REDIS = True
except ImportError:
    USE_REDIS = False
from app.services.city_service import CityService
from app.services.district_service import DistrictService

# 🆕 새로운 지역 정밀도 컴포넌트
from app.services.hierarchical_location_extractor import HierarchicalLocationExtractor
from app.services.context_aware_search_query_builder import ContextAwareSearchQueryBuilder
from app.services.geographic_filter import GeographicFilter
from app.services.local_context_db import LocalContextDB

class EnhancedPlaceDiscoveryService:
    def __init__(self):
        self.google_service = GoogleMapsService()  # 장소 검색 + 경로
        self.blog_crawler = BlogCrawlerService()
        self.weather_service = WeatherService()
        
        # 🆕 Redis 우선 사용, 없으면 메모리 캐시
        if USE_REDIS:
            self.cache_service = RedisCacheService()
            print("🎯 Redis 캐시 서비스 사용")
        else:
            self.cache_service = CrawlCacheService()
            print("📦 메모리 캐시 서비스 사용 (폴백)")
        
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
        
        # 🆕 Step 0: 계층적 지역 정보 추출 (비동기)
        print(f"\n📍 [Step 0] 계층적 지역 정보 추출")
        location_hierarchy = await self.location_extractor.extract_location_hierarchy(prompt)
        
        # 🆕 Step 0.1: city 파라미터 오버라이드 (Auto인 경우)
        if city == "Auto" or not city:
            extracted_city = location_hierarchy.get('city')
            if extracted_city:
                print(f"   🔄 city 파라미터 오버라이드: '{city}' → '{extracted_city}'")
                city = extracted_city
                # location_hierarchy는 이미 올바른 좌표를 가지고 있음 (AI 학습 완료)
        
        # 🆕 Step 0.5: 지역 맥락 정보 조회 (정적 DB + 동적 생성)
        print(f"\n🏙️ [Step 0.5] 지역 맥락 DB 조회 또는 생성")
        local_context = {}
        
        # 우선순위: neighborhood > district > city
        target_location = location_hierarchy.get('neighborhood') or \
                         location_hierarchy.get('district') or \
                         location_hierarchy.get('city')
        
        if target_location:
            print(f"   🔍 타겟 지역: {target_location}")
            
            # 동적 컨텍스트 조회/생성 (비동기)
            location_context = await self.local_context_db.get_or_create_context(target_location)
            
            if location_context:
                # enrich_search_with_context 호출
                local_context = self.local_context_db.enrich_search_with_context(
                    location=target_location,
                    user_request=prompt,
                    time_context=location_hierarchy.get('context', {}).get('시간대', []),
                    target_context=location_hierarchy.get('context', {}).get('타겟', [])
                )
                
                if local_context.get('enriched'):
                    print(f"   ✅ 지역 특성 매칭: {target_location}")
                    print(f"   특성: {', '.join(local_context.get('location_characteristics', [])[:3])}")
                    print(f"   추천 음식: {', '.join(local_context.get('recommended_cuisines', [])[:3])}")
                    print(f"   가격대: {local_context.get('target_price_range')}")
                    print(f"   분위기: {local_context.get('atmosphere')}")
                else:
                    print(f"   ℹ️ {target_location} 맥락 정보 사용 불가 (일반 검색)")
            else:
                print(f"   ⚠️ {target_location} 맥락 생성 실패 (일반 검색)")
        
        # 🆕 여행 일수 계산 (키워드 추출 전에 필요)
        days_count = len(travel_dates) if travel_dates else 1
        print(f"📊 여행 일수: {days_count}일")
        
        # 1. 프롬프트 분석 및 키워드 추출
        print(f"\n🔑 [Step 1] 키워드 추출")
        keywords = self._extract_keywords_from_prompt(prompt)
        
        # 🆕 여행 일수에 따른 키워드 확장
        if days_count >= 2:
            print(f"   🏨 1박 이상 여행 감지 → 키워드 자동 확장")
            
            # 숙박 관련
            if not any(k in keywords for k in ["호텔", "숙박", "게스트하우스"]):
                keywords.extend(["호텔", "게스트하우스"])
                print(f"   ✅ 숙박 키워드 추가: 호텔, 게스트하우스")
            
            # 관광지 관련 (맛집만 있는 경우)
            if any(k in keywords for k in ["맛집", "음식", "식당"]):
                if not any(k in keywords for k in ["관광", "명소", "체험"]):
                    keywords.extend(["관광지", "명소"])
                    print(f"   ✅ 관광 키워드 추가: 관광지, 명소")
        
        # 🆕 "실외" 키워드 감지 시 키워드 확장
        if "실외" in prompt or "야외" in prompt or "산책" in prompt:
            print(f"   🌳 실외 활동 감지 → 자연/체험 키워드 추가")
            outdoor_keywords = ["산책로", "공원", "둘레길", "체험"]
            for kw in outdoor_keywords:
                if kw not in keywords:
                    keywords.append(kw)
            print(f"   ✅ 실외 키워드 추가: {outdoor_keywords}")
        
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
        
        # 🆕 Step 1.8: 여행 일수에 따른 필요 장소 수 계산
        if days_count == 1:
            # 당일치기: 시간당 1-2개 × 8시간 = 8-16개
            required_places = 16
            places_per_keyword = 10
        elif days_count == 2:
            # 1박2일: 하루 8개 × 2일 = 16개 + 여유분 = 30개
            required_places = 30
            places_per_keyword = 15
        elif days_count >= 3:
            # 2박3일 이상: 하루 8개 × 일수 + 50% 여유
            required_places = days_count * 8 * 1.5
            places_per_keyword = 20
        else:
            required_places = 16
            places_per_keyword = 10
        
        print(f"📊 필요 장소: {required_places}개 (키워드당 {places_per_keyword}개)")
        
        # 2. 날씨 정보 조회 (지정된 일자)
        print(f"\n🌦️ [Step 2] 날씨 정보 조회")
        weather_data = await self._get_weather_for_dates(city, travel_dates)
        
        # 3. 캐시 확인 후 크롤링 (중복 방지) - 🆕 정밀 검색 쿼리 사용
        print(f"\n💾 [Step 3] 장소 데이터 수집 (캐시 + 크롤링)")
        all_places = []
        
        # 기존 키워드 기반 검색 (🆕 장기 여행은 더 많이 크롤링)
        for keyword in keywords:
            search_key = self.cache_service.generate_search_key(city, keyword)
            
            cached_places = self.cache_service.get_cached_data(search_key)
            if cached_places:
                print(f"   ✅ 캐시 사용: {search_key} ({len(cached_places)}개)")
                all_places.extend(cached_places)
            else:
                print(f"   🔍 새 크롤링: {search_key} (요청: {places_per_keyword}개)")
                new_places = await self._crawl_places_by_keyword(city, keyword, display=places_per_keyword)
                if new_places:
                    self.cache_service.save_crawled_data(search_key, new_places)
                    all_places.extend(new_places)
        
        # 🆕 정밀 검색 쿼리 기반 추가 검색 (🆕 장기 여행은 더 많이)
        query_count = 5 if days_count >= 2 else 3  # 1박2일 이상이면 쿼리 더 많이
        for query_info in search_queries[:query_count]:
            query = query_info['query']
            search_key = self.cache_service.generate_search_key("", query)
            
            cached_places = self.cache_service.get_cached_data(search_key)
            if cached_places:
                print(f"   ✅ 캐시 사용 (정밀): {query} ({len(cached_places)}개)")
                all_places.extend(cached_places)
            else:
                print(f"   🔍 새 크롤링 (정밀): {query} (요청: {places_per_keyword}개)")
                new_places = await self._crawl_places_by_precise_query(query, display=places_per_keyword)
                if new_places:
                    self.cache_service.save_crawled_data(search_key, new_places)
                    all_places.extend(new_places)
        
        print(f"   📊 총 수집된 장소: {len(all_places)}개")
        
        # 🆕 Step 3.3: 장소 부족 시 근교 지역 확대 (AI 기반)
        if days_count >= 2:  # 1박2일 이상만 근교 확대
            all_places, expanded_cities = await self.expand_to_nearby_regions(
                city=city,
                days_count=days_count,
                current_places=all_places,
                keywords=keywords
            )
            
            if expanded_cities:
                print(f"\n✅ 근교 확대 완료: {', '.join(expanded_cities)}")
                print(f"   📊 최종 수집된 장소: {len(all_places)}개")
        
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
        
        # 🆕 장소가 0개면 명확한 에러 메시지 반환 (디폴트 값 대신)
        if len(geo_filtered_places) == 0:
            requested_region = location_hierarchy.get('city', 'N/A')
            if location_hierarchy.get('district'):
                requested_region += f" {location_hierarchy.get('district')}"
            
            error_msg = f"해당 지역('{requested_region}')에서 적합한 장소를 찾을 수 없습니다. "
            error_msg += f"총 {len(all_places)}개 장소를 수집했으나 지리적 필터링 후 0개가 남았습니다. "
            
            if location_hierarchy.get('district'):
                error_msg += f"'{location_hierarchy.get('city')}' 전체로 검색을 넓혀보시거나, "
            
            error_msg += "다른 키워드를 시도해보세요."
            
            print(f"\n❌ 에러: {error_msg}")
            raise ValueError(error_msg)
        
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
            "resolved_city": city,  # 🆕 오버라이드된 도시명 (Auto → 실제 도시명)
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
    
    async def _crawl_places_by_keyword(self, city: str, keyword: str, display: int = 15) -> List[Dict[str, Any]]:
        """키워드별 장소 크롤링"""
        search_query = f"{city} {keyword}"
        
        # 네이버 검색 (🆕 display 파라미터 사용)
        naver_places = await self.naver_service.search_places(search_query, display=display)
        
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
        """프롬프트에서 키워드 추출 (🆕 확장된 키워드 패턴)"""
        keywords = []
        
        # 🆕 확장된 키워드 패턴
        keyword_patterns = {
            '맛집': ['맛집', '음식', '식당', '레스토랑', '먹거리'],
            '관광지': ['관광', '명소', '여행지', '볼거리', '투어'],
            '카페': ['카페', '커피', '디저트', '베이커리'],
            '쇼핑': ['쇼핑', '쇼핑몰', '백화점', '시장'],
            '호텔': ['호텔', '숙박', '게스트하우스', '펜션', '민박'],
            '산책로': ['산책', '산책로', '둘레길', '트레킹'],
            '공원': ['공원', '정원', '수목원', '식물원'],
            '체험': ['체험', '액티비티', '활동', '워크샵'],
            '문화': ['문화', '박물관', '미술관', '전시관', '갤러리'],
            '자연': ['자연', '산', '바다', '강', '호수', '해변'],
        }
        
        for keyword, patterns in keyword_patterns.items():
            if any(pattern in prompt for pattern in patterns):
                keywords.append(keyword)
        
        # 기본값: 다양한 키워드 포함
        if not keywords:
            keywords = ['관광지', '맛집', '카페']
        
        return keywords
    
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
    
    async def _crawl_places_by_precise_query(self, query: str, display: int = 15) -> List[Dict[str, Any]]:
        """
        🆕 정밀 검색 쿼리로 장소 크롤링
        
        Args:
            query: 정밀 검색 쿼리 (예: "서울 강서구 마곡동 맛집")
            display: 검색 결과 수 (🆕 장기 여행은 더 많이)
        
        Returns:
            장소 리스트
        """
        # 네이버 검색
        naver_places = await self.naver_service.search_places(query, display=display)
        
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
    
    def check_place_sufficiency(self, places: List[Dict], days_count: int) -> bool:
        """
        장소가 충분한지 확인
        
        Args:
            places: 현재 발견된 장소 리스트
            days_count: 여행 일수
        
        Returns:
            충분하면 True, 부족하면 False
        """
        required_min = days_count * 6  # 하루 최소 6개 (여유 있게)
        is_sufficient = len(places) >= required_min
        
        if not is_sufficient:
            print(f"\n⚠️ 장소 부족 감지:")
            print(f"   현재: {len(places)}개")
            print(f"   필요: {required_min}개 (하루 6개 × {days_count}일)")
        
        return is_sufficient
    
    async def filter_all_places_batch(
        self,
        schedule_frame: List[Dict[str, Any]],
        all_places_by_timeslot: Dict[int, List[Dict[str, Any]]],
        city: str
    ) -> Dict[int, Dict[str, Any]]:
        """
        🆕 모든 시간대의 장소를 한 번에 AI에게 보내서 최적의 조합 선택
        
        Args:
            schedule_frame: 스케줄 프레임 (시간대별 정보)
            all_places_by_timeslot: {timeslot_index: [places]} 형태
            city: 도시명
        
        Returns:
            {timeslot_index: selected_place} 형태
        """
        try:
            from openai import AsyncOpenAI
            import os
            import json
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print(f"   ℹ️ OpenAI API 키 없음 → 개별 필터링으로 폴백")
                return {}
            
            client = AsyncOpenAI(api_key=api_key)
            
            # 프롬프트 생성: 전체 스케줄과 모든 장소 목록 + 위치 정보
            prompt = f"""당신은 {city} 여행 큐레이터입니다.
아래는 여행 일정과 각 시간대에 검색된 장소 목록입니다.
**각 시간대마다 가장 적합한 장소 1개씩** 선택해주세요.

**🎯 선별 기준 (우선순위)**:
1. **동선 최적화 (최우선!)**: 
   - 이전 시간대에서 선택한 장소와 **3km 이내**인 곳 우선
   - **5km 이상**은 특별한 이유 없으면 제외
   - 거리가 가까울수록 높은 점수
   
2. **방향 일관성 (매우 중요!)**: 
   - ❌ **왔다갔다 하는 동선 금지!** 
     예) A → C(동쪽 5km) → B(서쪽 4km) ← 다시 돌아옴!
   - ✅ **한 방향으로 순차적 이동**
     예) A → B(동쪽 2km) → C(동쪽 3km) ← 계속 같은 방향!
   - 괄호 안의 방향 정보를 보고 일관된 방향 선택
   - 되돌아가는(backtracking) 동선은 최대한 회피
   - 한 방향으로 쭉 가거나, 서서히 원을 그리며 돌아오는 형태가 이상적
   
3. 시간대와 목적에 맞는 장소
4. 여행지로서 가치있는 곳 (동네 시설, 일반 공원 제외)
5. **체인점 제외** (스타벅스, 맥도날드, 이디야, 투썸플레이스 등)
6. **동네 시설 무조건 제외** (찜질방, 사우나, 목욕탕, 일반 대중탕, 동네 체육관 등)
7. 대표 랜드마크는 1일차에 반드시 포함

**🚫 절대 추천하면 안 되는 장소 (반드시 제외!)**:
- 찜질방, 사우나, 목욕탕 (예: 지오스파, 스파마린, 삼우목욕탕 등)
- 동네 시설 (동네 공원, 놀이터, 일반 체육관 등)
- 체인점 (스타벅스, 맥도날드, 버거킹, 투썸, 이디야 등)

**📍 일정 (거리 정보 포함, 방향성 고려 필수!)**:
"""
            
            # 이전 선택 장소 추적 (동선 최적화)
            prev_location = None
            
            for idx, frame_item in enumerate(schedule_frame):
                time_slot = frame_item.get('time_slot', '')
                place_type = frame_item.get('place_type', '')
                purpose = frame_item.get('purpose', '')
                day = frame_item.get('day', 1)
                
                places_for_slot = all_places_by_timeslot.get(idx, [])
                
                # 장소명과 위치 정보 포함 (상위 10개)
                place_infos = []
                for p in places_for_slot[:10]:
                    name = p.get('name', '')
                    lat = p.get('lat')
                    lng = p.get('lng')
                    
                    # 이전 장소와의 거리 및 방향 계산
                    distance_info = ""
                    if prev_location and lat and lng:
                        from math import radians, sin, cos, sqrt, atan2, degrees
                        R = 6371  # 지구 반경 (km)
                        lat1, lon1 = radians(prev_location[0]), radians(prev_location[1])
                        lat2, lon2 = radians(lat), radians(lng)
                        dlat = lat2 - lat1
                        dlon = lon2 - lon1
                        
                        # 거리 계산
                        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                        c = 2 * atan2(sqrt(a), sqrt(1-a))
                        distance = R * c
                        
                        # 방향 계산 (bearing)
                        x = sin(dlon) * cos(lat2)
                        y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
                        bearing = atan2(x, y)
                        bearing_deg = (degrees(bearing) + 360) % 360
                        
                        # 방향을 8방위로 변환
                        directions = ["북", "북동", "동", "남동", "남", "남서", "서", "북서"]
                        direction_idx = int((bearing_deg + 22.5) / 45) % 8
                        direction = directions[direction_idx]
                        
                        distance_info = f" ({distance:.1f}km {direction})"
                    
                    place_infos.append(f"{name}{distance_info}")
                
                prompt += f"\n[{idx}] {day}일차 {time_slot} - {purpose} ({self._get_place_type_korean(place_type)})\n"
                prompt += f"    후보: {', '.join(place_infos)}\n"
                
                # 첫 번째 장소를 prev_location으로 임시 설정 (AI가 참고용)
                if places_for_slot:
                    first_place = places_for_slot[0]
                    prev_location = (first_place.get('lat'), first_place.get('lng'))
            
            prompt += """
**응답 형식** (JSON만):
{
  "selections": [
    {"index": 0, "selected_place": "장소명", "reason": "선택 이유"},
    {"index": 1, "selected_place": "장소명", "reason": "선택 이유"}
  ]
}
"""
            
            print(f"\n🤖 AI 일괄 필터링 시작 (전체 {len(schedule_frame)}개 시간대)")
            
            response = await client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "당신은 여행 큐레이터입니다. 전체 일정을 보고 최적의 장소 조합을 선택합니다."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            # JSON 파싱
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
                content = content.strip()
            
            if not content:
                print(f"⚠️ AI 응답이 비어있음")
                return {}
            
            result = json.loads(content)
            selections = result.get('selections', [])
            
            print(f"✅ AI 선택 완료: {len(selections)}개")
            
            # {index: place} 매핑 생성 + 동선 검증
            selected_map = {}
            prev_selected_location = None
            total_distance = 0.0
            
            for sel in selections:
                idx = sel.get('index')
                place_name = sel.get('selected_place', '')
                reason = sel.get('reason', '')
                
                # 해당 시간대의 장소 목록에서 이름 매칭
                places_for_slot = all_places_by_timeslot.get(idx, [])
                for place in places_for_slot:
                    if place.get('name') == place_name:
                        selected_map[idx] = place
                        
                        # 동선 검증: 이전 장소와의 거리 계산
                        distance_str = ""
                        if prev_selected_location:
                            lat, lng = place.get('lat'), place.get('lng')
                            if lat and lng:
                                from math import radians, sin, cos, sqrt, atan2
                                R = 6371
                                lat1, lon1 = radians(prev_selected_location[0]), radians(prev_selected_location[1])
                                lat2, lon2 = radians(lat), radians(lng)
                                dlat, dlon = lat2 - lat1, lon2 - lon1
                                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                                c = 2 * atan2(sqrt(a), sqrt(1-a))
                                distance = R * c
                                total_distance += distance
                                distance_str = f" [이전 장소로부터 {distance:.1f}km]"
                        
                        print(f"   [{idx}] {place_name}{distance_str} - {reason}")
                        
                        # 다음 계산을 위해 현재 장소 저장
                        prev_selected_location = (place.get('lat'), place.get('lng'))
                        break
            
            if total_distance > 0:
                print(f"\n✅ 전체 이동 거리: {total_distance:.1f}km")
            
            return selected_map
            
        except Exception as e:
            print(f"⚠️ AI 일괄 필터링 실패: {e}")
            return {}
    
    async def filter_places_with_ai(
        self,
        places: List[Dict[str, Any]],
        city: str,
        place_type: str,
        max_count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        🆕 AI를 활용하여 Google Places 결과 중 좋은 장소만 선별 (Redis 캐싱)
        
        Args:
            places: Google Places 검색 결과 리스트
            city: 도시명
            place_type: 장소 유형
            max_count: 최대 선별 개수
        
        Returns:
            AI가 선별한 장소 리스트
        """
        if not places or len(places) == 0:
            return []
        
        # Step 1: 장소 이름 목록 생성
        place_names = [p.get('name', '') for p in places if p.get('name')]
        if len(place_names) == 0:
            return places[:max_count]  # AI 없이 상위 N개 반환
        
        # Step 2: AI에게 선별 요청
        try:
            from openai import AsyncOpenAI
            import os
            import json
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print(f"   ℹ️ OpenAI API 키 없음 → 상위 {max_count}개 반환")
                return places[:max_count]
            
            client = AsyncOpenAI(api_key=api_key)
            
            # place_type별 맞춤 프롬프트
            prompt = self._build_filter_prompt(city, place_type, place_names, max_count)
            
            response = await client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "당신은 여행 큐레이터입니다. 장소 목록 중에서 여행지로서 가치있는 곳만 선별합니다."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=1000  # 장소 목록이 많을 수 있으므로 넉넉하게
            )
            
            content = response.choices[0].message.content.strip()
            
            # JSON 코드 블록 제거
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
                content = content.strip()
            
            # 빈 응답 처리
            if not content:
                print(f"⚠️ AI 응답이 비어있음, 상위 {max_count}개 반환")
                return places[:max_count]
            
            result = json.loads(content)
            selected_names = result.get('selected', [])
            reason = result.get('reason', '')
            
            emoji = self._get_place_emoji(place_type)
            print(f"\n{emoji} AI 필터링 완료:")
            print(f"   입력: {len(places)}개 → 선별: {len(selected_names)}개")
            print(f"   선택: {', '.join(selected_names)}")
            print(f"   이유: {reason}")
            
            # Step 3: 선별된 장소만 반환 (순서 유지)
            filtered = []
            for place in places:
                if place.get('name') in selected_names:
                    place['is_ai_curated'] = True  # AI 선별 플래그
                    filtered.append(place)
            
            return filtered if filtered else places[:max_count]
            
        except Exception as e:
            print(f"⚠️ AI 필터링 실패: {e}, 상위 {max_count}개 반환")
            return places[:max_count]
    
    def _build_filter_prompt(self, city: str, place_type: str, place_names: List[str], max_count: int) -> str:
        """AI 필터링 프롬프트 생성"""
        
        if place_type == 'tourist_attraction':
            criteria = """
**선별 기준**:
1. 이 도시를 방문하면 **반드시 가봐야 하는** 필수 관광지
2. 관광객들이 가장 많이 찾는 명소
3. 도시를 대표하는 상징적인 장소
4. **동네 시설, 일반 공원은 제외**"""
        
        elif place_type == 'restaurant':
            criteria = """
**선별 기준**:
1. 현지인과 관광객 모두 인정하는 맛집
2. 이 도시의 특색을 느낄 수 있는 음식점
3. **체인점(맥도날드, KFC 등) 제외**
4. **일반 식당은 제외**, 유명 맛집만"""
        
        elif place_type == 'cafe':
            criteria = """
**선별 기준**:
1. 분위기 좋고 감성적인 카페
2. 관광객들이 많이 찾는 포토 스팟
3. **스타벅스 같은 체인점 제외**
4. 현지 특색 있는 카페만"""
        
        elif place_type == 'spa' or place_type == 'hot_spring_spa':
            # 🚫 스파/찜질방은 여행지답지 않으므로 빈 리스트 반환
            print(f"   🚫 {place_type} 유형은 여행지에 부적합 → 빈 리스트 반환")
            return []
        
        else:
            criteria = """
**선별 기준**:
1. 관광객들이 방문하기 좋은 곳
2. 여행지로서 가치가 있는 곳
3. 체인점, 동네 시설 제외"""
        
        return f"""
다음은 {city}의 {self._get_place_type_korean(place_type)} 검색 결과입니다.
이 중에서 **최대 {max_count}개**를 선별해주세요.

{criteria}

**장소 목록**:
{', '.join(place_names)}

**응답 형식 (JSON만)**:
{{
  "selected": ["선별된 장소1", "선별된 장소2", "선별된 장소3"],
  "reason": "선별 이유 1-2문장"
}}

**중요**: 
- JSON만 응답하세요 (코드 블록 불필요)
- 장소명은 위 목록에 있는 그대로 정확히 적으세요
- 최대 {max_count}개까지만 선별
"""
    
    def _get_place_emoji(self, place_type: str) -> str:
        """place_type별 이모지 반환"""
        emoji_map = {
            'tourist_attraction': '🏛️',
            'restaurant': '🍽️',
            'cafe': '☕',
            'bar': '🍷',
            'spa': '♨️',
            'night_view': '🌃'
        }
        return emoji_map.get(place_type, '📍')
    
    def _get_place_type_korean(self, place_type: str) -> str:
        """place_type 한글명 반환"""
        korean_map = {
            'tourist_attraction': '필수 관광지',
            'restaurant': '유명 맛집',
            'cafe': '인기 카페',
            'bar': '유명 바/야경',
            'spa': '감성 온천/스파',
            'night_view': '야경 명소'
        }
        return korean_map.get(place_type, '추천 장소')
    
    async def analyze_nearby_regions_with_ai(
        self,
        city: str,
        days_count: int
    ) -> List[str]:
        """
        AI를 활용하여 근교 지역 파악 (Redis 캐싱 적용)
        
        Args:
            city: 중심 도시 (예: "순천")
            days_count: 여행 일수
        
        Returns:
            근교 도시 리스트 (예: ["여수", "광양", "보성"])
        """
        
        # 🆕 Step 1: AI 캐시 확인
        from app.services.ai_cache_service import get_ai_cache_service
        ai_cache = get_ai_cache_service()
        
        cache_key = f"{city}_{days_count}"
        cached_result = ai_cache.get_cached_ai_response('nearby_regions', cache_key)
        
        if cached_result:
            nearby_cities = cached_result.get('nearby_cities', [])
            reason = cached_result.get('reason', '')
            
            print(f"\n🤖 AI 근교 분석 결과 (캐시):")
            print(f"   중심: {city}")
            print(f"   근교: {', '.join(nearby_cities)}")
            print(f"   이유: {reason}")
            
            return nearby_cities
        
        # 🆕 Step 2: OpenAI API 호출
        try:
            from openai import AsyncOpenAI
            import os
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("   ℹ️ OpenAI API 키 없음 → 근교 검색 건너뛰기")
                return []
            
            client = AsyncOpenAI(api_key=api_key)
            
            prompt = f"""
다음 도시의 근교에서 {days_count}박{days_count+1}일 여행 시 함께 방문하기 좋은 도시들을 추천해주세요.

**중심 도시**: {city}
**여행 기간**: {days_count}박{days_count+1}일

**조건**:
1. 차량 또는 대중교통으로 1시간 내외 거리
2. 여행지로 가치가 있는 곳
3. 최대 3개 도시만 추천
4. 가까운 순서대로 나열

**응답 형식 (JSON만)**:
{{
  "nearby_cities": ["도시1", "도시2", "도시3"],
  "reason": "추천 이유 (1-2 문장)"
}}

**중요**: JSON 형식으로만 응답하세요.
"""
            
            response = await client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "당신은 한국 지리 전문가입니다. 여행 동선을 고려하여 근교 도시를 추천합니다."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            
            # JSON 코드 블록 제거
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
                content = content.strip()
            
            # 빈 응답 처리
            if not content:
                print(f"⚠️ AI 응답이 비어있음")
                return []
            
            # JSON 파싱
            import json
            result = json.loads(content)
            
            nearby_cities = result.get('nearby_cities', [])
            reason = result.get('reason', '')
            
            print(f"\n🤖 AI 근교 분석 결과:")
            print(f"   중심: {city}")
            print(f"   근교: {', '.join(nearby_cities)}")
            print(f"   이유: {reason}")
            
            # 🆕 Step 3: Redis에 캐싱
            ai_cache.save_ai_response('nearby_regions', cache_key, result)
            
            return nearby_cities
            
        except Exception as e:
            print(f"⚠️ AI 근교 분석 실패: {e}")
            return []
    
    async def expand_to_nearby_regions(
        self,
        city: str,
        days_count: int,
        current_places: List[Dict],
        keywords: List[str]
    ) -> tuple[List[Dict], List[str]]:
        """
        AI로 근교 지역 파악 후 검색 확대
        
        Args:
            city: 중심 도시
            days_count: 여행 일수
            current_places: 현재 발견된 장소 리스트
            keywords: 검색 키워드 리스트
        
        Returns:
            (확장된 장소 리스트, 검색한 도시 리스트)
        """
        
        if self.check_place_sufficiency(current_places, days_count):
            return current_places, []  # 충분하면 그대로
        
        print(f"\n🔍 AI 근교 지역 확대 검색 시작...")
        
        # AI로 근교 도시 파악
        nearby_cities = await self.analyze_nearby_regions_with_ai(city, days_count)
        
        if not nearby_cities:
            print(f"   ℹ️ 근교 도시 미발견 → 원래 도시만 사용")
            return current_places, []
        
        expanded_cities = []
        
        # 각 근교 도시에서 검색
        for nearby_city in nearby_cities:
            print(f"\n   🌐 {nearby_city} 검색 중...")
            
            # 근교 도시도 지능형 해석기로 좌표 획득
            try:
                from app.services.intelligent_location_resolver import get_intelligent_resolver
                resolver = get_intelligent_resolver()
                location_info = await resolver.resolve_location(nearby_city)
                
                if location_info:
                    expanded_cities.append(nearby_city)
                    
                    # 키워드별 검색 (상위 3개 키워드만)
                    for keyword in keywords[:3]:
                        search_key = self.cache_service.generate_search_key(nearby_city, keyword)
                        
                        # 캐시 확인
                        cached = self.cache_service.get_cached_data(search_key)
                        if cached:
                            current_places.extend(cached)
                            print(f"      ✅ {keyword}: {len(cached)}개 (캐시)")
                        else:
                            # Naver API로 검색
                            try:
                                search_result = await self.naver_service.search_local(f"{nearby_city} {keyword}")
                                
                                if search_result and 'items' in search_result:
                                    new_places = search_result['items'][:10]
                                    
                                    if new_places:
                                        self.cache_service.save_crawled_data(search_key, new_places)
                                        current_places.extend(new_places)
                                        print(f"      ✅ {keyword}: {len(new_places)}개 (신규)")
                            except Exception as e:
                                print(f"      ⚠️ {keyword} 검색 실패: {e}")
                    
                    print(f"   📊 {nearby_city} 총: {len(current_places)}개 (누적)")
                    
                    # 충분해지면 중단
                    if self.check_place_sufficiency(current_places, days_count):
                        print(f"   ✅ 충분한 장소 확보!")
                        break
            
            except Exception as e:
                print(f"   ⚠️ {nearby_city} 검색 실패: {e}")
                continue
        
        return current_places, expanded_cities
    
    async def discover_places_sequential(
        self,
        schedule_frame: List[Dict[str, Any]],
        base_location: tuple[float, float],
        city: str
    ) -> List[Dict[str, Any]]:
        """
        스케줄 틀을 순회하며 실제 장소를 순차적으로 검색
        
        Args:
            schedule_frame: AI가 생성한 스케줄 틀
            base_location: 기준 위치 (위도, 경도)
            city: 도시명
        
        Returns:
            실제 장소 정보가 채워진 스케줄
        """
        print(f"\n🔍 일괄 장소 검색 시작 (AI 한 번에 처리)")
        print(f"   스케줄 프레임: {len(schedule_frame)}개")
        print(f"   🎯 기준 위치 (base_location): {base_location}")
        print(f"      위도: {base_location[0]:.4f}")
        print(f"      경도: {base_location[1]:.4f}")
        
        # 🆕 Step 1: 모든 시간대에 대해 Google Places 검색 (AI 없이)
        print(f"\n📋 Step 1: 모든 시간대 Google Places 검색")
        all_places_by_timeslot = {}
        current_location = base_location
        current_city = city
        
        for idx, frame_item in enumerate(schedule_frame, 1):
            day = frame_item.get('day', 1)
            time_slot = frame_item.get('time_slot', '')
            place_type = frame_item.get('place_type', 'tourist_attraction')
            keywords = frame_item.get('search_keywords', [])
            radius_km = frame_item.get('search_radius_km', 3.0)
            purpose = frame_item.get('purpose', '')
            
            # 🚫 찜질방/사우나 타입은 즉시 스킵 (로그도 간단하게)
            if place_type in ['spa', 'hot_spring_spa', 'sauna', 'jjimjilbang']:
                print(f"\n   [{idx}/{len(schedule_frame)}] 🚫 {place_type} 타입 스킵 (여행지 부적합)")
                all_places_by_timeslot[idx-1] = []
                continue
            
            print(f"\n   [{idx}/{len(schedule_frame)}] {day}일차 {time_slot} - {place_type}")
            print(f"      도시: {current_city}")
            print(f"      키워드: {keywords}")
            print(f"      현재 위치: {current_location}")
            print(f"      검색 반경: {radius_km}km")
            
            # 이전 위치 기준 근처 장소 검색 (AI 없이)
            try:
                places = await self._search_places_nearby_raw(
                    city=current_city,
                    keywords=keywords,
                    center_lat=current_location[0],
                    center_lng=current_location[1],
                    radius_km=radius_km,
                    place_type=place_type
                )
                
                # 결과 저장 (AI 필터링은 나중에 일괄 처리)
                all_places_by_timeslot[idx-1] = places  # idx는 1부터 시작하므로 -1
                print(f"      ✅ 검색 완료: {len(places)}개")
                
                # 🆕 임시로 첫 번째 장소를 current_location으로 설정 (동선 유지)
                if places:
                    current_location = (places[0].get('lat', current_location[0]), 
                                      places[0].get('lng', current_location[1]))
            
            except Exception as e:
                print(f"      ❌ 검색 실패: {e}")
                all_places_by_timeslot[idx-1] = []
        
        # 🆕 Step 2: AI에게 모든 장소를 한 번에 보내서 최적 조합 선택
        print(f"\n🤖 Step 2: AI 일괄 필터링")
        selected_map = await self.filter_all_places_batch(
            schedule_frame,
            all_places_by_timeslot,
            city
        )
        
        # 🆕 Step 3: 선택된 장소로 스케줄 채우기
        print(f"\n📝 Step 3: 스케줄 채우기")
        filled_schedule = []
        used_places = set()
        
        for idx, frame_item in enumerate(schedule_frame):
            day = frame_item.get('day', 1)
            time_slot = frame_item.get('time_slot', '')
            place_type = frame_item.get('place_type', 'tourist_attraction')
            purpose = frame_item.get('purpose', '')
            
            # AI가 선택한 장소 가져오기
            selected_place = selected_map.get(idx)
            
            # 폴백: AI가 선택 못했으면 첫 번째 장소 사용
            if not selected_place:
                places_for_slot = all_places_by_timeslot.get(idx, [])
                for place in places_for_slot:
                    place_id = place.get('name', '') + place.get('address', '')
                    if place_id not in used_places:
                        selected_place = place
                        used_places.add(place_id)
                        break
            
            if selected_place:
                # 중복 방지
                place_id = selected_place.get('name', '') + selected_place.get('address', '')
                used_places.add(place_id)
                
                # 🆕 Naver 블로그 후기 검색
                blog_reviews = []
                try:
                    place_name = selected_place.get('name', '')
                    if place_name:
                        print(f"      📝 블로그 후기 검색 중: {place_name}")
                        from app.services.naver_service import NaverService
                        naver_service = NaverService()
                        blog_results = await naver_service.search_blogs(f"{city} {place_name}", display=3)
                        blog_reviews = blog_results[:3] if blog_results else []  # 🆕 장소당 최대 3개 블로그 제한
                        if blog_reviews:
                            print(f"      ✅ 블로그 후기 {len(blog_reviews)}개 수집")
                            # 🆕 각 블로그 링크 확인
                            for blog_idx, blog in enumerate(blog_reviews, 1):
                                blog_link = blog.get('link') or blog.get('url') or ''
                                blog_title = blog.get('title', '제목없음')
                                print(f"         [{blog_idx}] {blog_title[:30]}")
                                print(f"             링크: {blog_link[:80] if blog_link else '❌ 링크 없음!'}")
                        else:
                            print(f"      ⚠️ 블로그 후기 없음")
                except Exception as e:
                    print(f"      ⚠️ 블로그 검색 실패: {e}")
                
                # 프레임 정보와 실제 장소 정보 병합
                filled_item = {
                    "day": day,
                    "time": time_slot.split('-')[0],  # 시작 시간만
                    "place_name": selected_place.get('name'),
                    "place_type": place_type,
                    "purpose": purpose,
                    "address": selected_place.get('address'),
                    "lat": selected_place.get('lat'),
                    "lng": selected_place.get('lng'),
                    "description": selected_place.get('description', purpose),
                    "rating": selected_place.get('rating', 0),
                    "duration": f"{frame_item.get('expected_duration_minutes', 90)}분",
                    "verified": True,
                    "google_info": selected_place.get('google_info', {}),
                    "naver_info": selected_place.get('naver_info', {}),
                    "blog_reviews": blog_reviews  # 🆕 블로그 후기 추가
                }
                
                filled_schedule.append(filled_item)
                print(f"      ✅ 채움: {selected_place.get('name')}")
            else:
                print(f"      ⚠️ 적합한 장소 없음")
        
        print(f"\n✅ 순차적 장소 검색 완료: {len(filled_schedule)}개 장소")
        return filled_schedule
    
    async def _search_places_nearby_raw(
        self,
        city: str,
        keywords: List[str],
        center_lat: float,
        center_lng: float,
        radius_km: float,
        place_type: str
    ) -> List[Dict[str, Any]]:
        """
        🆕 Google Places 검색 + 거리 필터링만 (AI 없음)
        일괄 처리를 위해 사용
        
        Note: 찜질방/사우나 타입은 호출 전에 이미 필터링됨
        """
        all_places = []
        
        # Step 1: Google Places 검색 (광범위하게)
        print(f"      🔍 Google Places 검색: {self._get_place_type_korean(place_type)}")
        print(f"         키워드: {keywords[:2]}")
        
        for keyword in keywords[:2]:
            query = f"{city} {keyword}"
            
            try:
                google_results = await self.google_service.search_nearby_places(
                    query=query,
                    location=(center_lat, center_lng),
                    radius=int(radius_km * 1000),
                    language="ko"
                )
                
                print(f"         📊 '{keyword}': {len(google_results)}개")
                
                for item in google_results:
                    lat = item.get('lat')
                    lng = item.get('lng')
                    name = item.get('name', '')
                    address = item.get('address', '')
                    
                    if lat and lng and -90 <= lat <= 90 and -180 <= lng <= 180:
                        place = {
                            "name": name,
                            "address": address,
                            "description": item.get('description', ''),
                            "category": item.get('category', ''),
                            "rating": item.get('rating', 0),
                            "lat": lat,
                            "lng": lng,
                            "google_info": item
                        }
                        all_places.append(place)
            
            except Exception as e:
                print(f"         ❌ 검색 실패 ({keyword}): {e}")
        
        # Step 2: 거리 필터링
        print(f"      📏 거리 필터링: {len(all_places)}개 → {radius_km}km 이내")
        
        filtered_places = []
        for place in all_places:
            distance = self.geo_filter.calculate_distance(
                center_lat, center_lng,
                place['lat'], place['lng']
            )
            
            if distance <= radius_km:
                place['distance_from_center'] = distance
                filtered_places.append(place)
        
        # 중복 제거 (이름 기준)
        seen_names = set()
        unique_places = []
        for place in filtered_places:
            if place['name'] not in seen_names:
                seen_names.add(place['name'])
                unique_places.append(place)
        
        print(f"         ✅ 거리 필터링 후: {len(unique_places)}개")
        
        # AI 필터링 없이 원본 반환 (일괄 처리용)
        return unique_places
    
    async def _search_places_nearby(
        self,
        city: str,
        keywords: List[str],
        center_lat: float,
        center_lng: float,
        radius_km: float,
        place_type: str
    ) -> List[Dict[str, Any]]:
        """
        특정 위치 근처에서 키워드로 장소 검색 + AI 필터링 (레거시)
        """
        # Raw 검색 후 AI 필터링
        places = await self._search_places_nearby_raw(
            city, keywords, center_lat, center_lng, radius_km, place_type
        )
        
        # AI 필터링
        if len(places) > 5:
            print(f"      🤖 AI 필터링: {len(places)}개 → 최대 5개 선별")
            filtered_by_ai = await self.filter_places_with_ai(
                places,
                city,
                place_type,
                max_count=5
            )
            return filtered_by_ai
        else:
            print(f"      ✅ 결과: {len(places)}개 (AI 필터링 스킵)")
            return places[:5]

