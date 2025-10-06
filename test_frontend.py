#!/usr/bin/env python3
"""
프론트엔드 테스트 스크립트

웹 프론트엔드와 API 연동이 정상적으로 작동하는지 검증합니다.
"""

import asyncio
import aiohttp
import json
from datetime import datetime

API_BASE_URL = "http://localhost:8000"

async def test_api_endpoints():
    """API 엔드포인트 테스트"""
    print("🧪 API 엔드포인트 테스트 시작")
    
    async with aiohttp.ClientSession() as session:
        # 1. Health Check
        print("\n1️⃣ Health Check 테스트")
        try:
            async with session.get(f"{API_BASE_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health Check 성공: {data['status']}")
                else:
                    print(f"❌ Health Check 실패: {response.status}")
        except Exception as e:
            print(f"❌ Health Check 오류: {str(e)}")
        
        # 2. Travel Plan API
        print("\n2️⃣ 여행 계획 생성 API 테스트")
        test_request = {
            "prompt": "서울에서 6시간 맛집 위주로 가족 여행 계획을 세워주세요"
        }
        
        try:
            async with session.post(
                f"{API_BASE_URL}/api/travel/plan",
                json=test_request,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 여행 계획 생성 성공!")
                    print(f"   📋 제목: {data.get('title', 'N/A')}")
                    print(f"   📍 일정 수: {len(data.get('itinerary', []))}")
                    print(f"   💰 총 비용: {data.get('total_cost', 'N/A')}")
                    print(f"   📝 Notion 저장: {'✅' if data.get('notion_saved') else '❌'}")
                    
                    # 일정 상세 출력
                    print("\n   📅 상세 일정:")
                    for i, item in enumerate(data.get('itinerary', [])[:3]):  # 처음 3개만
                        print(f"      {i+1}. {item.get('time')} - {item.get('name')}")
                        print(f"         📍 {item.get('location')}")
                        print(f"         ⏱️ {item.get('duration')}")
                        
                else:
                    error_data = await response.text()
                    print(f"❌ 여행 계획 생성 실패: {response.status}")
                    print(f"   오류 내용: {error_data}")
        except Exception as e:
            print(f"❌ 여행 계획 생성 오류: {str(e)}")

def test_frontend_files():
    """프론트엔드 파일 존재 확인"""
    print("\n🌐 프론트엔드 파일 확인")
    
    import os
    frontend_path = "frontend"
    
    required_files = [
        "index.html",
        "script.js"
    ]
    
    for file in required_files:
        file_path = os.path.join(frontend_path, file)
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"✅ {file} 존재 ({file_size:,} bytes)")
        else:
            print(f"❌ {file} 없음")

def test_html_structure():
    """HTML 구조 검증"""
    print("\n📄 HTML 구조 검증")
    
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        
        required_elements = [
            "Google Maps API",
            "timeline",
            "placeDetails", 
            "map",
            "notionStatus",
            "placeModal"
        ]
        
        for element in required_elements:
            if element in html_content:
                print(f"✅ {element} 포함됨")
            else:
                print(f"❌ {element} 누락")
                
    except Exception as e:
        print(f"❌ HTML 파일 읽기 오류: {str(e)}")

def test_javascript_functions():
    """JavaScript 함수 검증"""
    print("\n🔧 JavaScript 함수 검증")
    
    try:
        with open("frontend/script.js", "r", encoding="utf-8") as f:
            js_content = f.read()
        
        required_functions = [
            "initMap",
            "displayTimeline",
            "verifyAndDisplayPlaces",
            "displayRoute",
            "showPlaceModal",
            "updateNotionStatus"
        ]
        
        for func in required_functions:
            if f"function {func}" in js_content or f"{func} =" in js_content:
                print(f"✅ {func} 함수 존재")
            else:
                print(f"❌ {func} 함수 누락")
                
    except Exception as e:
        print(f"❌ JavaScript 파일 읽기 오류: {str(e)}")

async def main():
    """메인 테스트 실행"""
    print("🚀 한국 여행 플래너 프론트엔드 테스트")
    print("=" * 50)
    
    # 파일 구조 테스트
    test_frontend_files()
    test_html_structure()
    test_javascript_functions()
    
    # API 테스트 (서버가 실행 중일 때만)
    print("\n🌐 API 연동 테스트")
    print("⚠️  API 테스트를 위해서는 서버가 실행 중이어야 합니다:")
    print("   python -m uvicorn app.main:app --reload")
    
    try:
        await test_api_endpoints()
    except Exception as e:
        print(f"❌ API 서버 연결 실패: {str(e)}")
        print("   서버가 실행 중인지 확인해주세요.")
    
    print("\n" + "=" * 50)
    print("🎯 테스트 완료!")
    print("\n📋 사용법:")
    print("1. 서버 실행: python -m uvicorn app.main:app --reload")
    print("2. 브라우저에서 http://localhost:8000 접속")
    print("3. 여행 계획 요청 입력 후 테스트")

if __name__ == "__main__":
    asyncio.run(main())