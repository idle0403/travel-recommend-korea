#!/bin/bash
# 🔧 Terraform apply (refresh 스킵)

set -e

cd "$(dirname "$0")"

echo "⚠️  주의: 이 스크립트는 Terraform refresh를 스킵하고 apply만 실행합니다."
echo "   리소스가 이미 존재하는 경우에만 사용하세요."
echo ""

# refresh 스킵하고 apply 실행
terraform apply -refresh=false "$@"

