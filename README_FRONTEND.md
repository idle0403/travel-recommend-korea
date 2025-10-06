# 🇰🇷 스마트 한국 여행 플래너 - 프론트엔드

AI 기반 맞춤형 한국 여행 계획 생성 웹 애플리케이션

## ✨ 주요 기능

### 🎯 핵심 기능
- **AI 여행 계획 생성**: 자연어 프롬프트로 맞춤형 여행 계획 생성
- **시간별 상세 일정**: 구체적인 시간과 장소가 포함된 타임라인
- **지도 최적 동선**: Google Maps를 활용한 최적 경로 표시
- **장소 검증**: 실제 존재하는 맛집/관광지 확인 및 리뷰 링크 제공
- **Notion 자동 저장**: 생성된 계획을 Notion에 자동 저장 및 성공/실패 알림

### 🌟 사용자 경험 개선사항
- **실시간 피드백**: 로딩 상태, 진행률, 성공/실패 알림
- **인터랙티브 지도**: 클릭 가능한 마커와 최적화된 경로
- **모달 상세보기**: 각 장소의 상세 정보를 모달로 표시
- **반응형 디자인**: 모바일/태블릿/데스크톱 최적화
- **직관적 UI**: 아이콘과 색상을 활용한 시각적 구분

## 🚀 빠른 시작

### 1️⃣ 서버 실행
```bash
# 간편 실행
./start_server.sh

# 또는 수동 실행
source ../bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### 2️⃣ 웹 접속
- **메인 페이지**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3️⃣ 사용법
1. 여행 도시 선택 (서울, 부산, 제주 등)
2. 여행 기간 설정 (1-24시간)
3. 여행 요청사항 입력 (예: "맛집 위주로 가족 여행")
4. "AI 여행 계획 생성" 버튼 클릭
5. 결과 확인 및 Notion 저장 상태 확인

## 🎨 UI/UX 특징

### 📱 반응형 레이아웃
```
Desktop (lg+):  [Timeline & Details] | [Map & Status]
Mobile:         [Timeline & Details]
                [Map & Status]
```

### 🎯 핵심 컴포넌트
- **타임라인**: 시간순 일정 표시, 클릭으로 상세보기
- **지도**: Google Maps 기반 최적 경로 표시
- **장소 상세**: 검증된 정보, 평점, 리뷰 링크
- **Notion 상태**: 실시간 저장 진행률 및 결과

### 🎨 디자인 시스템
- **색상**: Blue/Indigo 그라데이션 (신뢰감)
- **아이콘**: Font Awesome (직관적 인식)
- **애니메이션**: 부드러운 전환 효과
- **피드백**: Toast 알림, 로딩 스피너

## 🔧 기술 스택

### Frontend
- **HTML5**: 시맨틱 마크업
- **Tailwind CSS**: 유틸리티 기반 스타일링
- **Vanilla JavaScript**: 경량화된 인터랙션
- **Google Maps API**: 지도 및 경로 표시

### Backend
- **FastAPI**: 고성능 Python 웹 프레임워크
- **Pydantic**: 데이터 검증 및 직렬화
- **CORS**: 크로스 오리진 요청 지원

## 📊 API 응답 구조

### 여행 계획 응답
```json
{
  "plan_id": "uuid",
  "title": "AI 추천 여행 계획",
  "summary": "맞춤형 여행 계획 요약",
  "itinerary": [
    {
      "time": "09:00",
      "name": "경복궁",
      "activity": "궁궐 관람",
      "location": "서울시 종로구 사직로 161",
      "duration": "2시간",
      "description": "조선왕조의 정궁",
      "rating": 4.5,
      "price": "3,000원",
      "lat": 37.5796,
      "lng": 126.9770
    }
  ],
  "total_cost": 50000,
  "notion_url": "https://notion.so/...",
  "notion_saved": true,
  "weather_info": {"condition": "맑음", "temperature": "18°C"}
}
```

## 🧪 테스트 및 검증

### 자동 테스트 실행
```bash
python test_frontend.py
```

### 테스트 항목
- ✅ 프론트엔드 파일 존재 확인
- ✅ HTML 구조 검증
- ✅ JavaScript 함수 검증
- ✅ API 엔드포인트 테스트
- ✅ 응답 데이터 구조 확인

### 수동 테스트 체크리스트
- [ ] 폼 입력 및 제출
- [ ] 로딩 상태 표시
- [ ] 타임라인 렌더링
- [ ] 지도 경로 표시
- [ ] 장소 모달 팝업
- [ ] Notion 저장 알림
- [ ] 모바일 반응형

## 🚨 문제 해결

### 일반적인 문제

#### 지도가 표시되지 않음
```bash
# Google Maps API 키 확인
# frontend/index.html의 API 키가 유효한지 확인
```

#### API 연결 실패
```bash
# 서버 실행 상태 확인
curl http://localhost:8000/health

# CORS 오류 시 브라우저 콘솔 확인
```

#### Notion 저장 실패
```bash
# 환경변수 확인
echo $NOTION_TOKEN
echo $NOTION_DATABASE_ID
```

### 개발자 도구 활용
1. **Network 탭**: API 요청/응답 확인
2. **Console 탭**: JavaScript 오류 확인
3. **Elements 탭**: DOM 구조 및 스타일 확인

## 🔮 향후 개발 계획

### 단기 계획
- [ ] 실시간 채팅 지원 (WebSocket)
- [ ] 사용자 계정 및 히스토리
- [ ] 소셜 공유 기능
- [ ] PWA 지원 (오프라인 사용)

### 장기 계획
- [ ] 모바일 앱 (React Native)
- [ ] 다국어 지원
- [ ] AI 음성 인터페이스
- [ ] 증강현실(AR) 가이드

## 📈 성능 최적화

### 현재 최적화
- **지연 로딩**: 지도 초기화 지연
- **캐싱**: API 응답 캐싱
- **압축**: 정적 파일 압축
- **CDN**: 외부 라이브러리 CDN 사용

### 추가 최적화 가능
- **이미지 최적화**: WebP 포맷 사용
- **코드 분할**: 모듈별 분리
- **서비스 워커**: 캐싱 전략
- **번들링**: Webpack/Vite 도입

---

**🎯 이제 브라우저에서 http://localhost:8000 접속하여 AI 기반 한국 여행 계획을 생성해보세요!**

*Made with ❤️ using FastAPI, Tailwind CSS, and Google Maps API*