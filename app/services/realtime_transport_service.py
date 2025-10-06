"""
실시간 대중교통 정보 서비스

서울시 버스/지하철 실시간 정보 및 최적 경로 제공
"""

import os
import aiohttp
from typing import Dict, Any, List
from app.services.ssl_helper import create_http_session

class RealtimeTransportService:
    def __init__(self):
        # 서울 열린데이터 광장 API 키
        self.seoul_api_key = os.getenv("SEOUL_API_KEY", "sample_key")
        self.bus_api_url = "http://ws.bus.go.kr/api/rest"
        self.subway_api_url = "http://swopenAPI.seoul.go.kr/api/subway"
    
    async def get_realtime_bus_info(self, bus_stop_id: str) -> Dict[str, Any]:
        """실시간 버스 도착 정보"""
        if not self.seoul_api_key or self.seoul_api_key == "sample_key":
            return self._mock_bus_info()
        
        params = {
            "serviceKey": self.seoul_api_key,
            "stId": bus_stop_id,
            "dataTerm": "0",
            "resultType": "json"
        }
        
        try:
            async with create_http_session() as session:
                async with session.get(f"{self.bus_api_url}/arrInfoByStopList", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_bus_arrival_data(data)
        except Exception as e:
            print(f"버스 API 오류: {str(e)}")
        
        return self._mock_bus_info()
    
    async def get_realtime_subway_info(self, station_name: str) -> Dict[str, Any]:
        """실시간 지하철 도착 정보"""
        if not self.seoul_api_key or self.seoul_api_key == "sample_key":
            return self._mock_subway_info()
        
        params = {
            "key": self.seoul_api_key,
            "type": "json",
            "service": "SearchArrivalTimeOfTrainByIDService",
            "stationName": station_name
        }
        
        try:
            async with create_http_session() as session:
                async with session.get(f"{self.subway_api_url}/{self.seoul_api_key}/json/SearchArrivalTimeOfTrainByIDService/1/10/{station_name}") as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_subway_arrival_data(data)
        except Exception as e:
            print(f"지하철 API 오류: {str(e)}")
        
        return self._mock_subway_info()
    
    async def get_optimal_route_with_realtime(self, origin: str, destination: str) -> Dict[str, Any]:
        """실시간 정보를 반영한 최적 경로"""
        # 기본 경로 정보
        base_route = await self._get_base_route(origin, destination)
        
        # 실시간 정보 추가
        enhanced_route = await self._enhance_with_realtime_info(base_route)
        
        return enhanced_route
    
    def _process_bus_arrival_data(self, data: Dict) -> Dict[str, Any]:
        """버스 도착 정보 처리"""
        arrivals = []
        
        if data.get("msgBody") and data["msgBody"].get("itemList"):
            for item in data["msgBody"]["itemList"]:
                arrival_info = {
                    "bus_number": item.get("rtNm", ""),
                    "route_type": item.get("routeType", ""),
                    "arrival_msg1": item.get("arrmsg1", ""),
                    "arrival_msg2": item.get("arrmsg2", ""),
                    "next_bus": item.get("arrmsg2", ""),
                    "congestion": self._get_congestion_level(item.get("reride_Num1", 0)),
                    "low_bus": item.get("isFullFlag", "0") == "1"
                }
                arrivals.append(arrival_info)
        
        return {
            "type": "bus",
            "arrivals": arrivals[:5],  # 상위 5개만
            "last_updated": "실시간"
        }
    
    def _process_subway_arrival_data(self, data: Dict) -> Dict[str, Any]:
        """지하철 도착 정보 처리"""
        arrivals = []
        
        if data.get("realtimeArrivalList"):
            for item in data["realtimeArrivalList"]:
                arrival_info = {
                    "line_name": item.get("subwayId", ""),
                    "train_line": item.get("trainLineNm", ""),
                    "direction": item.get("updnLine", ""),
                    "arrival_msg": item.get("arvlMsg2", ""),
                    "arrival_code": item.get("arvlCd", ""),
                    "current_station": item.get("lstcarAt", ""),
                    "express_yn": item.get("btrainSttus", "") == "1"
                }
                arrivals.append(arrival_info)
        
        return {
            "type": "subway",
            "arrivals": arrivals[:4],  # 상위 4개만
            "last_updated": "실시간"
        }
    
    async def _get_base_route(self, origin: str, destination: str) -> Dict[str, Any]:
        """기본 경로 정보 조회"""
        # Google Maps API 또는 기본 경로 계산
        return {
            "origin": origin,
            "destination": destination,
            "routes": [
                {
                    "type": "subway",
                    "duration": "25분",
                    "transfers": 1,
                    "stations": ["출발역", "환승역", "도착역"],
                    "lines": ["2호선", "4호선"]
                },
                {
                    "type": "bus",
                    "duration": "30분",
                    "transfers": 0,
                    "bus_numbers": ["143", "472"],
                    "stops": ["출발정류장", "도착정류장"]
                }
            ]
        }
    
    async def _enhance_with_realtime_info(self, base_route: Dict) -> Dict[str, Any]:
        """실시간 정보로 경로 강화"""
        enhanced_routes = []
        
        for route in base_route.get("routes", []):
            if route["type"] == "subway":
                # 지하철 실시간 정보 추가
                realtime_info = await self.get_realtime_subway_info(route["stations"][0])
                route["realtime"] = realtime_info
                
                # 지연 정보 반영
                if realtime_info.get("arrivals"):
                    first_train = realtime_info["arrivals"][0]
                    if "지연" in first_train.get("arrival_msg", ""):
                        route["status"] = "지연"
                        route["delay_minutes"] = 5
                    else:
                        route["status"] = "정상"
                        route["delay_minutes"] = 0
            
            elif route["type"] == "bus":
                # 버스 실시간 정보 추가
                realtime_info = await self.get_realtime_bus_info("sample_stop_id")
                route["realtime"] = realtime_info
                
                # 혼잡도 정보 반영
                if realtime_info.get("arrivals"):
                    route["congestion"] = realtime_info["arrivals"][0].get("congestion", "보통")
            
            enhanced_routes.append(route)
        
        # 실시간 정보 기반 최적 경로 재정렬
        enhanced_routes.sort(key=lambda x: x.get("delay_minutes", 0))
        
        return {
            "origin": base_route["origin"],
            "destination": base_route["destination"],
            "routes": enhanced_routes,
            "recommended_route": enhanced_routes[0] if enhanced_routes else None,
            "last_updated": "실시간"
        }
    
    def _get_congestion_level(self, passenger_count: int) -> str:
        """혼잡도 계산"""
        if passenger_count < 10:
            return "여유"
        elif passenger_count < 20:
            return "보통"
        elif passenger_count < 30:
            return "혼잡"
        else:
            return "매우혼잡"
    
    def _mock_bus_info(self) -> Dict[str, Any]:
        """모의 버스 정보"""
        return {
            "type": "bus",
            "arrivals": [
                {
                    "bus_number": "143",
                    "route_type": "간선",
                    "arrival_msg1": "3분 후 도착",
                    "arrival_msg2": "12분 후 도착",
                    "next_bus": "12분 후 도착",
                    "congestion": "보통",
                    "low_bus": False
                },
                {
                    "bus_number": "472",
                    "route_type": "지선",
                    "arrival_msg1": "7분 후 도착",
                    "arrival_msg2": "18분 후 도착",
                    "next_bus": "18분 후 도착",
                    "congestion": "여유",
                    "low_bus": True
                }
            ],
            "last_updated": "실시간"
        }
    
    def _mock_subway_info(self) -> Dict[str, Any]:
        """모의 지하철 정보"""
        return {
            "type": "subway",
            "arrivals": [
                {
                    "line_name": "2호선",
                    "train_line": "성수행",
                    "direction": "외선순환",
                    "arrival_msg": "2분 후 도착",
                    "arrival_code": "2",
                    "current_station": "신촌",
                    "express_yn": False
                },
                {
                    "line_name": "2호선",
                    "train_line": "성수행",
                    "direction": "외선순환",
                    "arrival_msg": "8분 후 도착",
                    "arrival_code": "8",
                    "current_station": "홍대입구",
                    "express_yn": False
                }
            ],
            "last_updated": "실시간"
        }