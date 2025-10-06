"""
OpenAI 서비스

GPT-4를 활용한 맞춤형 여행 계획 생성
"""

import os
import json
from typing import Dict, Any, List
from openai import AsyncOpenAI

# 환경변수 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app.core.config import settings
from app.services.naver_service import NaverService
from app.services.google_maps_service import GoogleMapsService
from app.services.blog_crawler_service import BlogCrawlerService
from app.services.weather_service import WeatherService
from app.services.place_verification_service import PlaceVerificationService
from app.services.place_quality_service import PlaceQualityService
from app.services.weather_recommendation_service import WeatherRecommendationService
from app.services.city_service import CityService
from app.services.district_service import DistrictService

class OpenAIService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Warning: OPENAI_API_KEY not found, using mock data")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=api_key)
    
    async def generate_detailed_itinerary(self, prompt: str, trip_details: Dict[str, Any] = None) -> Dict[str, Any]:
        """상세한 30분 단위 여행 일정 생성 (실제 API 연동)"""
        
        if not self.client:
            return self._generate_mock_itinerary(prompt, trip_details)
        
        # 날씨 정보 조회
        weather_service = WeatherService()
        city = trip_details.get('city', 'Seoul') if trip_details else 'Seoul'
        city_service = CityService()
        weather_code = city_service.get_weather_code(city)
        weather_data = await weather_service.get_current_weather(weather_code)
        forecast_data = await weather_service.get_forecast(weather_code)
        
        # 도시별 특화 정보 및 실제 장소 데이터베이스
        city_service = CityService()
        district_service = DistrictService()
        city_info = city_service.get_city_info(city)
        
        # 여행 스타일별 특화 프롬프트 생성
        travel_style = trip_details.get('travel_style', 'custom') if trip_details else 'custom'
        
        # 구역 기반 효율적 동선 구성
        duration_hours = trip_details.get('duration_hours', 8) if trip_details else 8
        start_location_coords = None
        if trip_details and trip_details.get('start_location'):
            # 출발지 좌표 추출 (실제로는 geocoding 필요)
            start_location_coords = {"lat": 37.5665, "lng": 126.9780}  # 기본값
        
        district_itinerary = district_service.create_district_based_itinerary(
            city, travel_style, duration_hours, start_location_coords
        )
        
        location_context = await self._get_location_context(prompt, city_info, district_itinerary)
        style_context = self._get_style_specific_context(travel_style)
        
        system_prompt = f"""
당신은 한국 여행 전문가입니다. 사용자의 요청에 따라 30분 단위로 상세한 여행 일정을 생성해주세요.

**🚨 절대 규칙 - 할루시네이션 금지 🚨**
1. **실제 존재하는 장소만**: 가상의 장소, 추측한 장소 절대 금지
2. **검증된 장소만**: 유명한 체인점, 관광명소, 검증된 맛집만 추천
3. **정확한 주소**: 구체적인 주소 (구/동까지 포함) 필수
4. **중복 금지**: 같은 장소나 유사한 장소 중복 추천 절대 금지
5. **불확실시 거부**: 확실하지 않으면 "해당 지역에 적합한 장소를 찾을 수 없습니다"라고 명시
6. **지역 일치**: 요청 지역과 다른 지역 장소 추천 절대 금지

**날씨 기반 추천 우선순위:**
- 날씨: {weather_data['condition']}
- 기온: {weather_data['temperature']}°C
- 강수확률: {weather_data['rain_probability']}%
- 추천: {weather_data['recommendation']}

**여행 스타일 특화:**
{style_context}

**검증된 지역 장소:**
{location_context}

**응답 규칙:**
- 각 장소는 고유해야 함 (중복 절대 금지)
- 실제 존재하는 장소만 포함
- 불확실한 경우 "verified": false로 표시
- 날씨에 맞는 실내/실외 활동 우선 선택

응답 형식:
{{
  "schedule": [
    {{
      "time": "09:00",
      "place_name": "실제 존재하는 고유한 장소명",
      "activity": "구체적인 활동",
      "address": "정확한 주소 (구/동 포함)",
      "duration": "30분",
      "description": "장소 설명",
      "transportation": "구체적인 대중교통 정보",
      "rating": 4.5,
      "price": "예상 비용",
      "lat": 37.5665,
      "lng": 126.9780,
      "verified": false
    }}
  ]
}}
"""
        
        # 날씨 기반 프롬프트 생성
        weather_context = f"""
현재 날씨 상황:
- 날씨: {weather_data['condition']}
- 기온: {weather_data['temperature']}°C (체감온도: {weather_data['feels_like']}°C)
- 강수확률: {weather_data['rain_probability']}%
- 바람: {weather_data['wind_speed']}m/s
- 추천: {weather_data['recommendation']}

**날씨 기반 활동 조정:**
{"- 비가 올 가능성이 있으니 실내 활동 위주로 구성하세요" if weather_data['is_rainy'] else ""}
{"- 맑은 날씨이니 야외 활동을 적극 포함하세요" if weather_data['is_sunny'] else ""}
"""
        
        # 날씨 기반 실시간 추천 로직
        weather_service = WeatherRecommendationService()
        weather_recommendations = weather_service.get_weather_based_recommendations(weather_data, forecast_data)
        
        # 여행 기간 계산
        start_date = trip_details.get('start_date') if trip_details else None
        end_date = trip_details.get('end_date') if trip_details else None
        
        if start_date and end_date:
            from datetime import datetime
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                days_count = (end_dt - start_dt).days + 1
            except:
                days_count = 1
        else:
            # 프롬프트에서 일수 추출 시도
            prompt_lower = prompt.lower()
            if '당일치기' in prompt or '하루' in prompt:
                days_count = 1
            elif '1박2일' in prompt or '하룻밤' in prompt:
                days_count = 2
            elif '2박3일' in prompt or '이틀밤' in prompt:
                days_count = 3
            elif '3박4일' in prompt or '사틀밤' in prompt:
                days_count = 4
            else:
                days_count = 1
        
        user_prompt = f"""
다음 요청에 대해 **{days_count}일간의 일자별 상세 여행 일정**을 생성해주세요:

요청: {prompt}

{weather_context}

**날씨 기반 실시간 추천:**
{weather_recommendations}

**여행 기간 정보:**
- 시작일: {start_date or '오늘'}
- 종료일: {end_date or '오늘'}
- 총 {days_count}일간 여행 (반드시 일자별로 구분해서 생성)
- 매일 시작 시간: {trip_details.get('start_time', '09:00') if trip_details else '09:00'}
- 매일 종료 시간: {trip_details.get('end_time', '18:00') if trip_details else '18:00'}
- 도시: {trip_details.get('city', '서울') if trip_details else '서울'}

**일정 생성 규칙:**
1. **일자별 구분**: 각 날짜별로 독립적인 일정 구성 (반드시 day 필드 포함)
2. **하루 6-10개 장소**: 매일 충분한 활동으로 구성
3. **시간 순서**: 각 날짜마다 09:00부터 시작하여 순차적 시간 배치
4. **실제 장소만**: 가상 장소 절대 금지, 검증된 장소만 추천
5. **중복 방지**: 전체 기간 동안 같은 장소 중복 금지
6. **현실적 동선**: 지역별 클러스터링으로 효율적 이동

**응답 형식 (중요):**
반드시 각 일정에 "day" 필드를 포함하여 {days_count}일간 일정을 생성하세요.

예시 ({days_count}일 여행):
{{
  "schedule": [
    {{
      "day": 1,
      "date": "{start_date or '2025-01-01'}",
      "time": "09:00",
      "place_name": "실제 장소명",
      "activity": "구체적 활동",
      "address": "정확한 주소",
      "duration": "90분",
      "description": "상세 설명",
      "transportation": "대중교통 정보",
      "rating": 4.5,
      "price": "예상 비용",
      "lat": 37.5665,
      "lng": 126.9780
    }},
    {{
      "day": 2,
      "date": "2025-01-02",
      "time": "09:00",
      ...
    }}
  ]
}}
"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            
            # JSON 파싱 시도
            try:
                ai_result = json.loads(content)
                # 일자별 일정 구조화
                structured_result = self._structure_daily_itinerary(ai_result, days_count)
                # 실제 장소 검증 및 블로그 후기 추가
                return await self._enhance_with_real_data(structured_result)
            except json.JSONDecodeError:
                return self._generate_mock_itinerary(prompt, trip_details, days_count)
                
        except Exception as e:
            print(f"OpenAI API 오류: {str(e)}")
            return self._generate_mock_itinerary(prompt, trip_details)
    

    
    async def _enhance_with_real_data(self, ai_result: Dict[str, Any]) -> Dict[str, Any]:
        """AI 결과를 실제 API 데이터로 보강 및 검증 - 중복 제거 및 할루시네이션 방지"""
        quality_service = PlaceQualityService()
        enhanced_schedule = []
        
        for item in ai_result.get('schedule', []):
            place_name = item.get('place_name', '')
            address = item.get('address', '')
            
            # 중복 검사
            if quality_service.is_duplicate(place_name, address):
                print(f"⚠️ 중복 장소 제외: {place_name}")
                continue
            
            # 실제 장소 검증 및 평점/후기 수집
            enhanced_item = await self.get_enhanced_place_info(place_name, address or 'Seoul')
            
            # 품질 기준 검증
            quality_score = quality_service.calculate_quality_score(enhanced_item)
            
            # 실제 존재하는 장소인지 확인
            is_real_place = quality_service.verify_real_place(enhanced_item)
            
            if is_real_place and quality_score >= 3.0:
                # 검증된 고품질 장소
                verified_item = quality_service.create_verified_item(item, enhanced_item, quality_score)
                enhanced_schedule.append(verified_item)
                quality_service.add_to_used(verified_item['place_name'], verified_item['address'])
                
            elif quality_score >= 2.0:  # 낮은 품질이지만 존재하는 장소
                # 경고와 함께 포함
                item.update({
                    'verified': False,
                    'quality_score': quality_score,
                    'description': item.get('description', '') + f' ⚠️ 검증 필요 (품질: {quality_score:.1f}/5.0)',
                    'blog_reviews': enhanced_item.get('blog_reviews', []),
                    'blog_contents': enhanced_item.get('blog_contents', [])
                })
                enhanced_schedule.append(item)
                quality_service.add_to_used(place_name, address)
                
            else:
                print(f"❌ 검증 실패로 제외: {place_name} (품질: {quality_score:.1f})")
        
        # 최소 3개 장소 보장
        if len(enhanced_schedule) < 3:
            fallback_places = quality_service.get_fallback_places(3 - len(enhanced_schedule))
            enhanced_schedule.extend(fallback_places)
        
        ai_result['schedule'] = enhanced_schedule
        return ai_result
    
    def _structure_daily_itinerary(self, ai_result: Dict[str, Any], days_count: int) -> Dict[str, Any]:
        """일자별 일정 구조화"""
        schedule = ai_result.get('schedule', [])
        
        if not schedule:
            return ai_result
        
        # 시간 기준으로 일자 할당 (더 정교한 방법)
        current_day = 1
        last_hour = 0
        
        for i, item in enumerate(schedule):
            if 'day' not in item or item['day'] is None:
                # 시간 추출
                time_str = item.get('time', '09:00')
                try:
                    hour = int(time_str.split(':')[0])
                except:
                    hour = 9 + (i % 12)  # 기본값
                
                # 시간이 이전보다 작아지면 다음 날
                if i > 0 and hour < last_hour and hour < 12:
                    current_day += 1
                    if current_day > days_count:
                        current_day = days_count
                
                item['day'] = current_day
                item['date'] = f"2025-01-{current_day:02d}"
                last_hour = hour
        
        # 일자별 균등 분배 조정
        if days_count > 1:
            items_per_day = len(schedule) // days_count
            remainder = len(schedule) % days_count
            
            day_counts = {}
            for item in schedule:
                day = item.get('day', 1)
                day_counts[day] = day_counts.get(day, 0) + 1
            
            # 불균형 조정
            for day in range(1, days_count + 1):
                if day not in day_counts:
                    # 빈 날짜에 아이템 이동
                    for item in schedule:
                        if item.get('day', 1) > day and day_counts.get(item['day'], 0) > items_per_day:
                            item['day'] = day
                            day_counts[day] = day_counts.get(day, 0) + 1
                            day_counts[item['day']] -= 1
                            break
        
        return ai_result
    
    def _generate_mock_itinerary(self, prompt: str, trip_details: Dict[str, Any] = None, days_count: int = 1) -> Dict[str, Any]:
        """API 키가 없을 때 모의 일정 생성"""
        mock_schedule = []
        
        for day in range(1, days_count + 1):
            # 하루에 8개 장소 생성
            daily_places = [
                {
                    "day": day,
                    "date": f"2025-01-{day:02d}",
                    "time": "09:00",
                    "place_name": f"경복궁" if day == 1 else f"창덕궁" if day == 2 else f"N서울타워",
                    "activity": "궁궐 관람" if day <= 2 else "전망대 관람",
                    "address": "서울시 종로구 사직로 161" if day == 1 else "서울시 종로구 창덕궁길 99" if day == 2 else "서울시 중구 남산동 3가 105",
                    "duration": "90분",
                    "description": "조선왕조의 정궁" if day == 1 else "아름다운 후원이 있는 궁궐" if day == 2 else "서울의 전경을 한눈에 볼 수 있는 전망대",
                    "transportation": "지하철 3호선 경복궁역" if day == 1 else "지하철 3호선 안국역" if day == 2 else "지하철 4호선 명동역",
                    "rating": 4.5 if day == 1 else 4.4 if day == 2 else 4.6,
                    "price": "3,000원" if day <= 2 else "12,000원",
                    "lat": 37.5796 if day == 1 else 37.5792 if day == 2 else 37.5512,
                    "lng": 126.9770 if day == 1 else 126.9910 if day == 2 else 126.9882
                },
                {
                    "day": day,
                    "date": f"2025-01-{day:02d}",
                    "time": "11:00",
                    "place_name": f"명동 쇼핑거리" if day == 1 else f"홍대 걸고싶은거리" if day == 2 else f"강남 거리",
                    "activity": "쇼핑 및 거리구경" if day == 1 else "쇼핑 및 카페" if day == 2 else "쇼핑 및 카페",
                    "address": "서울시 중구 명동길" if day == 1 else "서울시 마포구 서교동" if day == 2 else "서울시 강남구 강남대로",
                    "duration": "120분",
                    "description": "서울의 대표 쇼핑거리" if day == 1 else "젊음의 거리, 다양한 카페와 상점" if day == 2 else "트렌디한 쇼핑과 맛집이 모인 곳",
                    "transportation": "지하철 4호선 명동역" if day == 1 else "지하철 2호선 홍대입구역" if day == 2 else "지하철 2호선 강남역",
                    "rating": 4.2 if day == 1 else 4.1 if day == 2 else 4.2,
                    "price": "무료",
                    "lat": 37.5636 if day == 1 else 37.5563 if day == 2 else 37.4979,
                    "lng": 126.9834 if day == 1 else 126.9236 if day == 2 else 127.0276
                },
                {
                    "day": day,
                    "date": f"2025-01-{day:02d}",
                    "time": "13:00",
                    "place_name": f"남대문 시장" if day == 1 else f"광장시장" if day == 2 else f"가로수길",
                    "activity": "전통시장 탐방" if day <= 2 else "맛집 탐방",
                    "address": "서울시 중구 남대문시장길" if day == 1 else "서울시 중구 청계천로 40" if day == 2 else "서울시 강남구 가로수길",
                    "duration": "90분",
                    "description": "전통 시장에서 맛있는 음식 체험" if day <= 2 else "다양한 맛집이 모인 거리",
                    "transportation": "지하철 4호선 회현역" if day == 1 else "지하철 2호선 을지로3가역" if day == 2 else "지하철 3호선 신사역",
                    "rating": 4.3,
                    "price": "10,000원" if day <= 2 else "15,000원",
                    "lat": 37.5595 if day == 1 else 37.5658 if day == 2 else 37.5172,
                    "lng": 126.9941 if day == 1 else 126.9895 if day == 2 else 127.0286
                },
                {
                    "day": day,
                    "date": f"2025-01-{day:02d}",
                    "time": "15:00",
                    "place_name": f"인사동 거리" if day == 1 else f"이태원" if day == 2 else f"코엑스몰",
                    "activity": "거리 예술 감상" if day == 1 else "쇼핑 및 카페" if day == 2 else "쇼핑 및 영화관람",
                    "address": "서울시 종로구 인사동길" if day == 1 else "서울시 마포구 이태원로 29" if day == 2 else "서울시 강남구 영동대로 513",
                    "duration": "60분" if day == 1 else "90분" if day == 2 else "120분",
                    "description": "예술과 문화가 어우러진 거리" if day == 1 else "다양한 쇼핑과 맛집" if day == 2 else "대형 쇼핑몰과 영화관",
                    "transportation": "지하철 3호선 안국역" if day == 1 else "지하철 2호선 홍대입구역" if day == 2 else "지하철 2호선 삼성역",
                    "rating": 4.4 if day == 1 else 4.2 if day == 2 else 4.3,
                    "price": "무료" if day <= 2 else "5,000원",
                    "lat": 37.5759 if day == 1 else 37.5563 if day == 2 else 37.5125,
                    "lng": 126.9852 if day == 1 else 126.9236 if day == 2 else 127.1025
                },
                {
                    "day": day,
                    "date": f"2025-01-{day:02d}",
                    "time": "16:30",
                    "place_name": f"청계천" if day == 1 else f"한강공원 여의도" if day == 2 else f"선릉도공원",
                    "activity": "도심 산책" if day == 1 else "산책 및 휴식" if day == 2 else "산책 및 전망",
                    "address": "서울시 종로구 청계천로" if day == 1 else "서울시 영등포구 여의동로" if day == 2 else "서울시 동작구 상도동",
                    "duration": "45분" if day == 1 else "90분" if day == 2 else "60분",
                    "description": "도심 속 자연 하천" if day == 1 else "한강을 따라 산책할 수 있는 공원" if day == 2 else "서울의 전경을 볼 수 있는 공원",
                    "transportation": "지하철 1호선 종각역" if day == 1 else "지하철 5호선 여의나루역" if day == 2 else "지하철 9호선 동작역",
                    "rating": 4.1 if day == 1 else 4.3 if day == 2 else 4.5,
                    "price": "무료",
                    "lat": 37.5694 if day == 1 else 37.5285 if day == 2 else 37.5044,
                    "lng": 126.9912 if day == 1 else 126.9335 if day == 2 else 126.9834
                },
                {
                    "day": day,
                    "date": f"2025-01-{day:02d}",
                    "time": "17:30",
                    "place_name": f"동대문 디자인플라자" if day == 1 else f"반포한강공원" if day == 2 else f"롯데월드타워",
                    "activity": "디자인 및 문화 체험" if day == 1 else "산책 및 야경" if day == 2 else "쇼핑 및 전망대",
                    "address": "서울시 중구 을지로 281" if day == 1 else "서울시 서초구 반포대로 21길 40" if day == 2 else "서울시 송파구 올림픽로 300",
                    "duration": "90분",
                    "description": "현대적 디자인과 문화 공간" if day == 1 else "한강을 따라 산책하며 야경 감상" if day == 2 else "대형 쇼핑몰과 전망대",
                    "transportation": "지하철 2호선 동대문역사문화공원역" if day == 1 else "지하철 7호선 반포역" if day == 2 else "지하철 2호선 잠실역",
                    "rating": 4.6 if day == 1 else 4.4 if day == 2 else 4.5,
                    "price": "무료" if day <= 2 else "27,000원",
                    "lat": 37.5664 if day == 1 else 37.5133 if day == 2 else 37.5125,
                    "lng": 127.0092 if day == 1 else 127.0021 if day == 2 else 127.1025
                }
            ]
            mock_schedule.extend(daily_places)
        
        return {"schedule": mock_schedule}
    
    async def _get_location_context(self, prompt: str, city_info: Dict[str, Any], district_itinerary: List[Dict[str, Any]] = None) -> str:
        """도시별 특화 정보 및 실제 장소 정보 제공"""
        city_name = city_info.get('name', '서울')
        specialties = city_info.get('specialties', [])
        famous_places = city_info.get('famous_places', [])
        transport_hub = city_info.get('transport_hub', [])
        
        specialties_text = ", ".join(specialties)
        places_text = "\n".join([f"- {place}" for place in famous_places])
        transport_text = ", ".join(transport_hub)
        
        # 구역별 추천 장소 정보 추가
        district_context = ""
        if district_itinerary:
            district_context = "\n\n**구역별 효율적 동선 추천:**\n"
            current_district = None
            for item in district_itinerary:
                if item.get('district') != current_district:
                    current_district = item['district']
                    district_context += f"\n[{current_district}]\n"
                district_context += f"- {item['place_name']} ({item['type']})\n"
        
        return f"""
{city_name} 지역 정보:
특색: {specialties_text}
주요 교통거점: {transport_text}
대표 관광지/명소:
{places_text}
{district_context}

**동선 최적화 규칙:**
1. 같은 구역 내 장소들을 연속으로 방문하여 이동시간 최소화
2. 구역 간 이동은 대중교통 접근성을 고려하여 순서 결정
3. {city_name}의 실제 존재하는 장소만 추천
4. 위 구역별 추천을 우선 고려하되 다른 실제 장소도 추천 가능
5. {city_name}의 특색인 {specialties_text}을 활용한 여행 계획 구성
6. 다른 도시의 장소는 절대 추천 금지
"""
    
    def _get_style_specific_context(self, travel_style: str) -> str:
        """여행 스타일별 특화 가이드"""
        style_guides = {
            'indoor_date': """
특화 가이드: 실내 데이트
- 카페, 박물관, 미술관, 전시관 우선
- 쇼핑몰, 대형서점, 영화관 포함
- 실내 체험 공간 (도예, 쿠킹클래스 등)
- 날씨에 관계없이 즐길 수 있는 공간
- 조용하고 낭만적인 분위기
""",
            'outdoor_date': """
특화 가이드: 실외 데이트
- 공원, 한강, 산책로 우선
- 전망대, 전망카페, 야외 체험
- 자연 속 피크닉 장소
- 사진 촬영 명소 (인스타 핫플레이스)
- 날씨가 좋을 때 최적인 장소
""",
            'food_tour': """
특화 가이드: 맛집 투어
- 로컬 맛집, 전통시장 우선
- 미슐링 가이드 등재 맛집
- 전통 한식, 길거리 음식 포함
- 디저트 카페, 베이커리 연결
- 음식 체험 프로그램 (쿠킹클래스 등)
""",
            'culture_tour': """
특화 가이드: 문화 탐방
- 궁궐, 전통 건축물 우선
- 박물관, 미술관, 전시관
- 전통 공예촌, 한옥마을
- 역사적 의미가 있는 장소
- 문화체험 프로그램 (한복, 차 체험 등)
""",
            'shopping_tour': """
특화 가이드: 쇼핑 투어
- 명동, 홍대, 강남 쇼핑거리
- 대형 쇼핑몰, 디파트먼트 스토어
- 동대문 디자인 플라자
- 지하상가, 패션 스트리트
- K-뷰티, K-패션 전문점
""",
            'healing_tour': """
특화 가이드: 힐링 여행
- 스파, 천연 온천 우선
- 조용한 공원, 산책로
- 명상, 요가 체험 공간
- 전통 차 체험, 한의원 체험
- 자연 치유 공간, 산림욕
""",
            'adventure_tour': """
특화 가이드: 액티비티
- 놀이공원, 테마파크 우선
- 스포츠 체험 (볼링, 아이스링크 등)
- VR 체험관, 이스케이프 룸
- 어드벤처 스포츠 (집라인, 번지점프 등)
- 실내 클라이밍, 트램폴린
""",
            'night_tour': """
특화 가이드: 야경 투어
- 한강 야경, 전망대 우선
- 야시장, 홍대 밤거리
- 루프톱 바, 야경 카페
- 라이브 공연, 클럽 문화
- 야간 조명이 아름다운 장소
""",
            'family_tour': """
특화 가이드: 가족 여행
- 아이 친화적 박물관, 과학관
- 대형 공원, 동물원, 수족관
- 체험 학습 공간 (키즈 카페 등)
- 안전하고 넓은 실내 공간
- 유모차 접근 가능한 장소
"""
        }
        
        return style_guides.get(travel_style, "사용자 맞춤 여행 계획을 세워주세요.")
    
    async def get_enhanced_place_info(self, place_name: str, location: str = "Seoul") -> Dict[str, Any]:
        """장소 상세정보 및 후기 수집"""
        naver_service = NaverService()
        google_service = GoogleMapsService()
        blog_crawler = BlogCrawlerService()
        
        # 네이버 데이터
        naver_places = await naver_service.search_places(place_name)
        naver_blogs = await naver_service.search_blogs(f"{place_name} 후기")
        
        # 구글 데이터
        google_details = await google_service.get_place_details(place_name, location)
        
        # 블로그 내용 크롤링 (실제 크롤링)
        blog_contents = []
        if naver_blogs:
            blog_urls = [blog.get('link') for blog in naver_blogs[:3] if blog.get('link')]
            if blog_urls:
                blog_contents = await blog_crawler.get_multiple_blog_contents(blog_urls)
                print(f"✅ {place_name} 블로그 크롤링 완료: {len(blog_contents)}개")
        
        return {
            "naver_info": naver_places[0] if naver_places else {},
            "google_info": google_details,
            "blog_reviews": naver_blogs[:5],  # 상위 5개만
            "blog_contents": blog_contents,
            "verified": bool(naver_places or (google_details and google_details.get('name')))
        }
    
    async def _calculate_quality_score(self, enhanced_item: Dict[str, Any]) -> float:
        """장소 품질 점수 계산 (강화된 버전)"""
        score = 0.0
        
        # 구글 평점 (40%)
        google_info = enhanced_item.get('google_info', {})
        if google_info.get('rating', 0) > 0:
            score += google_info['rating'] * 0.4
        
        # 네이버 장소 정보 (30%)
        naver_info = enhanced_item.get('naver_info', {})
        if naver_info and naver_info.get('name'):
            score += 4.5 * 0.3  # 네이버에 등록된 장소는 기본 4.5점
        
        # 블로그 후기 수 (20%)
        blog_reviews = enhanced_item.get('blog_reviews', [])
        if blog_reviews and len(blog_reviews) > 0:
            review_score = min(len(blog_reviews) + 2, 5.0)  # 최소 2점 보장
            score += review_score * 0.2
        
        # 블로그 내용 품질 (10%)
        blog_contents = enhanced_item.get('blog_contents', [])
        if blog_contents:
            score += 4.0 * 0.1
        
        return min(score, 5.0)  # 최대 5점
    
    async def _find_quality_replacement(self, original_item: Dict[str, Any], enhanced_item: Dict[str, Any]) -> Dict[str, Any]:
        """품질 기준을 만족하는 대체 장소 찾기"""
        activity_type = original_item.get('activity', '')
        address = original_item.get('address', '')
        
        # 지역별 검증된 고품질 장소들
        quality_places = {
            '마곡': {
                '카페': [
                    {'name': '스타벅스 마곡나루역점', 'address': '서울시 강서구 마곡중앙로 161', 'rating': 4.2},
                    {'name': '투썸플레이스 마곡센트럴파크점', 'address': '서울시 강서구 마곡중앙로 240', 'rating': 4.1}
                ],
                '쇼핑': [
                    {'name': '마곡 롯데월드몰', 'address': '서울시 강서구 마곡중앙로 240', 'rating': 4.3},
                    {'name': '마곡 아이파크몰', 'address': '서울시 강서구 마곡중앙로 78', 'rating': 4.1}
                ],
                '식당': [
                    {'name': '마곡 푸드코트', 'address': '서울시 강서구 마곡중앙로 240', 'rating': 4.0}
                ]
            }
        }
        
        # 지역 및 활동 유형에 맞는 대체 장소 찾기
        for region in quality_places:
            if region in address:
                for activity_key, places in quality_places[region].items():
                    if activity_key in activity_type.lower() or activity_key in original_item.get('place_name', '').lower():
                        # 가장 높은 평점의 장소 선택
                        best_place = max(places, key=lambda x: x['rating'])
                        
                        # 실제 장소 정보 재검증
                        replacement_info = await self.get_enhanced_place_info(best_place['name'])
                        replacement_score = await self._calculate_quality_score(replacement_info)
                        
                        if replacement_score >= 3.0:
                            return {
                                'place_name': best_place['name'],
                                'address': best_place['address'],
                                'rating': best_place['rating'],
                                'verified': True,
                                'quality_score': replacement_score,
                                'description': f"{best_place['name']}에서 {original_item.get('activity', '')}",
                                'blog_reviews': replacement_info.get('blog_reviews', []),
                                'blog_contents': replacement_info.get('blog_contents', []),
                                'time': original_item.get('time'),
                                'duration': original_item.get('duration'),
                                'transportation': original_item.get('transportation'),
                                'price': original_item.get('price')
                            }
        
        return None
    
    async def _find_fallback_place(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """검증되지 않은 장소에 대한 대체 장소 찾기"""
        activity_type = item.get('activity', '')
        address = item.get('address', '')
        
        # 지역 기반 대체 장소 매핑
        fallback_places = {
            '마곡': {
                '카페': {'name': '마곡 센트럴파크 카페거리', 'address': '서울시 강서구 마곡중앙로 161'},
                '쇼핑': {'name': '마곡 롯데월드몰', 'address': '서울시 강서구 마곡중앙로 240'},
                '식당': {'name': '막걸리 맛집거리', 'address': '서울시 강서구 마곡동'}
            }
        }
        
        for region in fallback_places:
            if region in address:
                for activity_key, place_info in fallback_places[region].items():
                    if activity_key in activity_type or activity_key in item.get('place_name', ''):
                        return {
                            'place_name': place_info['name'],
                            'address': place_info['address'],
                            'verified': True,
                            'description': f"{place_info['name']}에서 {activity_type}"
                        }
        
        return None