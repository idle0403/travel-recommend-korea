#!/usr/bin/env python3
"""
API 테스트 스크립트
"""

import requests
import json

def test_health_endpoint():
    """Health 엔드포인트 테스트"""
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"Health Check Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {str(e)}")
        return False

def test_travel_plan_endpoint():
    """여행 계획 생성 엔드포인트 테스트"""
    try:
        data = {
            "prompt": "서울에서 당일치기 맛집 투어",
            "preferences": {
                "city": "Seoul",
                "travel_style": "food_tour"
            }
        }
        
        response = requests.post(
            "http://localhost:8000/api/travel/plan",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Travel Plan Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Plan ID: {result.get('plan_id')}")
            print(f"Title: {result.get('title')}")
            print(f"Itinerary items: {len(result.get('itinerary', []))}")
            print(f"Total cost: {result.get('total_cost')}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Travel plan test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 API 테스트 시작")
    print("=" * 50)
    
    # Health check
    health_ok = test_health_endpoint()
    print()
    
    # Travel plan test
    if health_ok:
        plan_ok = test_travel_plan_endpoint()
        print()
        
        if plan_ok:
            print("✅ 모든 테스트 통과!")
        else:
            print("❌ 여행 계획 테스트 실패")
    else:
        print("❌ Health check 실패 - 서버가 실행 중인지 확인하세요")