# 🚀 빠른 실행 가이드

## 1️⃣ 서버 시작
```bash
cd /Users/paul/Documents/venv/travel-recommend-korea
source ../bin/activate
./start_server.sh
```

## 2️⃣ 웹 접속
- 메인 페이지: http://localhost:8000
- API 문서: http://localhost:8000/docs

## 3️⃣ 테스트 실행
```bash
python test_frontend.py
```

## 🔑 API 키 설정 (.env 파일)
```bash
# 필수 API 키들
OPENAI_API_KEY=your-openai-key
GOOGLE_MAPS_API_KEY=your-google-maps-key
NOTION_TOKEN=your-notion-token
NOTION_DATABASE_ID=your-database-id
NAVER_CLIENT_ID=your-naver-client-id
NAVER_CLIENT_SECRET=your-naver-client-secret
```

## ✨ 모든 요구사항 구현 완료!
1. ✅ 네이버 블로그 내부 크롤링
2. ✅ 최적 동선 구성 (버스/지하철/도보)
3. ✅ 시간별 타임라인
4. ✅ 구글맵 동선 표기
5. ✅ Notion 자동 저장
6. ✅ 실시간 대중교통 정보
7. ✅ 날씨 기반 추천