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
            
            print(f"   🔍 필터링 전: {len(schedule_frame)}개 시간대, days_count={days_count}, end_time={end_time}")
            
            # end_time 필터링 적용
            schedule_frame = self._filter_by_end_time(schedule_frame, days_count, end_time)
            
            print(f"   ✅ AI 스케줄 프레임 생성 완료: {len(schedule_frame)}개 시간대 (end_time 필터링 적용)")
            
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
    
    def _filter_by_end_time(
        self,
        schedule_frame: List[Dict[str, Any]],
        days_count: int,
        end_time: str
    ) -> List[Dict[str, Any]]:
        """
        end_time을 기준으로 스케줄 필터링
        마지막 날의 경우 end_time 이후에 시작하는 시간대 제거
        """
        print(f"   🔍 _filter_by_end_time 호출: schedule_frame={len(schedule_frame) if schedule_frame else 0}, days_count={days_count}, end_time={end_time}")
        
        if not schedule_frame or not end_time:
            print(f"   ⚠️ 필터링 스킵: schedule_frame={len(schedule_frame) if schedule_frame else 0}, end_time={end_time}")
            return schedule_frame
        
        if not days_count:
            print(f"   ⚠️ 필터링 스킵: days_count={days_count}")
            return schedule_frame
        
        try:
            # end_time을 분으로 변환 (예: "18:00" -> 1080분)
            end_hour, end_minute = map(int, end_time.split(':'))
            end_minutes = end_hour * 60 + end_minute
            
            print(f"   🔍 필터링 시작: end_time={end_time} ({end_minutes}분), days_count={days_count}")
            
            filtered = []
            filtered_count = 0
            
            for item in schedule_frame:
                day = item.get('day', 1)
                time_slot = item.get('time_slot', '')
                
                # 디버깅: 마지막 날 항목 확인
                if day == days_count:
                    print(f"   🔍 마지막 날 항목: day={day}, time_slot={time_slot}")
                
                # 마지막 날이 아니면 모두 포함
                if day != days_count:
                    filtered.append(item)
                    continue
                
                # 마지막 날인 경우 end_time 체크
                # time_slot 파싱 (예: "20:00-22:00" 또는 "20:00")
                if '-' in time_slot:
                    start_str = time_slot.split('-')[0].strip()
                    end_str = time_slot.split('-')[1].strip()
                else:
                    start_str = time_slot.strip()
                    end_str = None
                
                try:
                    start_hour, start_minute = map(int, start_str.split(':'))
                    start_minutes = start_hour * 60 + start_minute
                    
                    # 종료 시간도 파싱 (있는 경우)
                    end_slot_minutes = None
                    if end_str:
                        try:
                            end_slot_hour, end_slot_minute = map(int, end_str.split(':'))
                            end_slot_minutes = end_slot_hour * 60 + end_slot_minute
                        except:
                            pass
                    
                    # 마지막 날인 경우: 시작 시간이 end_time 이후이면 제외
                    # 또는 종료 시간이 end_time을 초과하면 제외 (더 엄격한 필터링)
                    if start_minutes > end_minutes:
                        # 시작 시간이 end_time 이후
                        print(f"   🚫 필터링: {day}일차 {time_slot} (시작 {start_str} > end_time {end_time})")
                        filtered_count += 1
                        continue
                    elif end_slot_minutes and end_slot_minutes > end_minutes:
                        # 종료 시간이 end_time을 초과 (예: 17:30-18:30, end_time=18:00)
                        # 이 경우는 포함하되, 종료 시간을 end_time으로 조정할 수도 있음
                        # 하지만 일단은 포함하는 것이 자연스러움
                        pass
                    
                    filtered.append(item)
                except (ValueError, IndexError) as e:
                    # 시간 파싱 실패 시 포함 (안전하게 처리)
                    print(f"   ⚠️ 시간 파싱 실패: {time_slot}, 포함: {e}")
                    filtered.append(item)
            
            if filtered_count > 0:
                print(f"   ✅ end_time 필터링 완료: {filtered_count}개 시간대 제외, {len(filtered)}개 유지")
            
            return filtered
            
        except Exception as e:
            print(f"   ⚠️ end_time 필터링 실패: {e}, 원본 반환")
            import traceback
            print(traceback.format_exc())
            return schedule_frame
    
    def _create_fallback_frame(
        self,
        days_count: int,
        start_time: str = "09:00",
        end_time: str = "18:00"
    ) -> List[Dict[str, Any]]:
        """
        AI 실패 시 규칙 기반 폴백 프레임 생성
        end_time을 고려하여 시간대 필터링
        """
        print(f"   ⚠️ 폴백 모드: 규칙 기반 스케줄 프레임 생성 (end_time: {end_time})")
        
        frame = []
        
        # end_time을 분으로 변환
        try:
            end_hour, end_minute = map(int, end_time.split(':'))
            end_minutes = end_hour * 60 + end_minute
        except:
            end_minutes = 18 * 60  # 기본값 18:00
        
        for day in range(1, days_count + 1):
            # 기본 시간대 패턴
            time_slots = [
                {"slot": "09:00-11:00", "type": "tourist_attraction", "purpose": "오전 관광", "radius": 5.0 if day == 1 else 3.0, "duration": 120, "priority": "high"},
                {"slot": "11:30-13:00", "type": "restaurant", "purpose": "점심 식사", "radius": 2.0, "duration": 90, "priority": "high"},
                {"slot": "13:30-15:00", "type": "cafe", "purpose": "카페 휴식", "radius": 1.5, "duration": 60, "priority": "medium"},
                {"slot": "15:30-17:30", "type": "tourist_attraction", "purpose": "오후 관광", "radius": 3.0, "duration": 120, "priority": "high"},
                {"slot": "18:00-19:30", "type": "restaurant", "purpose": "저녁 식사", "radius": 2.0, "duration": 90, "priority": "high"},
                {"slot": "20:00-22:00", "type": "bar", "purpose": "야경/술집", "radius": 3.0, "duration": 120, "priority": "medium"}
            ]
            
            for ts in time_slots:
                # 마지막 날인 경우 end_time 이후 시간대 제외
                if day == days_count:
                    slot_start_str = ts["slot"].split('-')[0]
                    try:
                        slot_start_hour, slot_start_minute = map(int, slot_start_str.split(':'))
                        slot_start_minutes = slot_start_hour * 60 + slot_start_minute
                        
                        if slot_start_minutes >= end_minutes:
                            # end_time 이후 시간대는 제외
                            continue
                    except:
                        pass
                
                frame.append({
                    "day": day,
                    "time_slot": ts["slot"],
                    "place_type": ts["type"],
                    "purpose": ts["purpose"],
                    "search_keywords": self._get_keywords_for_type(ts["type"]),
                    "search_radius_km": ts["radius"],
                    "priority": ts["priority"],
                    "expected_duration_minutes": ts["duration"]
                })
        
        return frame
    
    def _get_keywords_for_type(self, place_type: str) -> List[str]:
        """장소 유형에 따른 검색 키워드 반환"""
        keywords_map = {
            "tourist_attraction": ["관광지", "명소"],
            "restaurant": ["맛집", "식당"],
            "cafe": ["카페", "디저트"],
            "bar": ["바", "펍", "야경명소"]
        }
        return keywords_map.get(place_type, ["장소"])

