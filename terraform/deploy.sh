#!/bin/bash
# 🚀 Travel Recommend Korea Lambda 배포 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 변수 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TERRAFORM_DIR="$SCRIPT_DIR"

echo -e "${GREEN}🚀 Travel Recommend Korea Lambda 배포 시작${NC}"
echo ""

# 1. Terraform 출력값 가져오기
echo -e "${YELLOW}📋 Terraform 출력값 확인 중...${NC}"
cd "$TERRAFORM_DIR"

if [ ! -f "terraform.tfstate" ]; then
    echo -e "${RED}❌ Terraform 상태 파일이 없습니다. 먼저 'terraform apply'를 실행하세요.${NC}"
    exit 1
fi

ECR_REPO_URL=$(terraform output -raw ecr_repository_url 2>/dev/null || echo "")
LAMBDA_FUNCTION_NAME=$(terraform output -raw lambda_function_name 2>/dev/null || echo "")
AWS_REGION=$(terraform output -raw aws_region 2>/dev/null || terraform output -json | jq -r '.aws_region.value // "ap-northeast-2"')

if [ -z "$ECR_REPO_URL" ] || [ -z "$LAMBDA_FUNCTION_NAME" ]; then
    echo -e "${RED}❌ Terraform 출력값을 가져올 수 없습니다.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ ECR 리포지토리: $ECR_REPO_URL${NC}"
echo -e "${GREEN}✓ Lambda 함수: $LAMBDA_FUNCTION_NAME${NC}"
echo -e "${GREEN}✓ AWS 리전: $AWS_REGION${NC}"
echo ""

# 2. ECR 로그인
echo -e "${YELLOW}🔐 ECR 로그인 중...${NC}"
ECR_REGISTRY=$(echo "$ECR_REPO_URL" | cut -d'/' -f1)
aws ecr get-login-password --region "$AWS_REGION" | \
    docker login --username AWS --password-stdin "$ECR_REGISTRY" || {
    echo -e "${RED}❌ ECR 로그인 실패${NC}"
    exit 1
}
echo -e "${GREEN}✓ ECR 로그인 성공${NC}"
echo ""

# 3. Docker 이미지 빌드 및 푸시 (linux/amd64 플랫폼으로 직접 푸시)
echo -e "${YELLOW}🐳 Docker 이미지 빌드 및 푸시 중 (linux/amd64)...${NC}"
cd "$PROJECT_ROOT"
docker buildx build --platform linux/amd64 -f Dockerfile.lambda -t "$ECR_REPO_URL:latest" --push . || {
    echo -e "${RED}❌ Docker 이미지 빌드/푸시 실패${NC}"
    exit 1
}
echo -e "${GREEN}✓ Docker 이미지 빌드 및 푸시 완료${NC}"
echo ""

# 4. 이미지 다이제스트 가져오기 (linux/amd64)
echo -e "${YELLOW}🔍 이미지 다이제스트 확인 중...${NC}"
REPO_NAME=$(echo "$ECR_REPO_URL" | cut -d'/' -f2)

# latest 태그의 manifest list 다이제스트 가져오기
MANIFEST_LIST_DIGEST=$(aws ecr describe-images \
    --repository-name "$REPO_NAME" \
    --region "$AWS_REGION" \
    --image-ids imageTag=latest \
    --query 'imageDetails[0].imageDigest' \
    --output text 2>/dev/null)

if [ -z "$MANIFEST_LIST_DIGEST" ] || [ "$MANIFEST_LIST_DIGEST" = "None" ]; then
    echo -e "${RED}❌ 이미지 다이제스트를 가져올 수 없습니다.${NC}"
    exit 1
fi

# manifest list에서 amd64 다이제스트 추출
MANIFEST_LIST=$(aws ecr batch-get-image \
    --repository-name "$REPO_NAME" \
    --region "$AWS_REGION" \
    --image-ids imageDigest="$MANIFEST_LIST_DIGEST" \
    --query 'images[0].imageManifest' \
    --output text 2>/dev/null)

if [ -z "$MANIFEST_LIST" ] || [ "$MANIFEST_LIST" = "None" ]; then
    echo -e "${RED}❌ Manifest list를 가져올 수 없습니다.${NC}"
    exit 1
fi

AMD64_DIGEST=$(echo "$MANIFEST_LIST" | python3 -c "
import sys, json
try:
    manifest = json.load(sys.stdin)
    if 'manifests' in manifest:
        for m in manifest['manifests']:
            if m.get('platform', {}).get('architecture') == 'amd64':
                print(m['digest'])
                break
except Exception as e:
    sys.stderr.write(f'Error: {e}\n')
    sys.exit(1)
" 2>/dev/null)

if [ -z "$AMD64_DIGEST" ]; then
    echo -e "${RED}❌ amd64 다이제스트를 찾을 수 없습니다.${NC}"
    exit 1
fi

IMAGE_URI="$ECR_REPO_URL@$AMD64_DIGEST"
echo -e "${GREEN}✓ amd64 다이제스트: $AMD64_DIGEST${NC}"
echo ""

# 7. Lambda 함수 업데이트
echo -e "${YELLOW}⚡ Lambda 함수 업데이트 중...${NC}"
echo -e "${YELLOW}   이미지 URI: $IMAGE_URI${NC}"
aws lambda update-function-code \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --image-uri "$IMAGE_URI" \
    --region "$AWS_REGION" > /dev/null || {
    echo -e "${RED}❌ Lambda 함수 업데이트 실패${NC}"
    echo -e "${YELLOW}⚠️  수동으로 업데이트를 시도하세요:${NC}"
    echo "   aws lambda update-function-code --function-name $LAMBDA_FUNCTION_NAME --image-uri $IMAGE_URI --region $AWS_REGION"
    exit 1
}
echo -e "${GREEN}✓ Lambda 함수 업데이트 완료${NC}"
echo ""

# 7. Function URL 확인
echo -e "${YELLOW}🔗 Function URL 확인 중...${NC}"
FUNCTION_URL=$(terraform output -raw lambda_function_url 2>/dev/null || echo "")
if [ -n "$FUNCTION_URL" ]; then
    echo -e "${GREEN}✓ Function URL: $FUNCTION_URL${NC}"
else
    echo -e "${YELLOW}⚠ Function URL이 비활성화되어 있습니다.${NC}"
fi
echo ""

echo -e "${GREEN}🎉 배포 완료!${NC}"
echo ""
echo -e "${GREEN}다음 단계:${NC}"
echo "  1. Lambda 함수가 업데이트될 때까지 몇 초 기다리세요"
echo "  2. Function URL로 접속하여 애플리케이션을 테스트하세요"
if [ -n "$FUNCTION_URL" ]; then
    echo "  3. URL: $FUNCTION_URL"
fi

