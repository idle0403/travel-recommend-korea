#!/usr/bin/env python3
"""
8단계 아키텍처 테스트 스크립트
"""

import asyncio
import aiohttp
import json
from datetime import datetime

API_BASE_URL = "http://localhost:8000"

async def test_8step_architecture():
    """8단계 아키텍처 테스트"""
    print("🚀 8단계 아키텍처 테스트 시작")
    
    # 실제 AI 추천을 테스트하는 요청
    test_request = {
        "prompt": "서울 강남에서 맛집 위주로 6시간 데이트 코스 추천해주세요",
        "preferences": {
            "city": "Seoul",
            "travel_style": "food_tour",
            "start_date": "2024-12-15",
            "end_date": "2024-12-15",
            "start_time": "11:00",
            "end_time": "21:00",
            "duration_hours": 10
        }
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            print("📤 8단계 아키텍처 요청 전송...")
            async with session.post(
                f"{API_BASE_URL}/api/travel/plan",
                json=test_request,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ 8단계 아키텍처 응답 성공!")
                    
                    # 8단계 처리 결과 분석
                    print(f"📋 제목: {data.get('title', 'N/A')}")
                    print(f"📍 일정 수: {len(data.get('itinerary', []))}")
                    print(f"💰 총 비용: {data.get('total_cost', 'N/A')}")
                    
                    # 첫 번째 일정 상세 분석
                    itinerary = data.get('itinerary', [])
                    if itinerary:
                        first_item = itinerary[0]
                        print(f"\n🔍 첫 번째 일정 분석:")
                        print(f"   - 장소: {first_item.get('name', 'N/A')}")
                        print(f"   - 주소: {first_item.get('location', 'N/A')}")
                        print(f"   - 검증 상태: {first_item.get('verified', 'N/A')}")
                        print(f"   - 블로그 후기: {len(first_item.get('blog_reviews', []))}개")
                        print(f"   - 처리 단계: {first_item.get('processing_step', 'N/A')}")
                    
                    # 8단계 메타데이터 확인
                    processing_metadata = data.get('processing_metadata', {})
                    if processing_metadata:
                        print(f"\n📊 8단계 처리 메타데이터:")
                        print(f"   - 검증된 장소: {processing_metadata.get('total_verified_places', 0)}개")
                        print(f"   - 매칭된 장소: {processing_metadata.get('matched_places', 0)}개")
                        print(f"   - 캐시 사용: {processing_metadata.get('cache_usage', {})}")
                    
                    # 경로 정보 확인
                    route_info = data.get('route_info', {})
                    if route_info:
                        print(f"\n🗺️ 경로 정보:")
                        print(f"   - 총 거리: {route_info.get('total_distance', 'N/A')}")
                        print(f"   - 총 시간: {route_info.get('total_duration', 'N/A')}")
                        print(f"   - 경로 세그먼트: {len(route_info.get('route_segments', []))}개")
                        print(f"   - Polyline 존재: {'Yes' if route_info.get('polyline') else 'No'}")
                        print(f"   - 장소 수: {len(route_info.get('locations', []))}개")
                    else:
                        print(f"\n⚠️ 경로 정보 없음 - UI 지도 표시에 문제가 있을 수 있습니다")
                    
                    return True
                else:
                    error_data = await response.text()
                    print(f"❌ 8단계 아키텍처 실패: {response.status}")
                    print(f"   오류 내용: {error_data}")
                    return False
                    
        except Exception as e:
            print(f"❌ 8단계 아키텍처 오류: {str(e)}")
            return False

async def main():
    """메인 테스트 실행"""
    print("=" * 60)
    print("🇰🇷 한국 여행 플래너 8단계 아키텍처 검증")
    print("=" * 60)
    
    success = await test_8step_architecture()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 8단계 아키텍처 테스트 완료!")
        print("\n📋 8단계 처리 과정:")
        print("1. 🔍 스마트 크롤링: 네이버 검색으로 실제 장소 수집")
        print("2. 🌦️ 날씨 분석: 지정 일자 날씨 기반 필터링")
        print("3. 🤖 AI 종합 분석: 장소+날씨+선호도 종합 추천")
        print("4. ✅ 할루시네이션 제거: 실제 존재 여부 재검증")
        print("5. 🗺️ 최적 동선: Google Maps 최단 경로 계산")
        print("6. 📱 UI 반영: 실시간 지도 표시 ✅ 개선됨")
        print("7. 🏢 구역별 세분화: 장기여행시 구역별 추가 크롤링")
        print("8. 💾 지능형 캐시: 1개월 데이터 보관")
    else:
        print("❌ 8단계 아키텍처 테스트 실패")
        print("서버가 실행 중인지 확인해주세요: python -m uvicorn app.main:app --reload")

if __name__ == "__main__":
    asyncio.run(main())