"""
AI 스케줄 프레이머 (Schedule Framer)

AI가 전체 여행 일정의 "틀"을 생성합니다 (실제 장소명은 제외).
시간대별로 적절한 장소 유형(맛집, 카페, 관광지 등)을 자동 결정하여
다양성 있는 여행 일정을 구성합니다.
"""

import json
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
import os
import redis.asyncio as redis
from datetime import datetime


class AIScheduleFramer:
    """AI 기반 여행 일정 틀 생성기"""
    
    def __init__(self):
        """초기화"""
        self.client = None
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = AsyncOpenAI(api_key=api_key)
        
        # Redis 설정
        self.redis_client = None
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        
        try:
            self.redis_client = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            print(f"✅ AIScheduleFramer Redis 연결: {redis_url}")
        except Exception as e:
            print(f"⚠️ AIScheduleFramer Redis 연결 실패: {e}")
    
    async def create_schedule_frame(
        self,
        prompt: str,
        city: str,
        days_count: int,
        start_time: str = "09:00",
        end_time: str = "18:00",
        travel_style: str = "custom",
        location_context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        AI가 전체 일정의 "틀"을 생성 (장소명 제외)
        
        Args:
            prompt: 사용자 요청 프롬프트
            city: 도시명
            days_count: 여행 일수
            start_time: 매일 시작 시간
            end_time: 매일 종료 시간
            travel_style: 여행 스타일
            location_context: 지역 맥락 정보 (음식, 특성 등)
        
        Returns:
            [
                {
                    "day": 1,
                    "time_slot": "11:00-13:00",
                    "place_type": "restaurant",
                    "purpose": "점심",
                    "search_keywords": ["한식", "현지맛집"],
                    "search_radius_km": 5.0,  # 2.0 → 5.0km
                    "priority": "high"
                },
                ...
            ]
        """
        if not self.client:
            return self._create_fallback_frame(days_count, start_time, end_time)
        
        # Redis 캐시 키
        cache_key = f"schedule_frame:{city}:{days_count}:{travel_style}:{start_time}:{end_time}"
        
        # 캐시 확인
        try:
            if self.redis_client:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    print(f"   ⚡ 스케줄 프레임 캐시 히트: {city} {days_count}일")
                    return json.loads(cached)
        except Exception as e:
            print(f"   ⚠️ 캐시 조회 실패: {e}")
        
        print(f"\n🎬 AI 스케줄 프레임 생성 시작")
        print(f"   도시: {city}")
        print(f"   일수: {days_count}일")
        print(f"   시간: {start_time} ~ {end_time}")
        print(f"   스타일: {travel_style}")
        
        # 지역 맥락 정보 추출
        local_foods = []
        local_features = []
        weather_info = ""
        if location_context:
            local_foods = location_context.get('recommended_food_types', [])
            local_features = location_context.get('features', [])
            weather_info = location_context.get('weather_recommendation', '')
        
        # AI 프롬프트 생성
        system_prompt = """당신은 여행 일정 전문가입니다.
사용자의 여행 요청을 분석하여 시간대별 활동 계획의 "틀"을 생성합니다.
실제 장소명은 제외하고, 각 시간대에 어떤 유형의 장소를 방문해야 할지만 결정합니다.

**🚫 절대 사용하면 안 되는 place_type**:
- spa, hot_spring_spa, sauna, jjimjilbang (찜질방/사우나/목욕탕 절대 제외)
- gym, fitness_center (동네 체육관 제외)

**✅ 사용 가능한 place_type**:
- tourist_attraction (관광지), restaurant (맛집), cafe (카페), bar (바/술집), night_view (야경)"""

        # 🆕 프롬프트 초간소화 + "간결하게" 지시 추가 (토큰 대폭 절약)
        weather_context = f" 날씨:{weather_info}" if weather_info else ""
        user_prompt = f"""
{city} {days_count}일({start_time}-{end_time}) {travel_style}{weather_context}

규칙: 11시 점심, 13:30 카페, 15-17시 관광, 18시 저녁, 20-22시 야간(선택). 유형 연속금지. 반경 넉넉하게 (관광7km, 맛집5km, 카페3km).
🚫 찜질방/사우나/스파 절대 제외!

**간결하게** JSON만 출력 (코드블록X, 설명X):
{{
  "schedule_frame": [
    {{"day":1,"time_slot":"09:00-11:00","place_type":"tourist_attraction","purpose":"오전 관광","search_keywords":["관광지","명소"],"search_radius_km":7.0,"priority":"high","expected_duration_minutes":120}},
    {{"day":1,"time_slot":"11:00-13:00","place_type":"restaurant","purpose":"점심","search_keywords":["맛집"],"search_radius_km":5.0,"priority":"high","expected_duration_minutes":90}}
  ]
}}

{days_count}일치 생성. JSON만."""

        try:
            # 🆕 동적 토큰 제한 (일정 길이에 따라)
            if days_count <= 2:
                max_tokens = 10000  # 1박2일
            elif days_count <= 3:
                max_tokens = 15000  # 2박3일
            else:
                max_tokens = 20000  # 3박4일+
            
            # GPT-5 호출
            print(f"   📤 GPT-5 요청 중...")
            print(f"      모델: gpt-5")
            print(f"      System 프롬프트 길이: {len(system_prompt)} 문자")
            print(f"      User 프롬프트 길이: {len(user_prompt)} 문자")
            print(f"      Max tokens: {max_tokens} (일수: {days_count}일)")
            
            response = await self.client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_completion_tokens=max_tokens  # 🆕 동적 조정
            )
            
            # 🔍 전체 응답 디버깅
            print(f"\n   🔍 === GPT-5 응답 디버깅 시작 ===")
            print(f"   📊 Response ID: {response.id if hasattr(response, 'id') else 'N/A'}")
            print(f"   📊 Model: {response.model if hasattr(response, 'model') else 'N/A'}")
            print(f"   📊 Created: {response.created if hasattr(response, 'created') else 'N/A'}")
            
            if hasattr(response, 'choices') and len(response.choices) > 0:
                choice = response.choices[0]
                print(f"   📊 Choices 개수: {len(response.choices)}")
                print(f"   📊 Finish Reason: {choice.finish_reason if hasattr(choice, 'finish_reason') else 'N/A'}")
                
                if hasattr(choice, 'message'):
                    message = choice.message
                    print(f"   📊 Message Role: {message.role if hasattr(message, 'role') else 'N/A'}")
                    print(f"   📊 Message Content Type: {type(message.content)}")
                    print(f"   📊 Message Content Length: {len(message.content) if message.content else 0} 문자")
                    
                    raw_content = message.content
                    print(f"\n   📥 원본 Content (처음 500자):")
                    print(f"   {repr(raw_content[:500]) if raw_content else 'NONE'}")
                    
                    if raw_content:
                        print(f"\n   📥 원본 Content (마지막 200자):")
                        print(f"   {repr(raw_content[-200:])}")
                else:
                    print(f"   ❌ Message 객체 없음!")
            else:
                print(f"   ❌ Choices 배열 비어있음!")
            
            print(f"   🔍 === GPT-5 응답 디버깅 종료 ===\n")
            
            # 🆕 Content 추출 (먼저 확인)
            content = response.choices[0].message.content
            
            # 🆕 빈 응답 체크 (우선)
            if not content or not content.strip():
                print(f"   ⚠️ GPT-5 빈 응답 반환! 폴백 모드 사용")
                return self._create_fallback_frame(days_count, start_time, end_time)
            
            # 🆕 finish_reason 체크 (두 번째)
            choice = response.choices[0]
            if choice.finish_reason == 'length':
                print(f"   ⚠️ 토큰 부족으로 응답 잘림! 폴백 모드 사용")
                return self._create_fallback_frame(days_count, start_time, end_time)
            
            content = content.strip()
            print(f"   📝 Stripped Content 길이: {len(content)} 문자")
            
            # JSON 파싱
            # 마크다운 코드 블록 제거
            original_content = content
            if content.startswith("```"):
                print(f"   🔧 마크다운 코드 블록 감지, 제거 중...")
                parts = content.split("```")
                if len(parts) >= 2:
                    content = parts[1]
                    if content.startswith("json"):
                        content = content[4:]
                    print(f"   🔧 코드 블록 제거 후 길이: {len(content)} 문자")
            
            content = content.strip()
            
            print(f"   🔍 최종 파싱 시도할 Content (처음 200자):")
            print(f"   {repr(content[:200])}")
            
            # JSON 파싱 시도
            try:
                data = json.loads(content)
                print(f"   ✅ JSON 파싱 성공!")
            except json.JSONDecodeError as parse_error:
                print(f"   ❌ JSON 파싱 실패: {parse_error}")
                print(f"   🔍 파싱 실패 위치: line {parse_error.lineno}, column {parse_error.colno}")
                print(f"   📄 전체 Content:")
                print(f"   {content}")
                raise
            
            schedule_frame = data.get('schedule_frame', [])
            
            print(f"   ✅ AI 스케줄 프레임 생성 완료: {len(schedule_frame)}개 시간대")
            
            # Redis 캐싱 (7일)
            try:
                if self.redis_client:
                    await self.redis_client.setex(
                        cache_key,
                        7 * 24 * 3600,  # 7일
                        json.dumps(schedule_frame, ensure_ascii=False)
                    )
            except Exception as e:
                print(f"   ⚠️ 캐시 저장 실패: {e}")
            
            return schedule_frame
            
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON 파싱 실패 (최종): {e}")
            return self._create_fallback_frame(days_count, start_time, end_time)
            
        except Exception as e:
            print(f"   ❌ AI 호출 실패 (예외): {type(e).__name__}: {e}")
            import traceback
            print(f"   📋 Traceback:")
            print(traceback.format_exc())
            return self._create_fallback_frame(days_count, start_time, end_time)
    
    def _create_fallback_frame(
        self,
        days_count: int,
        start_time: str = "09:00",
        end_time: str = "18:00"
    ) -> List[Dict[str, Any]]:
        """
        AI 실패 시 규칙 기반 폴백 프레임 생성
        """
        print(f"   ⚠️ 폴백 모드: 규칙 기반 스케줄 프레임 생성")
        
        frame = []
        
        for day in range(1, days_count + 1):
            # 패턴: 관광 → 점심 → 카페 → 관광 → 저녁 → 야간(선택적)
            frame.extend([
                {
                    "day": day,
                    "time_slot": "09:00-11:00",
                    "place_type": "tourist_attraction",
                    "purpose": "오전 관광",
                    "search_keywords": ["관광지", "명소"],
                    "search_radius_km": 5.0 if day == 1 else 3.0,  # 1일차만 5km, 이후 3km
                    "priority": "high",
                    "expected_duration_minutes": 120
                },
                {
                    "day": day,
                    "time_slot": "11:30-13:00",
                    "place_type": "restaurant",
                    "purpose": "점심 식사",
                    "search_keywords": ["맛집", "식당"],
                    "search_radius_km": 2.0,  # 🎯 타이트하게: 3.0 → 2.0km
                    "priority": "high",
                    "expected_duration_minutes": 90
                },
                {
                    "day": day,
                    "time_slot": "13:30-15:00",
                    "place_type": "cafe",
                    "purpose": "카페 휴식",
                    "search_keywords": ["카페", "디저트"],
                    "search_radius_km": 1.5,  # 🎯 타이트하게: 2.0 → 1.5km
                    "priority": "medium",
                    "expected_duration_minutes": 60
                },
                {
                    "day": day,
                    "time_slot": "15:30-17:30",
                    "place_type": "tourist_attraction",
                    "purpose": "오후 관광",
                    "search_keywords": ["관광지", "공원"],
                    "search_radius_km": 3.0,  # 🎯 타이트하게: 4.0 → 3.0km
                    "priority": "high",
                    "expected_duration_minutes": 120
                },
                {
                    "day": day,
                    "time_slot": "18:00-19:30",
                    "place_type": "restaurant",
                    "purpose": "저녁 식사",
                    "search_keywords": ["맛집", "저녁식사"],
                    "search_radius_km": 2.0,  # 🎯 타이트하게: 3.0 → 2.0km
                    "priority": "high",
                    "expected_duration_minutes": 90
                },
                {
                    "day": day,
                    "time_slot": "20:00-22:00",
                    "place_type": "bar",
                    "purpose": "야경/술집",
                    "search_keywords": ["바", "펍", "야경명소"],
                    "search_radius_km": 3.0,  # 🎯 타이트하게: 4.0 → 3.0km
                    "priority": "medium",
                    "expected_duration_minutes": 120
                }
            ])
        
        return frame

