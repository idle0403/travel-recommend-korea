"""
도시 정보 서비스

전국 도시별 좌표, 특색, 추천 장소 정보 관리
"""

from typing import Dict, Any, List

class CityService:
    def __init__(self):
        self.cities = {
            # 특별시
            "Seoul": {
                "name": "서울특별시",
                "type": "특별시",
                "lat": 37.5665,
                "lng": 126.9780,
                "weather_code": "Seoul,KR",
                "specialties": ["궁궐", "한강", "쇼핑", "카페", "야경"],
                "famous_places": ["경복궁", "명동", "홍대", "강남", "한강공원"],
                "transport_hub": ["서울역", "강남역", "홍대입구역"]
            },
            
            # 광역시
            "Busan": {
                "name": "부산광역시",
                "type": "광역시",
                "lat": 35.1796,
                "lng": 129.0756,
                "weather_code": "Busan,KR",
                "specialties": ["해변", "해산물", "온천", "영화제", "야경"],
                "famous_places": ["해운대", "광안리", "감천문화마을", "자갈치시장", "태종대"],
                "transport_hub": ["부산역", "서면역", "해운대역"]
            },
            "Daegu": {
                "name": "대구광역시",
                "type": "광역시",
                "lat": 35.8714,
                "lng": 128.6014,
                "weather_code": "Daegu,KR",
                "specialties": ["약령시", "섬유", "치킨", "근대골목", "팔공산"],
                "famous_places": ["동성로", "서문시장", "팔공산", "앞산공원", "김광석거리"],
                "transport_hub": ["동대구역", "중앙로역", "반월당역"]
            },
            "Incheon": {
                "name": "인천광역시",
                "type": "광역시",
                "lat": 37.4563,
                "lng": 126.7052,
                "weather_code": "Incheon,KR",
                "specialties": ["차이나타운", "공항", "항구", "섬", "해산물"],
                "famous_places": ["차이나타운", "월미도", "송도센트럴파크", "인천대교", "강화도"],
                "transport_hub": ["인천역", "부평역", "송도역"]
            },
            "Gwangju": {
                "name": "광주광역시",
                "type": "광역시",
                "lat": 35.1595,
                "lng": 126.8526,
                "weather_code": "Gwangju,KR",
                "specialties": ["예술", "비엔날레", "한정식", "무등산", "민주화"],
                "famous_places": ["무등산", "국립아시아문화전당", "충장로", "양림동", "518기념공원"],
                "transport_hub": ["광주송정역", "상무역", "금남로4가역"]
            },
            "Daejeon": {
                "name": "대전광역시",
                "type": "광역시",
                "lat": 36.3504,
                "lng": 127.3845,
                "weather_code": "Daejeon,KR",
                "specialties": ["과학", "온천", "엑스포", "대학", "연구소"],
                "famous_places": ["엑스포과학공원", "유성온천", "한밭수목원", "계룡산", "대청호"],
                "transport_hub": ["대전역", "서대전역", "유성온천역"]
            },
            "Ulsan": {
                "name": "울산광역시",
                "type": "광역시",
                "lat": 35.5384,
                "lng": 129.3114,
                "weather_code": "Ulsan,KR",
                "specialties": ["공업", "고래", "간절곶", "태화강", "석유화학"],
                "famous_places": ["간절곶", "태화강국가정원", "장생포고래박물관", "울기등대", "대왕암공원"],
                "transport_hub": ["울산역", "태화강역", "신울산역"]
            },
            
            # 특별자치도
            "Jeju": {
                "name": "제주특별자치도",
                "type": "특별자치도",
                "lat": 33.4996,
                "lng": 126.5312,
                "weather_code": "Jeju,KR",
                "specialties": ["한라산", "해변", "감귤", "돌하루방", "해녀"],
                "famous_places": ["한라산", "성산일출봉", "우도", "협재해수욕장", "천지연폭포"],
                "transport_hub": ["제주공항", "제주시청", "서귀포시청"]
            },
            
            # 경기도
            "Suwon": {
                "name": "수원시",
                "type": "경기도",
                "lat": 37.2636,
                "lng": 127.0286,
                "weather_code": "Suwon,KR",
                "specialties": ["화성", "갈비", "삼성", "월드컵경기장", "전통"],
                "famous_places": ["수원화성", "화성행궁", "수원월드컵경기장", "행리단길", "광교호수공원"],
                "transport_hub": ["수원역", "성균관대역", "광교중앙역"]
            },
            
            # 강원도
            "Chuncheon": {
                "name": "춘천시",
                "type": "강원도",
                "lat": 37.8813,
                "lng": 127.7298,
                "weather_code": "Chuncheon,KR",
                "specialties": ["닭갈비", "호수", "막국수", "소양강", "레일바이크"],
                "famous_places": ["남이섬", "소양강댐", "춘천호", "김유정문학촌", "강촌레일파크"],
                "transport_hub": ["춘천역", "남춘천역", "강촌역"]
            },
            "Gangneung": {
                "name": "강릉시",
                "type": "강원도",
                "lat": 37.7519,
                "lng": 128.8761,
                "weather_code": "Gangneung,KR",
                "specialties": ["커피", "해변", "올림픽", "바다", "선교장"],
                "famous_places": ["경포해변", "안목해변", "오죽헌", "선교장", "강릉커피거리"],
                "transport_hub": ["강릉역", "정동진역", "경포대역"]
            },
            
            # 전라북도
            "Jeonju": {
                "name": "전주시",
                "type": "전라북도",
                "lat": 35.8242,
                "lng": 127.1480,
                "weather_code": "Jeonju,KR",
                "specialties": ["한옥마을", "비빔밥", "한정식", "전통문화", "막걸리"],
                "famous_places": ["전주한옥마을", "경기전", "오목대", "덕진공원", "전주향교"],
                "transport_hub": ["전주역", "전주고속버스터미널", "덕진역"]
            },
            
            # 전라남도
            "Yeosu": {
                "name": "여수시",
                "type": "전라남도",
                "lat": 34.7604,
                "lng": 127.6622,
                "weather_code": "Yeosu,KR",
                "specialties": ["엑스포", "야경", "해산물", "케이블카", "섬"],
                "famous_places": ["여수엑스포", "오동도", "향일암", "여수해상케이블카", "돌산대교"],
                "transport_hub": ["여수엑스포역", "여수역", "여수공항"]
            },
            
            # 경상북도
            "Gyeongju": {
                "name": "경주시",
                "type": "경상북도",
                "lat": 35.8562,
                "lng": 129.2247,
                "weather_code": "Gyeongju,KR",
                "specialties": ["신라", "불국사", "석굴암", "첨성대", "역사"],
                "famous_places": ["불국사", "석굴암", "첨성대", "안압지", "대릉원"],
                "transport_hub": ["경주역", "신경주역", "불국사역"]
            },
            "Andong": {
                "name": "안동시",
                "type": "경상북도",
                "lat": 36.5684,
                "lng": 128.7294,
                "weather_code": "Andong,KR",
                "specialties": ["하회마을", "간고등어", "유교", "탈춤", "전통"],
                "famous_places": ["하회마을", "도산서원", "안동댐", "월영교", "봉정사"],
                "transport_hub": ["안동역", "안동터미널", "하회마을"]
            }
        }
    
    def get_city_info(self, city_code: str) -> Dict[str, Any]:
        """도시 정보 조회"""
        return self.cities.get(city_code, self.cities["Seoul"])
    
    def get_all_cities(self) -> Dict[str, Dict[str, Any]]:
        """전체 도시 목록 조회"""
        return self.cities
    
    def get_cities_by_type(self, city_type: str) -> List[Dict[str, Any]]:
        """도시 유형별 조회"""
        return [
            {"code": code, **info} 
            for code, info in self.cities.items() 
            if info["type"] == city_type
        ]
    
    def get_nearby_cities(self, city_code: str, radius_km: float = 100) -> List[str]:
        """인근 도시 조회 (간단한 거리 계산)"""
        if city_code not in self.cities:
            return []
        
        base_city = self.cities[city_code]
        nearby = []
        
        for code, city in self.cities.items():
            if code == city_code:
                continue
            
            # 간단한 거리 계산 (실제로는 더 정확한 계산 필요)
            lat_diff = abs(base_city["lat"] - city["lat"])
            lng_diff = abs(base_city["lng"] - city["lng"])
            
            # 대략적인 거리 (1도 ≈ 111km)
            distance = ((lat_diff ** 2 + lng_diff ** 2) ** 0.5) * 111
            
            if distance <= radius_km:
                nearby.append(code)
        
        return nearby
    
    def get_city_specialties(self, city_code: str) -> List[str]:
        """도시별 특색 조회"""
        city_info = self.get_city_info(city_code)
        return city_info.get("specialties", [])
    
    def get_weather_code(self, city_code: str) -> str:
        """날씨 API용 도시 코드 조회"""
        city_info = self.get_city_info(city_code)
        return city_info.get("weather_code", "Seoul,KR")