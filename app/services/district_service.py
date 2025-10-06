"""
지역 구역 서비스

도시별 세부 구역 정보 및 효율적 동선 구성
"""

from typing import Dict, Any, List, Tuple
import math

class DistrictService:
    def __init__(self):
        self.districts = {
            "Seoul": {
                "강남구": {
                    "center": {"lat": 37.5173, "lng": 127.0473},
                    "attractions": ["강남역", "코엑스", "가로수길", "압구정로데오", "봉은사", "선릉"],
                    "restaurants": ["강남 맛집거리", "신사동 가로수길 맛집", "압구정 맛집"],
                    "transport_hubs": ["강남역", "신사역", "압구정역", "선릉역"],
                    "characteristics": ["쇼핑", "트렌디", "고급", "카페"]
                },
                "종로구": {
                    "center": {"lat": 37.5735, "lng": 126.9788},
                    "attractions": ["경복궁", "창덕궁", "인사동", "북촌한옥마을", "광화문광장"],
                    "restaurants": ["인사동 전통차", "북촌 한정식", "종로 맛집"],
                    "transport_hubs": ["종각역", "안국역", "경복궁역", "광화문역"],
                    "characteristics": ["전통", "문화", "역사", "궁궐"]
                },
                "중구": {
                    "center": {"lat": 37.5640, "lng": 126.9970},
                    "attractions": ["명동", "남대문시장", "동대문", "N서울타워", "청계천"],
                    "restaurants": ["명동 맛집", "남대문시장 먹거리", "중구 전통시장"],
                    "transport_hubs": ["명동역", "을지로입구역", "동대문역", "회현역"],
                    "characteristics": ["쇼핑", "전통시장", "관광", "야경"]
                },
                "마포구": {
                    "center": {"lat": 37.5663, "lng": 126.9019},
                    "attractions": ["홍대", "상암DMC", "망원한강공원", "마포대교"],
                    "restaurants": ["홍대 맛집", "상수동 맛집", "망원동 맛집"],
                    "transport_hubs": ["홍대입구역", "상수역", "망원역", "디지털미디어시티역"],
                    "characteristics": ["젊음", "클럽", "카페", "예술"]
                },
                "송파구": {
                    "center": {"lat": 37.5145, "lng": 127.1059},
                    "attractions": ["롯데월드", "잠실한강공원", "석촌호수", "올림픽공원"],
                    "restaurants": ["잠실 롯데월드몰 맛집", "송파 맛집"],
                    "transport_hubs": ["잠실역", "석촌역", "송파역", "올림픽공원역"],
                    "characteristics": ["가족", "놀이공원", "쇼핑몰", "한강"]
                },
                "영등포구": {
                    "center": {"lat": 37.5264, "lng": 126.8962},
                    "attractions": ["여의도한강공원", "63빌딩", "타임스퀘어", "영등포시장"],
                    "restaurants": ["여의도 맛집", "영등포 맛집", "타임스퀘어 맛집"],
                    "transport_hubs": ["여의도역", "영등포구청역", "타임스퀘어역"],
                    "characteristics": ["한강", "야경", "쇼핑", "비즈니스"]
                }
            },
            "Busan": {
                "해운대구": {
                    "center": {"lat": 35.1631, "lng": 129.1635},
                    "attractions": ["해운대해수욕장", "동백섬", "누리마루", "달맞이길"],
                    "restaurants": ["해운대 횟집", "해운대 맛집거리"],
                    "transport_hubs": ["해운대역", "동백역"],
                    "characteristics": ["해변", "리조트", "야경", "해산물"]
                },
                "중구": {
                    "center": {"lat": 35.1014, "lng": 129.0320},
                    "attractions": ["자갈치시장", "용두산공원", "부산타워", "국제시장"],
                    "restaurants": ["자갈치시장 회센터", "국제시장 먹거리"],
                    "transport_hubs": ["남포역", "자갈치역", "부산역"],
                    "characteristics": ["전통시장", "해산물", "관광", "항구"]
                }
            }
        }
    
    def get_districts_by_city(self, city: str) -> Dict[str, Any]:
        """도시별 구역 정보 조회"""
        return self.districts.get(city, {})
    
    def calculate_distance(self, point1: Dict[str, float], point2: Dict[str, float]) -> float:
        """두 지점 간 거리 계산 (km)"""
        lat1, lng1 = point1["lat"], point1["lng"]
        lat2, lng2 = point2["lat"], point2["lng"]
        
        # Haversine 공식
        R = 6371  # 지구 반지름 (km)
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlng/2) * math.sin(dlng/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def find_optimal_districts(self, city: str, travel_style: str, duration_hours: int) -> List[str]:
        """여행 스타일과 시간에 따른 최적 구역 선택"""
        districts = self.get_districts_by_city(city)
        if not districts:
            return []
        
        # 여행 스타일별 선호 특성
        style_preferences = {
            "food_tour": ["전통시장", "맛집", "해산물"],
            "culture_tour": ["전통", "문화", "역사", "궁궐"],
            "shopping_tour": ["쇼핑", "트렌디", "쇼핑몰"],
            "night_tour": ["야경", "클럽", "한강"],
            "family_tour": ["가족", "놀이공원", "공원"],
            "healing_tour": ["한강", "공원", "자연"],
            "indoor_date": ["카페", "쇼핑몰", "문화"],
            "outdoor_date": ["한강", "공원", "해변"]
        }
        
        preferences = style_preferences.get(travel_style, [])
        
        # 구역별 점수 계산
        district_scores = {}
        for district_name, district_info in districts.items():
            score = 0
            characteristics = district_info.get("characteristics", [])
            
            # 선호도 매칭
            for pref in preferences:
                if pref in characteristics:
                    score += 10
            
            district_scores[district_name] = score
        
        # 시간에 따른 구역 수 결정
        max_districts = min(3, max(1, duration_hours // 4))
        
        # 점수 순으로 정렬하여 상위 구역 선택
        sorted_districts = sorted(district_scores.items(), key=lambda x: x[1], reverse=True)
        selected_districts = [district[0] for district in sorted_districts[:max_districts]]
        
        return selected_districts
    
    def optimize_district_order(self, city: str, selected_districts: List[str], start_location: Dict[str, float] = None) -> List[str]:
        """구역 방문 순서 최적화 (최단 경로)"""
        if len(selected_districts) <= 1:
            return selected_districts
        
        districts = self.get_districts_by_city(city)
        
        # 시작점 설정 (출발지 또는 첫 번째 구역)
        if start_location:
            current_location = start_location
        else:
            current_location = districts[selected_districts[0]]["center"]
        
        optimized_order = []
        remaining_districts = selected_districts.copy()
        
        # 가장 가까운 구역부터 방문 (Greedy Algorithm)
        while remaining_districts:
            min_distance = float('inf')
            next_district = None
            
            for district in remaining_districts:
                district_center = districts[district]["center"]
                distance = self.calculate_distance(current_location, district_center)
                
                if distance < min_distance:
                    min_distance = distance
                    next_district = district
            
            optimized_order.append(next_district)
            remaining_districts.remove(next_district)
            current_location = districts[next_district]["center"]
        
        return optimized_order
    
    def get_district_attractions(self, city: str, district: str, count: int = 3) -> List[Dict[str, Any]]:
        """구역별 추천 장소 조회"""
        districts = self.get_districts_by_city(city)
        district_info = districts.get(district, {})
        
        attractions = district_info.get("attractions", [])
        restaurants = district_info.get("restaurants", [])
        center = district_info.get("center", {"lat": 37.5665, "lng": 126.9780})
        
        places = []
        
        # 관광지 추가
        for i, attraction in enumerate(attractions[:count//2 + 1]):
            places.append({
                "name": attraction,
                "type": "attraction",
                "district": district,
                "lat": center["lat"] + (i * 0.005),  # 약간의 위치 변화
                "lng": center["lng"] + (i * 0.005),
                "characteristics": district_info.get("characteristics", [])
            })
        
        # 맛집 추가
        for i, restaurant in enumerate(restaurants[:count//2]):
            places.append({
                "name": restaurant,
                "type": "restaurant", 
                "district": district,
                "lat": center["lat"] - (i * 0.005),
                "lng": center["lng"] - (i * 0.005),
                "characteristics": district_info.get("characteristics", [])
            })
        
        return places[:count]
    
    def create_district_based_itinerary(self, city: str, travel_style: str, duration_hours: int, start_location: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """구역 기반 효율적 일정 생성"""
        
        # 1. 최적 구역 선택
        selected_districts = self.find_optimal_districts(city, travel_style, duration_hours)
        
        # 2. 구역 방문 순서 최적화
        optimized_districts = self.optimize_district_order(city, selected_districts, start_location)
        
        # 3. 각 구역별 장소 배정
        itinerary = []
        time_per_district = duration_hours // len(optimized_districts) if optimized_districts else duration_hours
        places_per_district = max(2, time_per_district // 2)
        
        current_time = 9  # 09:00 시작
        
        for district in optimized_districts:
            district_places = self.get_district_attractions(city, district, places_per_district)
            
            for place in district_places:
                itinerary.append({
                    "time": f"{int(current_time):02d}:00",
                    "place_name": place["name"],
                    "district": district,
                    "type": place["type"],
                    "lat": place["lat"],
                    "lng": place["lng"],
                    "duration": "90분" if place["type"] == "attraction" else "60분",
                    "characteristics": place["characteristics"]
                })
                
                # 시간 증가 (1.5시간씩)
                current_time += 1.5
                if current_time >= 24:
                    current_time = 9
        
        return itinerary
    
    def get_district_transport_info(self, city: str, district: str) -> Dict[str, Any]:
        """구역별 교통 정보"""
        districts = self.get_districts_by_city(city)
        district_info = districts.get(district, {})
        
        return {
            "main_stations": district_info.get("transport_hubs", []),
            "center": district_info.get("center", {}),
            "access_info": f"{district} 지역 주요 교통거점: {', '.join(district_info.get('transport_hubs', []))}"
        }