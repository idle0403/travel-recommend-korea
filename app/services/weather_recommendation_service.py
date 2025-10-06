"""
날씨 기반 추천 서비스

실시간 날씨 데이터를 기반으로 최적의 여행 활동 추천
"""

from typing import Dict, Any

class WeatherRecommendationService:
    def get_weather_based_recommendations(self, weather_data: Dict[str, Any], forecast_data: Dict[str, Any]) -> str:
        """날씨 기반 실시간 추천 로직"""
        recommendations = []
        
        # 현재 날씨 기반 추천
        if weather_data.get('is_rainy'):
            recommendations.extend([
                "☔ 비가 오니 실내 활동 우선: 박물관, 미술관, 카페, 쇼핑몰",
                "☔ 지하상가, 지하도 연결된 장소 추천",
                "☔ 실내 체험 활동: VR체험관, 이스케이프룸, 실내 클라이밍"
            ])
        elif weather_data.get('is_sunny'):
            recommendations.extend([
                "☀️ 맑은 날씨로 야외 활동 최적: 공원, 한강, 산책로",
                "☀️ 전망대, 전망카페에서 경치 감상 추천",
                "☀️ 야외 체험: 한강 자전거, 피크닉, 야외 마켓"
            ])
        else:
            recommendations.append("☁️ 흐린 날씨로 실내외 활동 모두 좋음")
        
        # 기온 기반 추천
        temp = weather_data.get('temperature', 18)
        if temp < 5:
            recommendations.append("🧊 추운 날씨: 따뜻한 실내 공간, 온천, 천연 온수 시설 추천")
        elif temp > 28:
            recommendations.append("🌡️ 더운 날씨: 에어컨 시설, 수영장, 아이스링크 추천")
        
        # 바람 기반 추천
        wind_speed = weather_data.get('wind_speed', 0)
        if wind_speed > 10:
            recommendations.append("🌬️ 바람이 강하니 실내 활동 추천")
        
        return "\n".join(recommendations) if recommendations else "날씨가 좋아 모든 활동이 가능합니다."