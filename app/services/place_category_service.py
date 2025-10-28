"""
장소 카테고리 분류 서비스

장소를 실내/실외/반실외로 분류하여 날씨 기반 추천에 활용합니다.
"""

from typing import Dict, Any, List


# 장소 카테고리 데이터베이스
PLACE_CATEGORIES = {
    "indoor": [
        # 문화/예술
        "박물관", "미술관", "전시관", "갤러리", "공연장", "극장", "영화관",
        # 쇼핑
        "쇼핑몰", "백화점", "마트", "아울렛", "대형서점", "지하상가",
        # 음식
        "카페", "레스토랑", "맛집", "음식점", "식당", "베이커리",
        # 기타
        "도서관", "스파", "찜질방", "노래방", "PC방", "VR체험관",
        "이스케이프룸", "볼링장", "실내클라이밍", "스크린골프",
        "키즈카페", "애견카페", "고양이카페", "방탈출카페"
    ],
    "outdoor": [
        # 자연
        "공원", "한강", "산", "숲", "해변", "해수욕장", "계곡", "폭포",
        "자연휴양림", "수목원", "정원", "호수", "강", "바다",
        # 관광
        "전망대", "성벽", "성곽", "유적지", "야외공연장",
        # 활동
        "캠핑장", "산책로", "자전거도로", "등산로", "트레킹코스",
        "야외운동장", "축구장", "야구장", "골프장"
    ],
    "semi_outdoor": [
        # 부분 실내
        "테마파크", "동물원", "식물원", "전통시장", "재래시장",
        "야시장", "아쿠아리움", "수족관", "민속촌", "한옥마을",
        "궁궐", "사찰", "성당", "교회"
    ]
}

# 날씨 기반 키워드
WEATHER_KEYWORDS = {
    "rainy_ok": ["실내", "indoor", "지하", "루프톱", "카페", "박물관", "쇼핑몰"],
    "sunny_preferred": ["야외", "outdoor", "공원", "한강", "산", "해변", "전망"],
    "cold_ok": ["온천", "찜질방", "따뜻한", "실내", "온수", "히터"],
    "hot_ok": ["수영장", "물놀이", "에어컨", "시원한", "아이스", "냉방"]
}


class PlaceCategoryService:
    """장소 카테고리 분류 및 날씨 적합도 판단"""
    
    def __init__(self):
        # 키워드 인덱스 생성 (빠른 검색)
        self.indoor_keywords = set(PLACE_CATEGORIES["indoor"])
        self.outdoor_keywords = set(PLACE_CATEGORIES["outdoor"])
        self.semi_outdoor_keywords = set(PLACE_CATEGORIES["semi_outdoor"])
    
    def classify_place(self, place_name: str, description: str = "", address: str = "") -> str:
        """
        장소를 실내/실외/반실외로 분류
        
        Args:
            place_name: 장소 이름
            description: 장소 설명
            address: 주소
        
        Returns:
            "indoor", "outdoor", "semi_outdoor" 중 하나
        """
        # 텍스트 통합 및 소문자 변환
        text = f"{place_name} {description} {address}".lower()
        
        # 각 카테고리별 매칭 점수 계산
        indoor_score = sum(1 for keyword in self.indoor_keywords if keyword in text)
        outdoor_score = sum(1 for keyword in self.outdoor_keywords if keyword in text)
        semi_outdoor_score = sum(1 for keyword in self.semi_outdoor_keywords if keyword in text)
        
        # 가장 높은 점수의 카테고리 반환
        scores = {
            "indoor": indoor_score,
            "outdoor": outdoor_score,
            "semi_outdoor": semi_outdoor_score
        }
        
        # 점수가 모두 0이면 기본값
        if max(scores.values()) == 0:
            # 기본적으로 실내로 간주 (안전한 선택)
            return "indoor"
        
        category = max(scores, key=scores.get)
        print(f"🏷️ 장소 분류: {place_name} -> {category} (점수: {scores})")
        
        return category
    
    def is_weather_suitable(
        self,
        place_category: str,
        weather_condition: str,
        temperature: float,
        rain_probability: float
    ) -> Dict[str, Any]:
        """
        장소가 현재 날씨에 적합한지 판단
        
        Args:
            place_category: "indoor", "outdoor", "semi_outdoor"
            weather_condition: 날씨 상태
            temperature: 기온 (섭씨)
            rain_probability: 강수 확률 (%)
        
        Returns:
            {
                "suitable": bool,
                "score": float (0.0 ~ 1.0),
                "reason": str
            }
        """
        score = 0.5  # 기본 점수
        reasons = []
        
        # 1. 비 올 확률 고려
        if rain_probability > 50:
            if place_category == "indoor":
                score += 0.4
                reasons.append("비 올 확률이 높아 실내 활동 추천")
            elif place_category == "outdoor":
                score -= 0.4
                reasons.append("비 올 확률이 높아 야외 활동 비추천")
            else:  # semi_outdoor
                score -= 0.2
                reasons.append("비 올 확률이 있어 주의 필요")
        
        # 2. 날씨 상태 고려
        if "rain" in weather_condition.lower() or "비" in weather_condition:
            if place_category == "indoor":
                score += 0.3
                reasons.append("비가 와서 실내 활동 최적")
            else:
                score -= 0.3
                reasons.append("비가 와서 야외 활동 부적합")
        
        if "clear" in weather_condition.lower() or "sunny" in weather_condition.lower() or "맑" in weather_condition:
            if place_category == "outdoor":
                score += 0.3
                reasons.append("맑은 날씨로 야외 활동 최적")
            elif place_category == "indoor":
                score += 0.1
                reasons.append("맑은 날씨지만 실내도 좋음")
        
        # 3. 기온 고려
        if temperature < 5:  # 추운 날씨
            if place_category == "indoor":
                score += 0.3
                reasons.append(f"추운 날씨({temperature}°C)로 실내 활동 추천")
            else:
                score -= 0.2
                reasons.append(f"추운 날씨({temperature}°C)로 야외 활동 주의")
        
        elif temperature > 28:  # 더운 날씨
            if place_category == "indoor":
                score += 0.2
                reasons.append(f"더운 날씨({temperature}°C)로 시원한 실내 추천")
            elif place_category == "outdoor":
                score -= 0.2
                reasons.append(f"더운 날씨({temperature}°C)로 야외 활동 주의")
        
        elif 15 <= temperature <= 25:  # 적정 온도
            if place_category in ["outdoor", "semi_outdoor"]:
                score += 0.2
                reasons.append(f"쾌적한 날씨({temperature}°C)로 야외 활동 좋음")
        
        # 4. 최종 점수 정규화 (0.0 ~ 1.0)
        score = max(0.0, min(1.0, score))
        suitable = score >= 0.5
        
        return {
            "suitable": suitable,
            "score": round(score, 2),
            "reasons": reasons
        }
    
    def filter_places_by_weather(
        self,
        places: List[Dict[str, Any]],
        weather_data: Dict[str, Any],
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        날씨에 적합한 장소만 필터링 및 우선순위 부여
        
        Args:
            places: 장소 리스트
            weather_data: 날씨 정보
            threshold: 적합도 최소 임계값
        
        Returns:
            우선순위가 부여된 장소 리스트
        """
        filtered_places = []
        
        for place in places:
            # 장소 분류
            place_name = place.get('name', '') or place.get('place_name', '')
            description = place.get('description', '')
            address = place.get('address', '')
            
            category = self.classify_place(place_name, description, address)
            
            # 날씨 적합도 판단
            suitability = self.is_weather_suitable(
                category,
                weather_data.get('condition', '맑음'),
                weather_data.get('temperature', 18),
                weather_data.get('rain_probability', 0)
            )
            
            # 장소에 카테고리 및 적합도 정보 추가
            place['category'] = category
            place['weather_suitability'] = suitability
            place['priority'] = int(suitability['score'] * 10)  # 0-10 점수
            
            # 임계값 이상인 경우만 포함
            if suitability['score'] >= threshold:
                filtered_places.append(place)
                print(f"✅ {place_name}: {category}, 적합도 {suitability['score']}")
            else:
                print(f"❌ {place_name}: {category}, 적합도 {suitability['score']} (제외)")
        
        # 우선순위 기준으로 정렬
        filtered_places.sort(key=lambda x: x.get('priority', 0), reverse=True)
        
        return filtered_places
    
    def get_category_stats(self, places: List[Dict[str, Any]]) -> Dict[str, int]:
        """장소 카테고리 통계"""
        stats = {"indoor": 0, "outdoor": 0, "semi_outdoor": 0}
        
        for place in places:
            category = place.get('category', 'indoor')
            stats[category] = stats.get(category, 0) + 1
        
        return stats


# 테스트
if __name__ == "__main__":
    service = PlaceCategoryService()
    
    # 테스트 장소
    test_places = [
        {"name": "국립중앙박물관", "description": "문화유산 전시", "address": "서울시 용산구"},
        {"name": "한강공원", "description": "야외 휴식 공간", "address": "서울시 영등포구"},
        {"name": "경복궁", "description": "조선시대 궁궐", "address": "서울시 종로구"},
        {"name": "스타벅스 강남점", "description": "카페", "address": "서울시 강남구"}
    ]
    
    # 테스트 날씨 (비오는 날)
    rainy_weather = {
        "condition": "비",
        "temperature": 18,
        "rain_probability": 80
    }
    
    print("=== 비오는 날 장소 필터링 ===")
    filtered = service.filter_places_by_weather(test_places, rainy_weather, threshold=0.4)
    
    for place in filtered:
        print(f"- {place['name']}: {place['category']} (우선순위: {place['priority']})")

