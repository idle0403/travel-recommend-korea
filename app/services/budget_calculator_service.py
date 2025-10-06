"""
비용 계산기 서비스
"""

from typing import Dict, Any, List

class BudgetCalculatorService:
    def __init__(self):
        # 기본 비용 데이터
        self.base_costs = {
            "transportation": {
                "subway": 1370,
                "bus": 1370,
                "taxi_per_km": 1000,
                "ktx_seoul_busan": 55800
            },
            "food": {
                "street_food": 5000,
                "casual_dining": 15000,
                "fine_dining": 50000,
                "cafe": 8000
            },
            "attractions": {
                "palace": 3000,
                "museum": 8000,
                "theme_park": 56000,
                "observatory": 27000
            },
            "accommodation": {
                "hostel": 30000,
                "hotel_3star": 80000,
                "hotel_4star": 150000,
                "hotel_5star": 300000
            }
        }
    
    def calculate_detailed_budget(self, itinerary: List[Dict[str, Any]], travel_style: str = "moderate") -> Dict[str, Any]:
        """상세 예산 계산"""
        total_cost = 0
        breakdown = {
            "transportation": 0,
            "food": 0,
            "attractions": 0,
            "accommodation": 0,
            "miscellaneous": 0
        }
        
        # 여행 스타일별 승수
        style_multipliers = {
            "budget": 0.7,
            "moderate": 1.0,
            "luxury": 1.8
        }
        multiplier = style_multipliers.get(travel_style, 1.0)
        
        for item in itinerary:
            # 교통비 계산
            transport_cost = self._calculate_transport_cost(item)
            breakdown["transportation"] += transport_cost
            
            # 음식비 계산
            food_cost = self._calculate_food_cost(item, multiplier)
            breakdown["food"] += food_cost
            
            # 관광지 입장료 계산
            attraction_cost = self._calculate_attraction_cost(item)
            breakdown["attractions"] += attraction_cost
        
        # 숙박비 (1박 이상인 경우)
        if len(set(item.get('day', 1) for item in itinerary)) > 1:
            nights = len(set(item.get('day', 1) for item in itinerary)) - 1
            accommodation_cost = self._calculate_accommodation_cost(nights, travel_style)
            breakdown["accommodation"] = accommodation_cost
        
        # 기타 비용 (총 비용의 15%)
        subtotal = sum(breakdown.values())
        breakdown["miscellaneous"] = int(subtotal * 0.15)
        
        total_cost = sum(breakdown.values())
        
        return {
            "total_cost": total_cost,
            "breakdown": breakdown,
            "per_person": total_cost,
            "currency": "KRW",
            "travel_style": travel_style,
            "recommendations": self._get_budget_recommendations(total_cost, travel_style)
        }
    
    def _calculate_transport_cost(self, item: Dict[str, Any]) -> int:
        """교통비 계산"""
        transportation = item.get('transportation', '').lower()
        
        if '지하철' in transportation or 'subway' in transportation:
            return self.base_costs["transportation"]["subway"]
        elif '버스' in transportation or 'bus' in transportation:
            return self.base_costs["transportation"]["bus"]
        elif '택시' in transportation or 'taxi' in transportation:
            return self.base_costs["transportation"]["taxi_per_km"] * 3  # 평균 3km
        else:
            return self.base_costs["transportation"]["subway"]  # 기본값
    
    def _calculate_food_cost(self, item: Dict[str, Any], multiplier: float) -> int:
        """음식비 계산"""
        activity = item.get('activity', '').lower()
        place_name = item.get('place_name', '').lower()
        
        if any(word in activity or word in place_name for word in ['카페', 'cafe', '커피']):
            return int(self.base_costs["food"]["cafe"] * multiplier)
        elif any(word in activity or word in place_name for word in ['맛집', '식당', '음식']):
            if '고급' in activity or '파인' in activity:
                return int(self.base_costs["food"]["fine_dining"] * multiplier)
            else:
                return int(self.base_costs["food"]["casual_dining"] * multiplier)
        elif '시장' in activity or '길거리' in activity:
            return int(self.base_costs["food"]["street_food"] * multiplier)
        
        return 0
    
    def _calculate_attraction_cost(self, item: Dict[str, Any]) -> int:
        """관광지 입장료 계산"""
        place_name = item.get('place_name', '').lower()
        activity = item.get('activity', '').lower()
        
        if any(word in place_name for word in ['궁', 'palace']):
            return self.base_costs["attractions"]["palace"]
        elif any(word in place_name for word in ['박물관', 'museum']):
            return self.base_costs["attractions"]["museum"]
        elif any(word in place_name for word in ['롯데월드', '에버랜드', '놀이공원']):
            return self.base_costs["attractions"]["theme_park"]
        elif any(word in place_name for word in ['타워', '전망대', 'observatory']):
            return self.base_costs["attractions"]["observatory"]
        
        # 가격 정보가 있는 경우
        price_str = item.get('price', '무료')
        if price_str and price_str != '무료':
            try:
                return int(''.join(filter(str.isdigit, price_str)))
            except:
                pass
        
        return 0
    
    def _calculate_accommodation_cost(self, nights: int, travel_style: str) -> int:
        """숙박비 계산"""
        style_mapping = {
            "budget": "hostel",
            "moderate": "hotel_3star",
            "luxury": "hotel_5star"
        }
        
        accommodation_type = style_mapping.get(travel_style, "hotel_3star")
        cost_per_night = self.base_costs["accommodation"][accommodation_type]
        
        return cost_per_night * nights
    
    def _get_budget_recommendations(self, total_cost: int, travel_style: str) -> List[str]:
        """예산 절약 팁"""
        recommendations = []
        
        if travel_style == "budget":
            recommendations.extend([
                "지하철/버스 1일권 구매로 교통비 절약",
                "전통시장에서 저렴한 먹거리 체험",
                "무료 관광지 위주로 일정 구성"
            ])
        elif total_cost > 200000:
            recommendations.extend([
                "점심시간 할인 메뉴 활용",
                "그룹 할인 혜택 확인",
                "사전 예약 할인 활용"
            ])
        
        recommendations.append(f"예상 총 비용: {total_cost:,}원")
        
        return recommendations