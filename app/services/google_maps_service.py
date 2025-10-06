"""
Google Maps API 서비스

경로 최적화, 대중교통 정보, 거리/시간 계산
"""

import os
import aiohttp
from typing import Dict, Any, List, Tuple
from app.services.ssl_helper import create_http_session

class GoogleMapsService:
    BASE_URL = "https://maps.googleapis.com/maps/api"
    DEFAULT_TIMEOUT = 10
    MAX_WAYPOINTS = 23  # Google Maps API limit
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    
    async def get_optimized_route(self, locations: List[Dict[str, Any]], mode: str = "transit") -> Dict[str, Any]:
        """여행지 목록으로 최적 경로 생성"""
        if len(locations) < 2:
            return {"error": "최소 2개 이상의 장소가 필요합니다"}
        
        if not self.api_key:
            return self._mock_optimized_route(locations)
        
        # 첫 번째와 마지막 장소를 출발지/도착지로 설정
        origin = f"{locations[0]['lat']},{locations[0]['lng']}"
        destination = f"{locations[-1]['lat']},{locations[-1]['lng']}"
        
        # 중간 지점들을 waypoints로 설정
        waypoints = []
        if len(locations) > 2:
            waypoints = [f"{loc['lat']},{loc['lng']}" for loc in locations[1:-1]]
        
        params = {
            "origin": origin,
            "destination": destination,
            "mode": mode,
            "key": self.api_key,
            "language": "ko",
            "region": "kr",
            "optimize": "true"  # 경로 최적화
        }
        
        if waypoints:
            params["waypoints"] = "optimize:true|" + "|".join(waypoints)
        
        try:
            async with create_http_session() as session:
                async with session.get(f"{self.BASE_URL}/directions/json", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_optimized_route(data, locations)
                    else:
                        return self._mock_optimized_route(locations)
        except Exception as e:
            print(f"Google Maps 최적 경로 조회 오류: {str(e)}")
            return self._mock_optimized_route(locations)
    
    async def get_directions(self, origin: str, destination: str, waypoints: List[str] = None, mode: str = "transit") -> Dict[str, Any]:
        """경로 및 대중교통 정보 조회"""
        if not self.api_key:
            return self._mock_directions_result(origin, destination)
        
        params = {
            "origin": origin,
            "destination": destination,
            "mode": mode,  # transit, driving, walking
            "key": self.api_key,
            "language": "ko",
            "region": "kr"
        }
        
        if waypoints:
            params["waypoints"] = "|".join(waypoints)
            params["optimize"] = "true"  # 경로 최적화
        
        try:
            async with create_http_session() as session:
                async with session.get(f"{self.BASE_URL}/directions/json", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_directions_result(data)
                    else:
                        return self._mock_directions_result(origin, destination)
        except Exception as e:
            print(f"Google Maps 경로 조회 오류: {str(e)}")
            return self._mock_directions_result(origin, destination)
    
    async def get_place_details(self, place_name: str, location: str = "Seoul, Korea") -> Dict[str, Any]:
        """장소 상세 정보 조회"""
        if not self.api_key:
            return self._mock_place_details(place_name)
        
        # 1단계: Place Search로 place_id 찾기
        search_params = {
            "query": f"{place_name} {location}",
            "key": self.api_key,
            "language": "ko",
            "region": "kr"
        }
        
        try:
            async with create_http_session() as session:
                # Place Search
                async with session.get(f"{self.BASE_URL}/place/textsearch/json", params=search_params) as response:
                    if response.status == 200:
                        search_data = await response.json()
                        if search_data.get("results"):
                            place_id = search_data["results"][0]["place_id"]
                            
                            # 2단계: Place Details로 상세 정보 조회
                            details_params = {
                                "place_id": place_id,
                                "fields": "name,formatted_address,geometry,rating,reviews,opening_hours,formatted_phone_number,website,price_level",
                                "key": self.api_key,
                                "language": "ko"
                            }
                            
                            async with session.get(f"{self.BASE_URL}/place/details/json", params=details_params) as details_response:
                                if details_response.status == 200:
                                    details_data = await details_response.json()
                                    return self._process_place_details(details_data.get("result", {}))
                
                return self._mock_place_details(place_name)
        except Exception as e:
            print(f"Google Places 조회 오류: {str(e)}")
            return self._mock_place_details(place_name)
    
    async def calculate_travel_time(self, origins: List[str], destinations: List[str], mode: str = "transit") -> Dict[str, Any]:
        """여러 지점 간 이동시간 계산"""
        if not self.api_key:
            return self._mock_travel_time_result()
        
        params = {
            "origins": "|".join(origins),
            "destinations": "|".join(destinations),
            "mode": mode,
            "key": self.api_key,
            "language": "ko",
            "region": "kr"
        }
        
        try:
            async with create_http_session() as session:
                async with session.get(f"{self.BASE_URL}/distancematrix/json", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_travel_time_result(data)
                    else:
                        return self._mock_travel_time_result()
        except Exception as e:
            print(f"Google Distance Matrix 오류: {str(e)}")
            return self._mock_travel_time_result()
    
    def _process_directions_result(self, data: Dict) -> Dict[str, Any]:
        """경로 결과 처리"""
        if data.get("status") != "OK" or not data.get("routes"):
            return {"error": "경로를 찾을 수 없습니다"}
        
        route = data["routes"][0]
        leg = route["legs"][0]
        
        # 대중교통 단계별 정보 추출
        steps = []
        for step in leg.get("steps", []):
            step_info = {
                "instruction": step.get("html_instructions", ""),
                "distance": step.get("distance", {}).get("text", ""),
                "duration": step.get("duration", {}).get("text", ""),
                "travel_mode": step.get("travel_mode", "")
            }
            
            # 대중교통 상세 정보
            if step.get("transit_details"):
                transit = step["transit_details"]
                step_info.update({
                    "transit_line": transit.get("line", {}).get("name", ""),
                    "departure_stop": transit.get("departure_stop", {}).get("name", ""),
                    "arrival_stop": transit.get("arrival_stop", {}).get("name", ""),
                    "num_stops": transit.get("num_stops", 0)
                })
            
            steps.append(step_info)
        
        return {
            "total_distance": leg.get("distance", {}).get("text", ""),
            "total_duration": leg.get("duration", {}).get("text", ""),
            "steps": steps,
            "polyline": route.get("overview_polyline", {}).get("points", ""),
            "bounds": route.get("bounds", {})
        }
    
    def _process_optimized_route(self, data: Dict, locations: List[Dict]) -> Dict[str, Any]:
        """최적화된 경로 결과 처리"""
        if data.get("status") != "OK" or not data.get("routes"):
            return {"error": "경로를 찾을 수 없습니다"}
        
        route = data["routes"][0]
        legs = route.get("legs", [])
        
        # 전체 경로 정보
        total_distance = sum([leg.get("distance", {}).get("value", 0) for leg in legs])
        total_duration = sum([leg.get("duration", {}).get("value", 0) for leg in legs])
        
        # 각 구간별 정보
        route_segments = []
        for i, leg in enumerate(legs):
            segment = {
                "from": locations[i]["name"] if i < len(locations) else "출발지",
                "to": locations[i + 1]["name"] if i + 1 < len(locations) else "도착지",
                "distance": leg.get("distance", {}).get("text", ""),
                "duration": leg.get("duration", {}).get("text", ""),
                "steps": []
            }
            
            # 각 구간의 상세 단계
            for step in leg.get("steps", []):
                step_info = {
                    "instruction": step.get("html_instructions", ""),
                    "distance": step.get("distance", {}).get("text", ""),
                    "duration": step.get("duration", {}).get("text", ""),
                    "travel_mode": step.get("travel_mode", "")
                }
                
                # 대중교통 정보
                if step.get("transit_details"):
                    transit = step["transit_details"]
                    step_info.update({
                        "transit_line": transit.get("line", {}).get("name", ""),
                        "departure_stop": transit.get("departure_stop", {}).get("name", ""),
                        "arrival_stop": transit.get("arrival_stop", {}).get("name", ""),
                        "num_stops": transit.get("num_stops", 0)
                    })
                
                segment["steps"].append(step_info)
            
            route_segments.append(segment)
        
        # 최적화된 순서 (waypoint_order가 있는 경우)
        optimized_order = route.get("waypoint_order", [])
        
        return {
            "total_distance": f"{total_distance / 1000:.1f}km",
            "total_duration": f"{total_duration // 60}분",
            "polyline": route.get("overview_polyline", {}).get("points", ""),
            "bounds": route.get("bounds", {}),
            "route_segments": route_segments,
            "optimized_order": optimized_order,
            "waypoint_order": optimized_order
        }
    
    def _process_place_details(self, result: Dict) -> Dict[str, Any]:
        """장소 상세 정보 처리"""
        geometry = result.get("geometry", {}).get("location", {})
        
        return {
            "name": result.get("name", ""),
            "address": result.get("formatted_address", ""),
            "lat": geometry.get("lat", 0),
            "lng": geometry.get("lng", 0),
            "rating": result.get("rating", 0),
            "phone": result.get("formatted_phone_number", ""),
            "website": result.get("website", ""),
            "price_level": result.get("price_level", 0),
            "opening_hours": result.get("opening_hours", {}).get("weekday_text", []),
            "reviews": [
                {
                    "author": review.get("author_name", ""),
                    "rating": review.get("rating", 0),
                    "text": review.get("text", "")[:200] + "..." if len(review.get("text", "")) > 200 else review.get("text", "")
                }
                for review in result.get("reviews", [])[:3]  # 상위 3개 리뷰만
            ]
        }
    
    def _process_travel_time_result(self, data: Dict) -> Dict[str, Any]:
        """이동시간 결과 처리"""
        if data.get("status") != "OK":
            return {"error": "이동시간을 계산할 수 없습니다"}
        
        results = []
        for i, row in enumerate(data.get("rows", [])):
            for j, element in enumerate(row.get("elements", [])):
                if element.get("status") == "OK":
                    results.append({
                        "origin_index": i,
                        "destination_index": j,
                        "distance": element.get("distance", {}).get("text", ""),
                        "duration": element.get("duration", {}).get("text", ""),
                        "duration_value": element.get("duration", {}).get("value", 0)  # 초 단위
                    })
        
        return {"results": results}
    
    def _mock_optimized_route(self, locations: List[Dict]) -> Dict[str, Any]:
        """모의 최적 경로 결과"""
        return {
            "total_distance": "8.5km",
            "total_duration": "45분",
            "polyline": "sample_encoded_polyline_string",
            "bounds": {
                "northeast": {"lat": 37.5665, "lng": 126.9780},
                "southwest": {"lat": 37.5565, "lng": 126.9680}
            },
            "route_segments": [
                {
                    "from": locations[0]["name"] if locations else "출발지",
                    "to": locations[1]["name"] if len(locations) > 1 else "도착지",
                    "distance": "2.1km",
                    "duration": "12분",
                    "steps": [
                        {
                            "instruction": "지하철 2호선 이용",
                            "distance": "2.1km",
                            "duration": "12분",
                            "travel_mode": "TRANSIT",
                            "transit_line": "지하철 2호선",
                            "departure_stop": "출발역",
                            "arrival_stop": "도착역",
                            "num_stops": 3
                        }
                    ]
                }
            ],
            "optimized_order": [],
            "waypoint_order": []
        }
    
    def _mock_directions_result(self, origin: str, destination: str) -> Dict[str, Any]:
        """모의 경로 결과"""
        return {
            "total_distance": "5.2km",
            "total_duration": "25분",
            "polyline": "sample_encoded_polyline_string",
            "bounds": {
                "northeast": {"lat": 37.5665, "lng": 126.9780},
                "southwest": {"lat": 37.5565, "lng": 126.9680}
            },
            "steps": [
                {
                    "instruction": f"{origin}에서 지하철역까지 도보",
                    "distance": "300m",
                    "duration": "4분",
                    "travel_mode": "WALKING"
                },
                {
                    "instruction": "지하철 2호선 이용",
                    "distance": "4.5km",
                    "duration": "18분",
                    "travel_mode": "TRANSIT",
                    "transit_line": "지하철 2호선",
                    "departure_stop": "출발역",
                    "arrival_stop": "도착역",
                    "num_stops": 6
                },
                {
                    "instruction": f"지하철역에서 {destination}까지 도보",
                    "distance": "400m",
                    "duration": "3분",
                    "travel_mode": "WALKING"
                }
            ]
        }
    
    def _mock_place_details(self, place_name: str) -> Dict[str, Any]:
        """모의 장소 상세 정보"""
        return {
            "name": place_name,
            "address": "서울시 강남구 테헤란로 123",
            "lat": 37.5665,
            "lng": 126.9780,
            "rating": 4.3,
            "phone": "02-1234-5678",
            "website": "https://example.com",
            "price_level": 2,
            "opening_hours": self._get_default_hours(),
            "reviews": self._get_mock_reviews()
        }
    
    def _get_default_hours(self) -> List[str]:
        return ["월요일: 09:00~21:00", "화요일: 09:00~21:00"]
    
    def _get_mock_reviews(self) -> List[Dict[str, Any]]:
        return [
            {
                "author": "김철수",
                "rating": 5,
                "text": "정말 좋은 곳이에요. 음식도 맛있고 서비스도 친절합니다."
            }
        ]
    
    def _mock_travel_time_result(self) -> Dict[str, Any]:
        """모의 이동시간 결과"""
        return {
            "results": [
                {
                    "origin_index": 0,
                    "destination_index": 0,
                    "distance": "2.5km",
                    "duration": "15분",
                    "duration_value": 900
                }
            ]
        }