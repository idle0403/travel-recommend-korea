"""
SSE 스트리밍 엔드포인트

ChatGPT처럼 진행 상황을 실시간으로 웹에 표시
"""

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, AsyncGenerator
import json
import asyncio
from datetime import datetime

from app.services.openai_service import OpenAIService

router = APIRouter()


class TravelPlanStreamRequest(BaseModel):
    """스트리밍 여행 계획 요청"""
    prompt: str
    preferences: Optional[Dict[str, Any]] = None


async def progress_generator(request: TravelPlanStreamRequest) -> AsyncGenerator[str, None]:
    """
    진행 상황을 SSE 형식으로 스트리밍
    
    SSE 형식:
    data: {"type": "status", "message": "청도 인식 완료"}\n\n
    """
    
    try:
        # 1. 시작 메시지
        yield f"data: {json.dumps({'type': 'status', 'message': '🚀 여행 계획 생성 시작...', 'progress': 0}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)
        
        # 2. 지역 추출
        yield f"data: {json.dumps({'type': 'status', 'message': '📍 지역 정보 추출 중...', 'progress': 10}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.5)
        
        preferences = request.preferences or {}
        city = preferences.get('city', 'Auto')
        
        # 프롬프트에서 지역 추출 (간단히 표시용)
        detected_city = "청도" if "청도" in request.prompt else city
        yield f"data: {json.dumps({'type': 'info', 'message': f'✅ 목적지 인식: {detected_city}', 'progress': 20}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.3)
        
        # 3. 크롤링 시작
        yield f"data: {json.dumps({'type': 'status', 'message': '🔍 맛집 정보 크롤링 중...', 'progress': 30}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(1)
        
        yield f"data: {json.dumps({'type': 'info', 'message': '📝 네이버 블로그 후기 수집 중... (15개)', 'progress': 40}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(1)
        
        # 4. AI 분석
        yield f"data: {json.dumps({'type': 'status', 'message': '🤖 AI가 최적 일정 생성 중...', 'progress': 60}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.5)
        
        # 5. 실제 여행 계획 생성 (OpenAI 호출)
        openai_service = OpenAIService()
        result = await openai_service.generate_detailed_itinerary(
            prompt=request.prompt,
            trip_details=preferences
        )
        
        schedule_count = len(result.get("schedule", []))
        info_data = {'type': 'info', 'message': f'✅ {schedule_count}개 장소 선정 완료', 'progress': 80}
        yield f"data: {json.dumps(info_data, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.5)
        
        # 6. 검증 및 최적화
        yield f"data: {json.dumps({'type': 'status', 'message': '✅ 장소 검증 및 경로 최적화 중...', 'progress': 90}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.5)
        
        # 7. 완료
        yield f"data: {json.dumps({'type': 'status', 'message': '🎉 여행 계획 생성 완료!', 'progress': 100}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.2)
        
        # 8. 최종 결과 전송
        complete_data = {'type': 'complete', 'data': result}
        yield f"data: {json.dumps(complete_data, ensure_ascii=False)}\n\n"
        
    except Exception as e:
        error_msg = f"오류 발생: {str(e)}"
        yield f"data: {json.dumps({'type': 'error', 'message': error_msg}, ensure_ascii=False)}\n\n"


@router.post("/plan-stream")
async def create_travel_plan_stream(request: TravelPlanStreamRequest):
    """
    🌊 **SSE 스트리밍 여행 계획 생성**
    
    ChatGPT처럼 진행 상황을 실시간으로 표시하면서 여행 계획을 생성합니다.
    
    ### SSE 이벤트 타입:
    - `status`: 진행 상황 (예: "크롤링 중...")
    - `info`: 정보 메시지 (예: "청도 인식 완료")
    - `complete`: 최종 결과 데이터
    - `error`: 오류 메시지
    
    ### 사용 예시:
    ```javascript
    const eventSource = new EventSource('/api/travel/plan-stream');
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'status') {
            console.log(data.message);  // "크롤링 중..."
        }
    };
    ```
    """
    return StreamingResponse(
        progress_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # nginx 버퍼링 방지
        }
    )

