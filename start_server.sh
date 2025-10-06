#!/bin/bash

# 🇰🇷 한국 여행 플래너 서버 시작 스크립트

echo "🚀 한국 여행 플래너 서버를 시작합니다..."

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 가상환경 확인
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}⚠️  가상환경을 활성화하세요: source ../bin/activate${NC}"
    exit 1
fi

# 의존성 설치
echo -e "${BLUE}📦 의존성 설치 중...${NC}"
pip install -r requirements.txt

# 서버 시작
echo -e "${GREEN}🌐 서버 시작 중...${NC}"
echo -e "${BLUE}📍 접속 주소: http://localhost:8000${NC}"
echo -e "${BLUE}📚 API 문서: http://localhost:8000/docs${NC}"
echo -e "${YELLOW}⏹️  종료하려면 Ctrl+C를 누르세요${NC}"

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000