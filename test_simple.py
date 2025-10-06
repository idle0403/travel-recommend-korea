#!/usr/bin/env python3
"""
간단한 테스트 스크립트
"""

import requests
import json

def test_api():
    """API 테스트"""
    url = "http://localhost:8000/api/travel/plan"
    
    data = {
        "prompt": "서울에서 당일치기 맛집 투어",
        "preferences": {
            "city": "Seoul",
            "travel_style": "food_tour",
            "start_date": "2024-12-01",
            "end_date": "2024-12-01",
            "start_time": "11:00",
            "end_time": "21:00",
            "duration_days": 0,
            "duration_hours": 10
        }
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 성공! 일정 {len(result.get('itinerary', []))}개 생성됨")
        else:
            print(f"❌ 실패: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 오류: {str(e)}")

if __name__ == "__main__":
    test_api()