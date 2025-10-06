"""
날씨 API 서비스

OpenWeatherMap API를 통한 실시간 날씨 정보 조회
"""

import os
import aiohttp
from typing import Dict, Any
from app.services.ssl_helper import create_http_session

class WeatherService:
    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    async def get_current_weather(self, city: str = "Seoul") -> Dict[str, Any]:
        """현재 날씨 조회"""
        if not self.api_key:
            return self._mock_weather_data()
        
        params = {
            "q": f"{city},KR",
            "appid": self.api_key,
            "units": "metric",
            "lang": "kr"
        }
        
        try:
            async with create_http_session() as session:
                async with session.get(f"{self.base_url}/weather", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_weather_data(data)
                    else:
                        return self._mock_weather_data()
        except Exception as e:
            print(f"날씨 API 오류: {str(e)}")
            return self._mock_weather_data()
    
    async def get_forecast(self, city: str = "Seoul") -> Dict[str, Any]:
        """5일 예보 조회"""
        if not self.api_key:
            return self._mock_forecast_data()
        
        params = {
            "q": f"{city},KR",
            "appid": self.api_key,
            "units": "metric",
            "lang": "kr"
        }
        
        try:
            async with create_http_session() as session:
                async with session.get(f"{self.base_url}/forecast", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_forecast_data(data)
                    else:
                        return self._mock_forecast_data()
        except Exception as e:
            print(f"날씨 예보 API 오류: {str(e)}")
            return self._mock_forecast_data()
    
    def _process_weather_data(self, data: Dict) -> Dict[str, Any]:
        """날씨 데이터 처리"""
        weather = data.get("weather", [{}])[0]
        main = data.get("main", {})
        
        return {
            "condition": weather.get("description", "맑음"),
            "temperature": round(main.get("temp", 18)),
            "feels_like": round(main.get("feels_like", 18)),
            "humidity": main.get("humidity", 60),
            "pressure": main.get("pressure", 1013),
            "visibility": data.get("visibility", 10000) / 1000,
            "wind_speed": data.get("wind", {}).get("speed", 2),
            "rain_probability": data.get("rain", {}).get("1h", 0),
            "weather_code": weather.get("id", 800),
            "is_rainy": weather.get("id", 800) < 600,
            "is_sunny": weather.get("id", 800) == 800,
            "recommendation": self._get_weather_recommendation(weather.get("id", 800))
        }
    
    def _process_forecast_data(self, data: Dict) -> Dict[str, Any]:
        """예보 데이터 처리"""
        forecasts = []
        for item in data.get("list", [])[:8]:  # 24시간 예보
            weather = item.get("weather", [{}])[0]
            main = item.get("main", {})
            
            forecasts.append({
                "time": item.get("dt_txt", ""),
                "temperature": round(main.get("temp", 18)),
                "condition": weather.get("description", "맑음"),
                "rain_probability": item.get("pop", 0) * 100,
                "is_rainy": weather.get("id", 800) < 600
            })
        
        return {"forecasts": forecasts}
    
    def _get_weather_recommendation(self, weather_code: int) -> str:
        """날씨 코드 기반 추천"""
        if weather_code < 600:  # 비/눈
            return "실내 활동 추천 (카페, 박물관, 쇼핑몰)"
        elif weather_code < 700:  # 눈
            return "실내 활동 또는 겨울 액티비티 추천"
        elif weather_code < 800:  # 안개/먼지
            return "실내 활동 추천, 야외 활동 시 마스크 착용"
        elif weather_code == 800:  # 맑음
            return "야외 활동 최적 (공원, 한강, 관광지)"
        else:  # 구름
            return "실내외 활동 모두 좋음"
    
    def _mock_weather_data(self) -> Dict[str, Any]:
        """모의 날씨 데이터"""
        return {
            "condition": "맑음",
            "temperature": 18,
            "feels_like": 20,
            "humidity": 65,
            "pressure": 1013,
            "visibility": 10,
            "wind_speed": 2.5,
            "rain_probability": 0,
            "weather_code": 800,
            "is_rainy": False,
            "is_sunny": True,
            "recommendation": "야외 활동 최적 (공원, 한강, 관광지)"
        }
    
    def _mock_forecast_data(self) -> Dict[str, Any]:
        """모의 예보 데이터"""
        return {
            "forecasts": [
                {
                    "time": "2024-12-01 12:00:00",
                    "temperature": 18,
                    "condition": "맑음",
                    "rain_probability": 0,
                    "is_rainy": False
                }
            ]
        }