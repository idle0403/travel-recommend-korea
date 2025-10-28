"""
카카오맵 API 서비스

카카오맵 API를 사용하여 한국 내 정확한 경로 정보를 제공합니다.
무료 쿼터: 하루 30만건 (개인 프로젝트에 충분)
"""

import os
import httpx
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class KakaoMapsService:
    """카카오맵 API 서비스 클래스"""
    
    def __init__(self):
        self.rest_api_key = os.getenv('KAKAO_REST_API_KEY')
        self.base_url = "https://apis-navi.kakaomobility.com/v1/directions"
        
        if not self.rest_api_key:
            logger.warning("⚠️ 카카오맵 REST API 키가 설정되지 않았습니다.")
    
    async def get_directions(
        self, 
        origin: str, 
        destination: str, 
        mode: str = "transit"
    ) -> Dict[str, Any]:
        """
        경로 탐색
        
        Args:
            origin: 출발지 (좌표: "lat,lng")
            destination: 도착지 (좌표: "lat,lng")
            mode: 이동 수단 (transit=대중교통, walking=도보, driving=자동차)
        
        Returns:
            경로 정보 딕셔너리
        """
        
        if not self.rest_api_key:
            return {
                "success": False,
                "error": "카카오맵 API 키가 설정되지 않았습니다.",
                "detail": "KAKAO_REST_API_KEY 환경변수를 설정하세요."
            }
        
        try:
            # 좌표 변환
            origin_coords = self._parse_coords(origin)
            dest_coords = self._parse_coords(destination)
            
            if not origin_coords or not dest_coords:
                return {
                    "success": False,
                    "error": "좌표 변환 실패"
                }
            
            # 모드별 처리
            if mode == "walking":
                return await self._get_walking_route(origin_coords, dest_coords)
            elif mode == "transit":
                # 대중교통은 Google Maps 사용 권장
                return {
                    "success": False,
                    "error": "대중교통 경로는 Google Maps를 사용합니다.",
                    "fallback_to_google": True
                }
            else:  # driving (카카오 내비 API)
                return await self._get_driving_route(origin_coords, dest_coords)
                
        except Exception as e:
            logger.error(f"카카오맵 API 오류: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_coords(self, location: str) -> Optional[Dict[str, float]]:
        """
        좌표 문자열을 파싱
        
        Args:
            location: "lat,lng" 형식
        
        Returns:
            {"lat": float, "lng": float} 또는 None
        """
        if ',' in location:
            try:
                parts = location.split(',')
                lat = float(parts[0].strip())
                lng = float(parts[1].strip())
                return {"lat": lat, "lng": lng}
            except ValueError:
                return None
        return None
    
    async def _get_driving_route(
        self, 
        origin: Dict[str, float], 
        destination: Dict[str, float]
    ) -> Dict[str, Any]:
        """자동차 경로 조회 (카카오 내비 API)"""
        
        headers = {
            "Authorization": f"KakaoAK {self.rest_api_key}",
            "Content-Type": "application/json"
        }
        
        params = {
            "origin": f"{origin['lng']},{origin['lat']}",  # lng,lat 순서
            "destination": f"{destination['lng']},{destination['lat']}",
            "priority": "RECOMMEND",  # 추천 경로
            "car_fuel": "GASOLINE",
            "car_hipass": "false",
            "alternatives": "false",
            "road_details": "false"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    headers=headers,
                    params=params,
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    logger.error(f"카카오 API 오류: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"API 오류: {response.status_code}"
                    }
                
                data = response.json()
                
                # 경로가 없는 경우
                if not data.get('routes'):
                    return {
                        "success": False,
                        "error": "경로를 찾을 수 없습니다."
                    }
                
                # 첫 번째 경로 사용
                route = data['routes'][0]
                summary = route.get('summary', {})
                
                # 거리 및 시간
                distance_m = summary.get('distance', 0)
                duration_s = summary.get('duration', 0)
                
                return {
                    "success": True,
                    "mode": "driving",
                    "distance": f"{distance_m / 1000:.1f}km" if distance_m >= 1000 else f"{distance_m}m",
                    "duration": f"{duration_s // 60}분" if duration_s >= 60 else f"{duration_s}초",
                    "total_distance": distance_m,
                    "total_duration": duration_s * 1000,  # ms로 변환
                    "fare": summary.get('fare', {}).get('taxi', 0),
                    "steps": self._parse_sections(route.get('sections', [])),
                    "polyline": self._encode_path(route.get('sections', []))
                }
                
        except Exception as e:
            logger.error(f"카카오 내비 API 호출 실패: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"경로 조회 실패: {str(e)}"
            }
    
    async def _get_walking_route(
        self, 
        origin: Dict[str, float], 
        destination: Dict[str, float]
    ) -> Dict[str, Any]:
        """도보 경로 (간단한 계산)"""
        
        # 간단한 거리 계산 (Haversine)
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371000  # 지구 반지름 (미터)
        lat1, lng1 = radians(origin['lat']), radians(origin['lng'])
        lat2, lng2 = radians(destination['lat']), radians(destination['lng'])
        
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c
        
        # 도보 속도: 80m/분
        duration_minutes = int(distance / 80)
        
        return {
            "success": True,
            "mode": "walking",
            "distance": f"{distance:.0f}m" if distance < 1000 else f"{distance/1000:.1f}km",
            "duration": f"{duration_minutes}분" if duration_minutes > 0 else "1분 미만",
            "total_distance": int(distance),
            "total_duration": duration_minutes * 60000,
            "steps": [
                {
                    "instruction": "목적지까지 직진",
                    "distance": f"{distance:.0f}m",
                    "duration": f"{duration_minutes}분"
                }
            ]
        }
    
    def _parse_sections(self, sections: List[Dict]) -> List[Dict]:
        """경로 구간 파싱"""
        steps = []
        for section in sections:
            distance = section.get('distance', 0)
            duration = section.get('duration', 0)
            
            steps.append({
                "instruction": section.get('name', '직진'),
                "distance": f"{distance}m" if distance < 1000 else f"{distance/1000:.1f}km",
                "duration": f"{duration // 60}분" if duration >= 60 else f"{duration}초"
            })
        
        return steps if steps else [{"instruction": "경로를 따라 이동", "distance": "-", "duration": "-"}]
    
    def _encode_path(self, sections: List[Dict]) -> str:
        """경로를 간단한 문자열로 인코딩"""
        # sections의 좌표 추출 (상세 구현 가능)
        return ""


# 전역 인스턴스
kakao_maps_service = KakaoMapsService()

