# 🚀 배포 가이드

Lambda 함수는 ECR 이미지가 있어야 생성할 수 있습니다. 다음 단계를 따라 배포하세요.

## 1단계: ECR 리포지토리만 먼저 생성

Lambda 함수를 제외하고 나머지 리소스만 생성:

```bash
cd terraform
terraform apply -target=aws_ecr_repository.app -target=aws_iam_role.lambda_execution -target=aws_cloudwatch_log_group.lambda_logs
```

또는 ECR만 생성:

```bash
terraform apply -target=aws_ecr_repository.app
```

## 2단계: Docker 이미지 빌드 및 푸시

```bash
# ECR 로그인
ECR_REPO_URL=$(terraform output -raw ecr_repository_url)
ECR_REGISTRY=$(echo "$ECR_REPO_URL" | cut -d'/' -f1)
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin "$ECR_REGISTRY"

# 이미지 빌드 (프로젝트 루트에서)
cd ..
docker build -f Dockerfile.lambda -t travel-recommend-korea:latest .

# 이미지 태그 지정
docker tag travel-recommend-korea:latest "$ECR_REPO_URL:latest"

# ECR에 푸시
docker push "$ECR_REPO_URL:latest"
```

## 3단계: 나머지 리소스 생성 (Lambda 함수 포함)

이미지가 ECR에 있으므로 이제 Lambda 함수를 생성할 수 있습니다:

```bash
cd terraform
terraform apply
```

## 또는: 자동 배포 스크립트 사용

위 단계를 자동화한 스크립트를 사용할 수도 있습니다. 하지만 먼저 ECR 리포지토리가 생성되어 있어야 합니다.

```bash
# 1. ECR 리포지토리만 먼저 생성
terraform apply -target=aws_ecr_repository.app

# 2. 배포 스크립트 실행
./terraform/deploy.sh
```

## 문제 해결

### 에러: "Source image does not exist"

이 에러는 Lambda 함수를 생성할 때 ECR 이미지가 없어서 발생합니다.

**해결 방법:**
1. 위의 1-3단계를 순서대로 실행하세요
2. 또는 Lambda 함수를 제외하고 먼저 생성:
   ```bash
   terraform apply -target=aws_ecr_repository.app -target=aws_iam_role.lambda_execution -target=aws_cloudwatch_log_group.lambda_logs
   ```
3. 이미지를 푸시한 후 Lambda 함수 생성:
   ```bash
   terraform apply -target=aws_lambda_function.app
   ```

### 에러: "MalformedPolicyDocument"

IAM 정책의 Statement 배열이 비어있어서 발생합니다. 이미 수정되었으므로 다시 시도하세요.

