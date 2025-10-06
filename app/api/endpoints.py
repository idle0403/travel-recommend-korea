"""
API 엔드포인트 정의

여행 계획 생성, 장소 검색, 날씨 조회 등
모든 API 엔드포인트를 정의합니다.
"""

from datetime import datetime
from typing import Dict, Any, Optional, Union, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

import os
from dotenv import load_dotenv
load_dotenv()  # .env 파일 로드

from app.services.openai_service import OpenAIService
from app.services.notion_service import NotionService
from app.services.naver_service import NaverService
from app.services.google_maps_service import GoogleMapsService
from app.services.weather_service import WeatherService
from app.services.realtime_transport_service import RealtimeTransportService

# 상수 정의
DEFAULT_COORDINATES = {"lat": 37.5665, "lng": 126.9780}

router = APIRouter()

# =============================================================================
# Request/Response 모델 정의
# =============================================================================

class TravelPlanRequest(BaseModel):
    """여행 계획 생성 요청"""
    prompt: str = Field(
        ..., 
        description="자연어 여행 계획 요청",
        example="서울에서 6시간 맛집 위주로 가족 여행"
    )
    user_id: Optional[str] = Field(
        None,
        description="사용자 ID (선택사항)",
        example="user123"
    )
    preferences: Optional[Dict[str, Any]] = Field(
        None,
        description="추가 선호사항",
        example={
            "budget": 200000,
            "activity_level": "relaxed",
            "food_preferences": ["korean", "cafe"],
            "avoid_crowds": True
        }
    )

class ItineraryItem(BaseModel):
    """일정 항목"""
    time: str = Field(..., description="시간", example="09:00")
    name: str = Field(..., description="장소명", example="경복궁")
    activity: str = Field(..., description="활동", example="궁궐 관람")
    location: str = Field(..., description="주소", example="서울시 종로구")
    duration: str = Field(..., description="소요시간", example="30분")
    description: Optional[str] = Field(None, description="설명")
    transportation: Optional[str] = Field(None, description="대중교통 정보")
    rating: Optional[float] = Field(None, description="평점")
    price: Optional[str] = Field(None, description="비용")
    lat: Optional[float] = Field(None, description="위도")
    lng: Optional[float] = Field(None, description="경도")

class TravelPlanResponse(BaseModel):
    """여행 계획 생성 응답"""
    plan_id: str = Field(..., description="생성된 계획 ID")
    title: str = Field(..., description="여행 계획 제목")
    summary: str = Field(..., description="계획 요약")
    itinerary: List[ItineraryItem] = Field(..., description="상세 일정")
    total_cost: Union[int, Dict[str, Any]] = Field(..., description="총 예상 비용")
    notion_url: Optional[str] = Field(None, description="Notion 페이지 URL")
    notion_saved: bool = Field(False, description="Notion 저장 성공 여부")
    notion_error: Optional[str] = Field(None, description="Notion 저장 오류")
    weather_info: Optional[Dict[str, Any]] = Field(None, description="날씨 정보")
    created_at: str = Field(..., description="생성 시간")





# =============================================================================
# 헬퍼 함수들
# =============================================================================

async def _generate_ai_itinerary(request: TravelPlanRequest) -> Dict[str, Any]:
    openai_service = OpenAIService()
    ai_itinerary = await openai_service.generate_detailed_itinerary(
        prompt=request.prompt,
        trip_details=request.preferences or {}
    )
    print(f"AI itinerary generated: {len(ai_itinerary.get('schedule', []))} items")
    return ai_itinerary

async def _process_itinerary(ai_itinerary: Dict[str, Any]) -> tuple:
    sample_itinerary = []
    locations_for_route = []
    
    for item in ai_itinerary.get('schedule', []):
        itinerary_item = ItineraryItem(
            time=item.get('time', '09:00'),
            name=item.get('place_name', ''),
            activity=item.get('activity', ''),
            location=item.get('verified_address', item.get('address', '')),
            duration=item.get('duration', '30분'),
            description=item.get('description', ''),
            transportation=item.get('transportation', ''),
            rating=item.get('google_rating', item.get('rating', 4.0)),
            price=item.get('price', '무료'),
            lat=item.get('lat', DEFAULT_COORDINATES['lat']),
            lng=item.get('lng', DEFAULT_COORDINATES['lng'])
        )
        
        # 추가 데이터 반영
        if hasattr(itinerary_item, '__dict__'):
            itinerary_item.__dict__.update({
                'verified_address': item.get('verified_address'),
                'phone': item.get('phone'),
                'google_rating': item.get('google_rating'),
                'blog_reviews': item.get('blog_reviews', []),
                'blog_contents': item.get('blog_contents', []),
                'opening_hours': item.get('opening_hours', []),
                'website': item.get('website'),
                'verified': item.get('verified', False)
            })
        
        sample_itinerary.append(itinerary_item)
        locations_for_route.append({
            'name': item.get('place_name', ''),
            'lat': item.get('lat', DEFAULT_COORDINATES['lat']),
            'lng': item.get('lng', DEFAULT_COORDINATES['lng'])
        })
    
    # 경로 최적화 및 실시간 대중교통 정보
    maps_service = GoogleMapsService()
    transport_service = RealtimeTransportService()
    optimized_route = await maps_service.get_optimized_route(locations_for_route)
    
    # 실시간 대중교통 정보 추가
    if locations_for_route:
        first_location = locations_for_route[0]['name']
        last_location = locations_for_route[-1]['name'] if len(locations_for_route) > 1 else first_location
        realtime_transport = await transport_service.get_optimal_route_with_realtime(first_location, last_location)
        optimized_route['realtime_transport'] = realtime_transport
    
    # 경로 정보 및 실시간 대중교통 정보 반영
    if optimized_route.get('route_segments'):
        for i, segment in enumerate(optimized_route['route_segments']):
            if i < len(sample_itinerary):
                sample_itinerary[i].__dict__.update({
                    'route_distance': segment.get('distance', ''),
                    'route_duration': segment.get('duration', ''),
                    'route_steps': segment.get('steps', []),
                    'realtime_transport': optimized_route.get('realtime_transport', {})
                })
    
    return sample_itinerary, optimized_route

async def _get_weather_info(city: str) -> Dict[str, Any]:
    """실시간 날씨 정보 조회"""
    weather_service = WeatherService()
    return await weather_service.get_current_weather(city)

async def _save_to_notion(request: TravelPlanRequest, itinerary: List, route_info: Dict) -> tuple:
    notion_service = NotionService()
    notion_saved = False
    notion_url = None
    notion_error = None
    
    try:
        total_cost = _calculate_total_cost(itinerary)
        notion_data = {
            "title": f"🇰🇷 AI 추천 여행 계획 - {request.prompt[:20]}...",
            "summary": "실제 API 연동으로 검증된 장소들과 최적화된 경로로 구성된 맞춤형 여행 계획입니다.",
            "itinerary": [item.__dict__ if hasattr(item, '__dict__') else item for item in itinerary],
            "total_cost": total_cost,
            "route_info": route_info
        }
        notion_url = notion_service.create_travel_plan_page(notion_data)
        notion_saved = True
        print(f"Notion 저장 성공: {notion_url}")
    except Exception as e:
        notion_error = str(e)
        print(f"Notion 저장 오류: {str(e)}")
    
    return notion_url, notion_saved, notion_error

def _calculate_total_cost(itinerary: List) -> int:
    total_cost = 0
    for item in itinerary:
        if item.price and item.price != '무료':
            try:
                cost_str = item.price.replace('원', '').replace(',', '').strip()
                if cost_str.isdigit():
                    total_cost += int(cost_str)
            except:
                pass
    return total_cost

def _create_response(plan_id: str, request: TravelPlanRequest, itinerary: List, total_cost: int, route_info: Dict, notion_url: str, notion_saved: bool, notion_error: str, weather_info: Dict) -> TravelPlanResponse:
    return TravelPlanResponse(
        plan_id=plan_id,
        title=f"🇰🇷 AI 추천 여행 계획 - {request.prompt[:20]}...",
        summary="실제 API 연동으로 검증된 장소들과 최적화된 경로로 구성된 맞춤형 여행 계획입니다.",
        itinerary=itinerary,
        total_cost={
            'amount': total_cost,
            'currency': 'KRW',
            'route_info': route_info
        },
        notion_url=notion_url,
        notion_saved=notion_saved,
        notion_error=notion_error,
        weather_info=weather_info,
        created_at=datetime.now().isoformat()
    )

# =============================================================================
# 메인 API 엔드포인트
# =============================================================================

@router.post("/plan", response_model=TravelPlanResponse)
async def create_travel_plan(
    request: TravelPlanRequest,
    background_tasks: BackgroundTasks
):
    """
    🚀 **여행 계획 생성 (메인 기능)**
    
    자연어 프롬프트를 받아서 AI가 최적화된 여행 계획을 생성하고,
    Notion에 예쁜 템플릿으로 자동 저장합니다.
    
    ### 사용 예시:
    - "이번 주말 서울 반나절 데이트 코스"
    - "다음주 제주도 2박3일 가족여행" 
    - "부산 1박2일 혼자 힐링 여행"
    - "친구들과 홍대 맛집 투어"
    
    ### 자동으로 고려되는 요소:
    - 📍 지역별 인기 관광지, 맛집
    - 🌤️ 실시간 날씨 (비 예보시 실내 활동 우선)
    - 👥 혼잡도 정보 (대기시간, 피크시간 회피)
    - 🚇 실시간 대중교통 정보 (버스/지하철 도착시간, 혼잡도)
    - 💰 예산 범위 및 가성비
    - ⏰ 영업시간, 휴무일
    """
    try:
        import uuid
        plan_id = str(uuid.uuid4())
        
        print(f"Received request: {request.prompt}")
        print(f"Preferences: {request.preferences}")
        
        # AI 일정 생성
        ai_itinerary = await _generate_ai_itinerary(request)
        
        # 일정 및 경로 처리
        sample_itinerary, optimized_route = await _process_itinerary(ai_itinerary)
        
        # Notion 저장은 사용자 선택에 따라 결정
        notion_url = None
        notion_saved = False
        notion_error = None
        
        # 비용 계산
        total_cost = _calculate_total_cost(sample_itinerary)
        
        # 날씨 정보 조회
        city = request.preferences.get('city', 'Seoul') if request.preferences else 'Seoul'
        from app.services.city_service import CityService
        city_service = CityService()
        weather_code = city_service.get_weather_code(city)
        weather_info = await _get_weather_info(weather_code)
        
        # 응답 생성
        response = _create_response(plan_id, request, sample_itinerary, total_cost, optimized_route, notion_url, notion_saved, notion_error, weather_info)
        
        print(f"Response created successfully with {len(sample_itinerary)} items")
        return response
        
    except Exception as e:
        import traceback
        print(f"Error in create_travel_plan: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"계획 생성 중 오류 발생: {str(e)}")

@router.get("/health")
async def health_check():
    """
    ❤️ **서비스 상태 확인**
    
    API 서버와 연결된 외부 서비스들의 상태를 확인합니다.
    """
    status = {
        "service": "Korean Travel Planner API",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
    
    # 기본 상태만 반환
    status["apis"] = {
        "openai": "configured" if os.getenv("OPENAI_API_KEY") else "missing",
        "google_maps": "configured" if os.getenv("GOOGLE_MAPS_API_KEY") else "missing",
        "notion": "configured" if os.getenv("NOTION_TOKEN") else "missing",
        "naver": "configured" if os.getenv("NAVER_CLIENT_ID") else "missing"
    }
    
    return status

@router.post("/save-notion")
async def save_to_notion(request: dict):
    """
    💾 **Notion 저장**
    
    사용자가 선택적으로 Notion에 여행 계획을 저장합니다.
    """
    try:
        notion_service = NotionService()
        
        # 여행 계획 데이터 구성
        notion_data = {
            "title": f"🇰🇷 AI 추천 여행 계획 - {datetime.now().strftime('%Y-%m-%d')}",
            "summary": "실제 API 연동으로 검증된 장소들과 최적화된 경로로 구성된 맞춤형 여행 계획입니다.",
            "itinerary": request.get('itinerary', []),
            "total_cost": request.get('total_cost', 0)
        }
        
        notion_url = notion_service.create_travel_plan_page(notion_data)
        
        return {
            "success": True,
            "url": notion_url,
            "message": "Notion에 성공적으로 저장되었습니다."
        }
        
    except Exception as e:
        print(f"Notion 저장 오류: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Notion 저장에 실패했습니다."
        }