"""
경로 최적화 서비스

구역별 클러스터링과 TSP 알고리즘을 활용한 최적 동선 구성
"""

from typing import Dict, Any, List, Tuple
import math
from app.services.district_service import DistrictService

class RouteOptimizerService:
    def __init__(self):
        self.district_service = DistrictService()
    
    def optimize_travel_route(self, places: List[Dict[str, Any]], city: str, start_location: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """여행지 최적 경로 구성"""
        
        if len(places) <= 2:
            return places
        
        # 1. 구역별 클러스터링
        clustered_places = self._cluster_by_district(places, city)
        
        # 2. 구역 간 최적 순서 결정
        optimized_clusters = self._optimize_cluster_order(clustered_places, city, start_location)
        
        # 3. 각 구역 내 최적 순서 결정
        final_route = []
        for cluster in optimized_clusters:
            optimized_cluster = self._optimize_within_cluster(cluster["places"])
            final_route.extend(optimized_cluster)
        
        return final_route
    
    def _cluster_by_district(self, places: List[Dict[str, Any]], city: str) -> List[Dict[str, Any]]:
        """장소들을 구역별로 클러스터링"""
        districts = self.district_service.get_districts_by_city(city)
        clusters = {}
        
        for place in places:
            place_coords = {"lat": place.get("lat", 37.5665), "lng": place.get("lng", 126.9780)}
            
            # 가장 가까운 구역 찾기
            closest_district = None
            min_distance = float('inf')
            
            for district_name, district_info in districts.items():
                district_center = district_info["center"]
                distance = self.district_service.calculate_distance(place_coords, district_center)
                
                if distance < min_distance:
                    min_distance = distance
                    closest_district = district_name
            
            # 클러스터에 추가
            if closest_district:
                if closest_district not in clusters:
                    clusters[closest_district] = {
                        "district": closest_district,
                        "center": districts[closest_district]["center"],
                        "places": []
                    }
                clusters[closest_district]["places"].append(place)
        
        return list(clusters.values())
    
    def _optimize_cluster_order(self, clusters: List[Dict[str, Any]], city: str, start_location: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """구역 간 방문 순서 최적화"""
        if len(clusters) <= 1:
            return clusters
        
        # 시작점 설정
        if start_location:
            current_location = start_location
        else:
            current_location = clusters[0]["center"]
        
        optimized_order = []
        remaining_clusters = clusters.copy()
        
        # 가장 가까운 구역부터 방문
        while remaining_clusters:
            min_distance = float('inf')
            next_cluster = None
            
            for cluster in remaining_clusters:
                distance = self.district_service.calculate_distance(current_location, cluster["center"])
                
                if distance < min_distance:
                    min_distance = distance
                    next_cluster = cluster
            
            optimized_order.append(next_cluster)
            remaining_clusters.remove(next_cluster)
            current_location = next_cluster["center"]
        
        return optimized_order
    
    def _optimize_within_cluster(self, places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """구역 내 장소들의 방문 순서 최적화"""
        if len(places) <= 2:
            return places
        
        # 간단한 TSP 해결 (Nearest Neighbor)
        optimized_places = []
        remaining_places = places.copy()
        
        # 첫 번째 장소 선택 (가장 북쪽 또는 서쪽)
        first_place = min(remaining_places, key=lambda p: (p.get("lat", 0), p.get("lng", 0)))
        optimized_places.append(first_place)
        remaining_places.remove(first_place)
        
        current_location = {"lat": first_place.get("lat", 37.5665), "lng": first_place.get("lng", 126.9780)}
        
        # 가장 가까운 장소부터 방문
        while remaining_places:
            min_distance = float('inf')
            next_place = None
            
            for place in remaining_places:
                place_coords = {"lat": place.get("lat", 37.5665), "lng": place.get("lng", 126.9780)}
                distance = self.district_service.calculate_distance(current_location, place_coords)
                
                if distance < min_distance:
                    min_distance = distance
                    next_place = place
            
            optimized_places.append(next_place)
            remaining_places.remove(next_place)
            current_location = {"lat": next_place.get("lat", 37.5665), "lng": next_place.get("lng", 126.9780)}
        
        return optimized_places
    
    def calculate_total_travel_time(self, places: List[Dict[str, Any]]) -> Dict[str, Any]:
        """전체 이동시간 및 거리 계산"""
        if len(places) < 2:
            return {"total_distance": 0, "total_time": 0, "segments": []}
        
        total_distance = 0
        total_time = 0
        segments = []
        
        for i in range(len(places) - 1):
            current = {"lat": places[i].get("lat", 37.5665), "lng": places[i].get("lng", 126.9780)}
            next_place = {"lat": places[i+1].get("lat", 37.5665), "lng": places[i+1].get("lng", 126.9780)}
            
            distance = self.district_service.calculate_distance(current, next_place)
            time = self._estimate_travel_time(distance)
            
            total_distance += distance
            total_time += time
            
            segments.append({
                "from": places[i].get("place_name", ""),
                "to": places[i+1].get("place_name", ""),
                "distance": f"{distance:.1f}km",
                "time": f"{time:.0f}분",
                "transport_method": self._recommend_transport_method(distance)
            })
        
        return {
            "total_distance": f"{total_distance:.1f}km",
            "total_time": f"{total_time:.0f}분",
            "segments": segments
        }
    
    def _estimate_travel_time(self, distance_km: float) -> float:
        """거리 기반 이동시간 추정 (분)"""
        if distance_km < 0.5:  # 500m 미만
            return distance_km * 12  # 도보 5km/h
        elif distance_km < 2:  # 2km 미만
            return 5 + distance_km * 8  # 대중교통 준비시간 + 이동
        else:  # 2km 이상
            return 10 + distance_km * 6  # 대중교통
    
    def _recommend_transport_method(self, distance_km: float) -> str:
        """거리별 추천 교통수단"""
        if distance_km < 0.5:
            return "도보"
        elif distance_km < 2:
            return "버스 또는 도보"
        else:
            return "지하철 또는 버스"