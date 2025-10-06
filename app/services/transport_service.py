"""
대중교통 정보 서비스

실시간 버스/지하철 정보 및 최적 경로 제공
"""

import aiohttp
from typing import Dict, Any, List
from app.services.ssl_helper import create_http_session

class TransportService:
    def __init__(self):
        # 서울 열린데이터 광장 API (실제로는 API 키 필요)
        self.seoul_api_key = "sample_key"
        self.base_url = "http://ws.bus.go.kr/api/rest"
    
    async def get_subway_route(self, start_station: str, end_station: str) -> Dict[str, Any]:
        """지하철 경로 및 소요시간 조회"""
        # 서울 지하철 노선도 기반 경로 계산
        route_info = self._calculate_subway_route(start_station, end_station)
        
        return {
            "transport_type": "지하철",
            "route": route_info["route"],
            "duration": route_info["duration"],
            "transfers": route_info["transfers"],
            "fare": route_info["fare"],
            "first_train": "05:30",
            "last_train": "24:00",
            "steps": route_info["steps"]
        }
    
    async def get_bus_route(self, start_location: str, end_location: str) -> Dict[str, Any]:
        """버스 경로 및 실시간 정보 조회"""
        # 실제로는 서울시 버스 API 연동
        return {
            "transport_type": "버스",
            "route": f"{start_location} → {end_location}",
            "bus_numbers": ["143", "472", "N16"],
            "duration": "25분",
            "fare": "1,370원",
            "real_time_info": [
                {"bus_no": "143", "arrival_time": "3분 후", "remaining_seats": "여유"},
                {"bus_no": "472", "arrival_time": "7분 후", "remaining_seats": "보통"}
            ]
        }
    
    async def get_optimal_transport(self, origin: str, destination: str) -> Dict[str, Any]:
        """최적 대중교통 경로 추천"""
        # 지하철과 버스 경로 모두 조회하여 최적 경로 선택
        subway_route = await self.get_subway_route(origin, destination)
        bus_route = await self.get_bus_route(origin, destination)
        
        # 소요시간 기준으로 최적 경로 선택
        if self._parse_duration(subway_route["duration"]) <= self._parse_duration(bus_route["duration"]):
            recommended = subway_route
            alternative = bus_route
        else:
            recommended = bus_route
            alternative = subway_route
        
        return {
            "recommended": recommended,
            "alternative": alternative,
            "walking_distance": "도보 5분",
            "total_time": recommended["duration"]
        }
    
    def _calculate_subway_route(self, start: str, end: str) -> Dict[str, Any]:
        """지하철 경로 계산 (간단한 로직)"""
        # 실제로는 지하철 노선도 데이터베이스 필요
        subway_lines = {
            "1호선": ["서울역", "종각", "종로3가", "동대문", "청량리"],
            "2호선": ["강남", "역삼", "선릉", "삼성", "종합운동장", "잠실", "홍대입구", "신촌", "이대"],
            "3호선": ["경복궁", "안국", "종로3가", "을지로3가", "충무로", "동대입구", "약수", "금고개"],
            "4호선": ["명동", "회현", "서울역", "동대문", "혜화", "한성대입구"]
        }
        
        # 간단한 경로 찾기 (실제로는 더 복잡한 알고리즘 필요)
        for line_name, stations in subway_lines.items():
            if start in stations and end in stations:
                start_idx = stations.index(start)
                end_idx = stations.index(end)
                station_count = abs(end_idx - start_idx)
                
                return {
                    "route": f"{line_name} {start} → {end}",
                    "duration": f"{station_count * 2 + 5}분",
                    "transfers": 0,
                    "fare": "1,370원",
                    "steps": [
                        f"{start}역에서 {line_name} 승차",
                        f"{station_count}개 역 이동",
                        f"{end}역 하차"
                    ]
                }
        
        # 환승 필요한 경우 (간단한 예시)
        return {
            "route": f"{start} → {end} (환승 1회)",
            "duration": "35분",
            "transfers": 1,
            "fare": "1,370원",
            "steps": [
                f"{start}역 출발",
                "종로3가역에서 환승",
                f"{end}역 도착"
            ]
        }
    
    def _parse_duration(self, duration_str: str) -> int:
        """소요시간 문자열을 분 단위 숫자로 변환"""
        import re
        match = re.search(r'(\d+)', duration_str)
        return int(match.group(1)) if match else 30