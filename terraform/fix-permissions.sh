#!/bin/bash
# 🔧 Terraform 권한 문제 해결 스크립트

set -e

echo "🔍 AWS 인증 정보 확인 중..."
aws sts get-caller-identity || {
    echo "❌ AWS 인증 실패"
    echo "AWS SSO 로그인이 필요합니다:"
    echo "  aws sso login"
    exit 1
}

echo "✅ AWS 인증 확인 완료"
echo ""

echo "🔍 리소스 접근 테스트 중..."

# ECR 접근 테스트
echo -n "  ECR 리포지토리: "
aws ecr describe-repositories --repository-names travel-recommend-korea-dev --region ap-northeast-2 > /dev/null 2>&1 && echo "✅" || echo "❌"

# IAM 역할 접근 테스트
echo -n "  IAM 역할: "
aws iam get-role --role-name travel-recommend-korea-lambda-execution-dev > /dev/null 2>&1 && echo "✅" || echo "❌"

# CloudWatch Logs 접근 테스트
echo -n "  CloudWatch Logs: "
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/travel-recommend-korea-dev --region ap-northeast-2 > /dev/null 2>&1 && echo "✅" || echo "❌"

echo ""
echo "💡 해결 방법:"
echo "1. AWS SSO 재로그인: aws sso login"
echo "2. 또는 관리자에게 다음 권한 요청:"
echo "   - ecr:DescribeRepositories"
echo "   - iam:GetRole"
echo "   - logs:DescribeLogGroups"

