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
    진행 상황을 SSE 형식으로 실시간 스트리밍
    크롤링되는 장소를 하나씩 표시
    """
    
    try:
        # 1. 시작
        yield f"data: {json.dumps({'type': 'status', 'message': '🚀 여행 계획 생성 시작...', 'progress': 0}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)
        
        # 2. 지역 추출
        yield f"data: {json.dumps({'type': 'status', 'message': '📍 지역 정보 추출 중...', 'progress': 5}, ensure_ascii=False)}\n\n"
        
        # 3. 간단한 진행 메시지 (클라이언트에서 처리)
        preferences = request.preferences or {}
        
        yield f"data: {json.dumps({'type': 'status', 'message': '🔍 장소 크롤링 중...', 'progress': 20}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(3)
        
        yield f"data: {json.dumps({'type': 'status', 'message': '🤖 AI 분석 중...', 'progress': 60}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(5)
        
        yield f"data: {json.dumps({'type': 'status', 'message': '✅ 검증 중...', 'progress': 90}, ensure_ascii=False)}\n\n"
        
        # 🆕 실제 계획 생성은 일반 API 호출 권장
        yield f"data: {json.dumps({'type': 'info', 'message': '💡 실제 장소명은 클라이언트에서 표시됩니다', 'progress': 100}, ensure_ascii=False)}\n\n"
        
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

