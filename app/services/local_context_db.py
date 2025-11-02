"""
지역 맥락 데이터베이스 (Local Context Database)

각 지역의 특성, 타겟층, 가격대, 인기 시간대 등
세밀한 컨텍스트 정보를 제공합니다.

🆕 동적 확장: DB에 없는 지역은 실시간으로 정보 수집하여 자동 생성
"""

from typing import Dict, Any, List, Optional
import asyncio


class LocalContextDB:
    """지역별 특화 정보 데이터베이스 (정적 + 동적)"""
    
    # 동적 컨텍스트 캐시 (런타임에 생성된 지역 정보)
    # 메모리 기반 캐시로 30일간 보관
    DYNAMIC_CONTEXT_CACHE: Dict[str, Dict[str, Any]] = {}
    
    def __init__(self):
        """캐시 만료 시간 설정"""
        from datetime import timedelta
        self.cache_duration = timedelta(days=30)
    
    # 지역 특성 데이터베이스
    CONTEXT_DB = {
        # ========== 서울 ==========
        '마곡동': {
            'characteristics': [
                'IT 기업 밀집지역',
                'LG사이언스파크',
                '비즈니스 특구',
                '점심시간 혼잡',
                '스타트업 허브',
                '신규 개발 지역'
            ],
            'popular_times': {
                '아침': '07:30-09:00',
                '점심': '12:00-13:30',
                '저녁': '18:00-20:00'
            },
            'target_demographics': ['직장인', 'IT 종사자', '엔지니어', '스타트업 직원'],
            'price_range': 'medium_high',  # 직장인 대상, 10,000-15,000원
            'cuisine_preferences': ['한식', '일식', '샐러드', '커피', '브런치', '프랜차이즈'],
            'nearby_landmarks': [
                {'name': 'LG사이언스파크', 'lat': 37.5614, 'lng': 126.8279, 'type': 'business'},
                {'name': '마곡나루역', 'lat': 37.5605, 'lng': 126.8251, 'type': 'transit'},
                {'name': '마곡역', 'lat': 37.5602, 'lng': 126.8255, 'type': 'transit'},
                {'name': '마곡 롯데월드몰', 'lat': 37.5620, 'lng': 126.8273, 'type': 'shopping'}
            ],
            'competitor_regions': ['여의도', '상암DMC', '판교'],  # 유사한 특성
            'avoid_regions': ['강남', '홍대', '명동'],  # 전혀 다른 성격
            'best_for': ['점심 회식', '비즈니스 미팅', 'IT 네트워킹'],
            'atmosphere': 'modern_business'
        },
        
        '역삼동': {
            'characteristics': [
                '강남 비즈니스 중심',
                '스타트업 밸리',
                '고층 빌딩',
                '테헤란로',
                '벤처기업 밀집',
                '비즈니스 호텔 다수'
            ],
            'popular_times': {
                '아침': '07:00-09:00',
                '점심': '11:30-13:30',
                '저녁': '18:00-21:00',
                '야식': '22:00-00:00'
            },
            'target_demographics': ['직장인', '스타트업', '투자자', '외국인 비즈니스맨'],
            'price_range': 'high',  # 강남 프리미엄, 15,000-25,000원
            'cuisine_preferences': ['일식', '양식', '고급 한식', '이탈리안', '와인바', '카페'],
            'nearby_landmarks': [
                {'name': '강남역', 'lat': 37.4981, 'lng': 127.0276, 'type': 'transit'},
                {'name': '역삼역', 'lat': 37.5009, 'lng': 127.0359, 'type': 'transit'},
                {'name': '테헤란로', 'lat': 37.5009, 'lng': 127.0359, 'type': 'business'},
                {'name': '선릉역', 'lat': 37.5045, 'lng': 127.0489, 'type': 'transit'}
            ],
            'competitor_regions': ['삼성동', '청담동', '여의도'],
            'avoid_regions': ['홍대', '이태원', '성수'],
            'best_for': ['비즈니스 미팅', '투자자 미팅', '고급 회식', '외국인 접대'],
            'atmosphere': 'upscale_business'
        },
        
        '서교동': {  # 홍대
            'characteristics': [
                '젊음의 거리',
                '클럽 문화',
                '인디 음악',
                '예술가 밀집',
                '트렌디한 카페',
                '국제적 분위기'
            ],
            'popular_times': {
                '브런치': '11:00-14:00',
                '카페': '14:00-18:00',
                '저녁': '18:00-22:00',
                '나이트': '22:00-04:00'
            },
            'target_demographics': ['대학생', '20-30대', '외국인', '예술가', '프리랜서'],
            'price_range': 'medium',  # 학생 친화적, 8,000-12,000원
            'cuisine_preferences': ['멕시칸', '버거', '피자', '브런치', '디저트', '이국 음식'],
            'nearby_landmarks': [
                {'name': '홍대입구역', 'lat': 37.5571, 'lng': 126.9245, 'type': 'transit'},
                {'name': '홍익대학교', 'lat': 37.5509, 'lng': 126.9228, 'type': 'education'},
                {'name': '홍대 클럽거리', 'lat': 37.5540, 'lng': 126.9220, 'type': 'entertainment'},
                {'name': '연남동 카페거리', 'lat': 37.5667, 'lng': 126.9245, 'type': 'cafe'}
            ],
            'competitor_regions': ['이태원', '성수', '한남'],
            'avoid_regions': ['강남', '여의도', '종로'],
            'best_for': ['데이트', '친구 모임', '카페 투어', '클럽', '브런치'],
            'atmosphere': 'trendy_young'
        },
        
        '여의도동': {
            'characteristics': [
                '금융 중심지',
                '국회의사당',
                '한강공원',
                '증권가',
                '대기업 본사',
                '고급 레스토랑'
            ],
            'popular_times': {
                '아침': '07:00-09:00',
                '점심': '12:00-13:30',
                '저녁': '18:00-20:00'
            },
            'target_demographics': ['금융인', '공무원', '대기업 임원', '정치인'],
            'price_range': 'high',  # 금융가 프리미엄, 15,000-30,000원
            'cuisine_preferences': ['일식', '고급 한식', '양식', '스테이크', '와인'],
            'nearby_landmarks': [
                {'name': '여의도역', 'lat': 37.5219, 'lng': 126.9245, 'type': 'transit'},
                {'name': '국회의사당역', 'lat': 37.5295, 'lng': 126.9149, 'type': 'transit'},
                {'name': 'IFC몰', 'lat': 37.5251, 'lng': 126.9261, 'type': 'shopping'},
                {'name': '여의도 한강공원', 'lat': 37.5285, 'lng': 126.9328, 'type': 'park'}
            ],
            'competitor_regions': ['강남', '광화문', '청담'],
            'avoid_regions': ['홍대', '이태원', '성수'],
            'best_for': ['비즈니스 미팅', '고급 회식', '한강 산책', '데이트'],
            'atmosphere': 'corporate_upscale'
        },
        
        '명동': {
            'characteristics': [
                '관광 명소',
                '쇼핑 천국',
                '외국인 다수',
                '화장품 거리',
                '길거리 음식',
                '명품 매장'
            ],
            'popular_times': {
                '오전': '10:00-12:00',
                '오후': '14:00-18:00',
                '저녁': '18:00-21:00'
            },
            'target_demographics': ['관광객', '외국인', '쇼핑객', '10-30대'],
            'price_range': 'medium_high',  # 관광지 프리미엄, 10,000-20,000원
            'cuisine_preferences': ['한식', '길거리 음식', '디저트', '카페', '치킨', '분식'],
            'nearby_landmarks': [
                {'name': '명동역', 'lat': 37.5610, 'lng': 126.9865, 'type': 'transit'},
                {'name': '명동성당', 'lat': 37.5634, 'lng': 126.9870, 'type': 'landmark'},
                {'name': '남대문시장', 'lat': 37.5595, 'lng': 126.9770, 'type': 'market'},
                {'name': '롯데백화점', 'lat': 37.5650, 'lng': 126.9810, 'type': 'shopping'}
            ],
            'competitor_regions': ['동대문', '이태원', '인사동'],
            'avoid_regions': ['마곡', '판교', '여의도'],
            'best_for': ['쇼핑', '관광', '화장품 구매', '길거리 음식'],
            'atmosphere': 'tourist_shopping'
        },
        
        # ========== 부산 ==========
        '우동': {  # 해운대
            'characteristics': [
                '해운대 해수욕장',
                '고급 호텔',
                '마린시티',
                '바다 뷰',
                '관광 명소',
                '해산물'
            ],
            'popular_times': {
                '아침': '08:00-10:00',
                '점심': '12:00-14:00',
                '저녁': '18:00-21:00'
            },
            'target_demographics': ['관광객', '가족', '커플', '외국인'],
            'price_range': 'high',  # 관광지 + 해수욕장, 15,000-25,000원
            'cuisine_preferences': ['해산물', '횟집', '회', '조개구이', '카페'],
            'nearby_landmarks': [
                {'name': '해운대해수욕장', 'lat': 35.1631, 'lng': 129.1635, 'type': 'beach'},
                {'name': '해운대역', 'lat': 35.1631, 'lng': 129.1635, 'type': 'transit'},
                {'name': '동백섬', 'lat': 35.1573, 'lng': 129.1511, 'type': 'landmark'},
                {'name': '마린시티', 'lat': 35.1586, 'lng': 129.1420, 'type': 'residential'}
            ],
            'competitor_regions': ['광안리', '송정'],
            'avoid_regions': ['서면', '남포동'],
            'best_for': ['해변 데이트', '가족 여행', '해산물', '휴양'],
            'atmosphere': 'beach_resort'
        },
        
        '부전동': {  # 서면
            'characteristics': [
                '부산 강남',
                '번화가',
                '쇼핑',
                '전포카페거리',
                '젊은 분위기',
                '맛집 밀집'
            ],
            'popular_times': {
                '점심': '12:00-14:00',
                '카페': '14:00-18:00',
                '저녁': '18:00-22:00',
                '나이트': '22:00-02:00'
            },
            'target_demographics': ['20-30대', '대학생', '직장인', '쇼핑객'],
            'price_range': 'medium',  # 부산 평균, 10,000-15,000원
            'cuisine_preferences': ['한식', '일식', '카페', '술집', '고기', '해산물'],
            'nearby_landmarks': [
                {'name': '서면역', 'lat': 35.1561, 'lng': 129.0601, 'type': 'transit'},
                {'name': '전포카페거리', 'lat': 35.1550, 'lng': 129.0630, 'type': 'cafe'},
                {'name': '롯데백화점', 'lat': 35.1570, 'lng': 129.0590, 'type': 'shopping'}
            ],
            'competitor_regions': ['광안리', '남포동'],
            'avoid_regions': ['해운대', '기장'],
            'best_for': ['쇼핑', '카페 투어', '술자리', '맛집 탐방'],
            'atmosphere': 'urban_trendy'
        },
        
        # ========== 대구 ==========
        '동인동': {  # 동성로
            'characteristics': [
                '대구 명동',
                '젊음의 거리',
                '쇼핑 중심',
                '대학생 문화',
                '치맥 문화',
                '패션 거리'
            ],
            'popular_times': {
                '점심': '12:00-14:00',
                '오후': '14:00-18:00',
                '저녁': '18:00-22:00'
            },
            'target_demographics': ['대학생', '10-20대', '쇼핑객'],
            'price_range': 'low_medium',  # 학생 친화적, 7,000-10,000원
            'cuisine_preferences': ['치맥', '한식', '분식', '카페', '패스트푸드'],
            'nearby_landmarks': [
                {'name': '중앙로역', 'lat': 35.8714, 'lng': 128.6014, 'type': 'transit'},
                {'name': '동성로거리', 'lat': 35.8714, 'lng': 128.6014, 'type': 'shopping'},
                {'name': '대구백화점', 'lat': 35.8700, 'lng': 128.6000, 'type': 'shopping'}
            ],
            'competitor_regions': ['김광석거리', '수성못'],
            'avoid_regions': [],
            'best_for': ['쇼핑', '친구 모임', '데이트', '치맥'],
            'atmosphere': 'young_vibrant'
        }
    }
    
    def get_context(self, location: str) -> Dict[str, Any]:
        """
        지역 컨텍스트 조회 (정적 DB → 동적 캐시 순서)
        
        Args:
            location: 지역명 (예: '마곡동', '역삼동', '청도')
        
        Returns:
            지역 특성 정보 딕셔너리
        """
        # 1. 정적 DB에서 먼저 조회
        static_context = self.CONTEXT_DB.get(location)
        if static_context:
            print(f"   ✅ 정적 DB에서 {location} 컨텍스트 발견")
            return static_context
        
        # 2. 동적 캐시에서 조회
        dynamic_context = self.DYNAMIC_CONTEXT_CACHE.get(location)
        if dynamic_context:
            print(f"   ✅ 동적 캐시에서 {location} 컨텍스트 발견")
            return dynamic_context
        
        # 3. 없으면 빈 딕셔너리 반환 (호출자가 동적 생성 트리거)
        print(f"   ℹ️ {location} 컨텍스트 미발견 → 동적 생성 필요")
        return {}
    
    async def get_or_create_context(self, location: str) -> Dict[str, Any]:
        """
        지역 컨텍스트 조회 또는 동적 생성 (비동기)
        
        Args:
            location: 지역명
        
        Returns:
            지역 컨텍스트 (없으면 동적 생성)
        """
        # 기존 컨텍스트 확인
        existing_context = self.get_context(location)
        if existing_context:
            # 캐시 만료 확인 (동적 생성된 경우만)
            if existing_context.get('cache_until'):
                from datetime import datetime
                cache_until = datetime.fromisoformat(existing_context['cache_until'])
                if datetime.now() > cache_until:
                    print(f"   ⏰ {location} 캐시 만료 → 재생성")
                    # 캐시 삭제
                    if location in self.DYNAMIC_CONTEXT_CACHE:
                        del self.DYNAMIC_CONTEXT_CACHE[location]
                else:
                    return existing_context
            else:
                # 정적 DB 데이터는 만료 없음
                return existing_context
        
        # 동적 생성
        print(f"\n🔄 {location} 동적 컨텍스트 생성 시작...")
        from app.services.dynamic_location_context_service import DynamicLocationContextService
        
        dynamic_service = DynamicLocationContextService()
        new_context = await dynamic_service.generate_location_context(location)
        
        # 캐시에 저장
        self.DYNAMIC_CONTEXT_CACHE[location] = new_context
        print(f"✅ {location} 동적 컨텍스트 생성 및 캐시 저장 완료 (30일 보관)")
        
        return new_context
    
    def cleanup_expired_cache(self):
        """만료된 동적 컨텍스트 정리"""
        from datetime import datetime
        
        expired_locations = []
        current_time = datetime.now()
        
        for location, context in self.DYNAMIC_CONTEXT_CACHE.items():
            cache_until_str = context.get('cache_until')
            if cache_until_str:
                cache_until = datetime.fromisoformat(cache_until_str)
                if current_time > cache_until:
                    expired_locations.append(location)
        
        for location in expired_locations:
            del self.DYNAMIC_CONTEXT_CACHE[location]
            print(f"🗑️ 만료된 캐시 삭제: {location}")
        
        return len(expired_locations)
    
    def enrich_search_with_context(
        self,
        location: str,
        user_request: str,
        time_context: List[str] = None,
        target_context: List[str] = None
    ) -> Dict[str, Any]:
        """
        지역 특성을 반영한 검색 강화
        
        Args:
            location: 지역명
            user_request: 사용자 요청
            time_context: 시간대 컨텍스트 (예: ['점심'])
            target_context: 타겟 컨텍스트 (예: ['직장인'])
        
        Returns:
            강화된 검색 쿼리 및 필터 정보
        """
        context = self.get_context(location)
        
        if not context:
            return {
                'original_request': user_request,
                'enriched': False
            }
        
        enriched_query = {
            'original_request': user_request,
            'location': location,
            'location_characteristics': context.get('characteristics', []),
            'recommended_cuisines': context.get('cuisine_preferences', []),
            'target_price_range': context.get('price_range', 'medium'),
            'optimal_visit_times': context.get('popular_times', {}),
            'nearby_landmarks_for_search': context.get('nearby_landmarks', []),
            'best_for': context.get('best_for', []),
            'atmosphere': context.get('atmosphere', 'general'),
            'enriched': True
        }
        
        # 시간대 매칭
        if time_context:
            for time in time_context:
                if time in context.get('popular_times', {}):
                    enriched_query['recommended_time'] = context['popular_times'][time]
        
        # 타겟층 매칭
        if target_context:
            matched_targets = [
                t for t in context.get('target_demographics', [])
                if any(tc in t for tc in target_context)
            ]
            if matched_targets:
                enriched_query['target_match'] = matched_targets
        
        # 유사 지역 추가 (참고용)
        if context.get('competitor_regions'):
            enriched_query['reference_regions'] = context['competitor_regions']
        
        # 회피할 지역 명시 (필터링용)
        if context.get('avoid_regions'):
            enriched_query['exclude_regions'] = context['avoid_regions']
        
        return enriched_query
    
    def get_price_range_filter(self, price_range: str) -> tuple:
        """
        가격대 문자열을 실제 금액 범위로 변환
        
        Returns:
            (min_price, max_price) 튜플 (원 단위)
        """
        price_ranges = {
            'low': (5000, 8000),
            'low_medium': (7000, 10000),
            'medium': (8000, 12000),
            'medium_high': (10000, 15000),
            'high': (15000, 25000),
            'very_high': (25000, 50000)
        }
        
        return price_ranges.get(price_range, (8000, 12000))
    
    def get_all_contexts(self) -> Dict[str, Dict]:
        """모든 지역 컨텍스트 반환"""
        return self.CONTEXT_DB
    
    def search_by_characteristic(self, characteristic: str) -> List[str]:
        """
        특정 특성을 가진 지역 검색
        
        Args:
            characteristic: 특성 키워드 (예: 'IT', '해변', '대학생')
        
        Returns:
            매칭되는 지역명 리스트
        """
        matched_locations = []
        
        for location, context in self.CONTEXT_DB.items():
            # 특성에서 검색
            if any(characteristic.lower() in char.lower() 
                   for char in context.get('characteristics', [])):
                matched_locations.append(location)
                continue
            
            # 타겟층에서 검색
            if any(characteristic.lower() in demo.lower() 
                   for demo in context.get('target_demographics', [])):
                matched_locations.append(location)
                continue
            
            # best_for에서 검색
            if any(characteristic.lower() in best.lower() 
                   for best in context.get('best_for', [])):
                matched_locations.append(location)
        
        return matched_locations

