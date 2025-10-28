"""
장소 품질 검증 서비스

실제 장소 존재 여부 확인, 중복 제거, 할루시네이션 방지
"""

from typing import Dict, Any, List, Set, Tuple
from app.utils.similarity import are_similar_places, are_same_location, normalize_place_name

class PlaceQualityService:
    def __init__(self):
        # 사용된 장소 목록 (이름, 주소, 좌표)
        self.used_places: List[Dict[str, Any]] = []
        # 빠른 조회를 위한 정규화된 이름 세트
        self.normalized_names: Set[str] = set()
    
    def verify_real_place(self, enhanced_item: Dict[str, Any]) -> bool:
        """실제 장소 존재 여부 확인"""
        has_naver = bool(enhanced_item.get('naver_info', {}).get('name'))
        has_google = bool(enhanced_item.get('google_info', {}).get('name'))
        has_reviews = bool(enhanced_item.get('blog_reviews'))
        
        # 최소 2개 이상의 소스에서 확인되어야 실제 장소로 인정
        verification_count = sum([has_naver, has_google, has_reviews])
        return verification_count >= 2
    
    def is_duplicate(self, place_name: str, address: str, lat: float = None, lng: float = None) -> bool:
        """
        강화된 중복 장소 검사
        
        1. 정규화된 이름으로 빠른 조회
        2. 문자열 유사도 검사
        3. 좌표 기반 위치 검사
        """
        if not place_name:
            return False
        
        # 1. 정규화된 이름으로 빠른 조회
        normalized_name = normalize_place_name(place_name)
        if normalized_name in self.normalized_names:
            print(f"🔍 중복 발견 (정규화 이름): {place_name}")
            return True
        
        # 2. 기존 장소들과 유사도 비교
        for used_place in self.used_places:
            used_name = used_place.get('name', '')
            used_address = used_place.get('address', '')
            used_lat = used_place.get('lat')
            used_lng = used_place.get('lng')
            
            # 이름 유사도 검사 (임계값: 0.85)
            if are_similar_places(place_name, used_name, threshold=0.85):
                print(f"🔍 중복 발견 (유사 이름): {place_name} ≈ {used_name}")
                return True
            
            # 주소 유사도 검사
            if address and used_address:
                if are_similar_places(address, used_address, threshold=0.9):
                    print(f"🔍 중복 발견 (유사 주소): {address} ≈ {used_address}")
                    return True
            
            # 좌표 기반 위치 검사 (50m 이내)
            if lat and lng and used_lat and used_lng:
                if are_same_location(lat, lng, used_lat, used_lng, threshold=50.0):
                    print(f"🔍 중복 발견 (같은 위치): {place_name} ({lat}, {lng})")
                    return True
        
        return False
    
    def add_to_used(self, place_name: str, address: str, lat: float = None, lng: float = None):
        """사용된 장소 목록에 추가"""
        self.used_places.append({
            'name': place_name,
            'address': address,
            'lat': lat,
            'lng': lng
        })
        
        # 정규화된 이름도 추가
        normalized_name = normalize_place_name(place_name)
        if normalized_name:
            self.normalized_names.add(normalized_name)
        
        print(f"✅ 장소 추가: {place_name} (총 {len(self.used_places)}개)")
    
    def clear(self):
        """사용된 장소 목록 초기화"""
        self.used_places.clear()
        self.normalized_names.clear()
    
    def get_used_count(self) -> int:
        """사용된 장소 수 반환"""
        return len(self.used_places)
    
    def calculate_quality_score(self, enhanced_item: Dict[str, Any]) -> float:
        """장소 품질 점수 계산"""
        score = 0.0
        
        # 구글 평점 (40%)
        google_info = enhanced_item.get('google_info', {})
        if google_info.get('rating', 0) > 0:
            score += google_info['rating'] * 0.4
        
        # 네이버 장소 정보 (30%)
        naver_info = enhanced_item.get('naver_info', {})
        if naver_info and naver_info.get('name'):
            score += 4.5 * 0.3
        
        # 블로그 후기 수 (20%)
        blog_reviews = enhanced_item.get('blog_reviews', [])
        if blog_reviews and len(blog_reviews) > 0:
            review_score = min(len(blog_reviews) + 2, 5.0)
            score += review_score * 0.2
        
        # 블로그 내용 품질 (10%)
        blog_contents = enhanced_item.get('blog_contents', [])
        if blog_contents:
            score += 4.0 * 0.1
        
        return min(score, 5.0)
    
    def create_verified_item(self, original_item: Dict[str, Any], enhanced_item: Dict[str, Any], quality_score: float) -> Dict[str, Any]:
        """검증된 장소 아이템 생성"""
        verified_item = original_item.copy()
        
        # Google 데이터로 업데이트
        if enhanced_item.get('google_info'):
            google_info = enhanced_item['google_info']
            verified_item.update({
                'place_name': google_info.get('name', original_item.get('place_name')),
                'address': google_info.get('address', original_item.get('address')),
                'lat': google_info.get('lat', original_item.get('lat', 37.5665)),
                'lng': google_info.get('lng', original_item.get('lng', 126.9780)),
                'rating': google_info.get('rating', 0),
                'phone': google_info.get('phone', ''),
                'website': google_info.get('website', ''),
                'opening_hours': google_info.get('opening_hours', [])
            })
        
        # Naver 데이터로 보완
        if enhanced_item.get('naver_info'):
            naver_info = enhanced_item['naver_info']
            verified_item.update({
                'verified_address': naver_info.get('address', verified_item.get('address')),
                'phone': naver_info.get('phone', verified_item.get('phone', ''))
            })
        
        # 블로그 데이터 추가
        verified_item.update({
            'blog_reviews': enhanced_item.get('blog_reviews', []),
            'blog_contents': enhanced_item.get('blog_contents', []),
            'verified': True,
            'quality_score': quality_score
        })
        
        return verified_item
    
    def get_fallback_places(self, needed_count: int) -> List[Dict[str, Any]]:
        """최소 장소 수 보장을 위한 대체 장소 추가"""
        fallback_places = [
            {
                'place_name': '명동 쇼핑거리',
                'address': '서울시 중구 명동길',
                'activity': '쇼핑 및 거리 구경',
                'time': '15:00',
                'duration': '60분',
                'description': '서울의 대표적인 쇼핑 및 관광 명소',
                'transportation': '지하철 4호선 명동역',
                'rating': 4.2,
                'price': '무료',
                'lat': 37.5636,
                'lng': 126.9834,
                'verified': True,
                'quality_score': 4.0
            },
            {
                'place_name': '홍대 걷고싶은거리',
                'address': '서울시 마포구 서교동',
                'activity': '거리 구경 및 카페',
                'time': '16:30',
                'duration': '90분',
                'description': '젊음의 거리, 다양한 카페와 상점',
                'transportation': '지하철 2호선 홍대입구역',
                'rating': 4.1,
                'price': '무료',
                'lat': 37.5563,
                'lng': 126.9236,
                'verified': True,
                'quality_score': 4.0
            },
            {
                'place_name': '한강공원 여의도',
                'address': '서울시 영등포구 여의동로',
                'activity': '산책 및 휴식',
                'time': '18:00',
                'duration': '60분',
                'description': '한강을 따라 산책할 수 있는 공원',
                'transportation': '지하철 5호선 여의나루역',
                'rating': 4.3,
                'price': '무료',
                'lat': 37.5285,
                'lng': 126.9335,
                'verified': True,
                'quality_score': 4.2
            }
        ]
        
        added_places = []
        for place in fallback_places:
            if len(added_places) >= needed_count:
                break
            if not self.is_duplicate(place['place_name'], place['address']):
                added_places.append(place)
                self.add_to_used(place['place_name'], place['address'])
        
        return added_places