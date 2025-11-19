# 🔧 Terraform 권한 에러 해결 가이드

## 에러: "explicit deny in an identity-based policy"

이 에러는 IAM 정책에서 특정 리소스에 대한 접근이 명시적으로 거부되었을 때 발생합니다.

## 가능한 원인

1. **AWS SSO 세션 만료**
   - SSO 세션이 만료되어 권한이 없어짐

2. **권한 정책 변경**
   - 관리자가 IAM 정책을 변경하여 접근 제한

3. **SCP (Service Control Policy) 제한**
   - 조직 레벨에서 특정 리소스 접근 제한

4. **리소스 태그 정책**
   - 특정 태그가 있는 리소스에 대한 접근 제한

## 해결 방법

### 1단계: AWS SSO 재로그인

```bash
# AWS SSO 로그인
aws sso login --profile your-profile

# 또는
aws configure sso
```

### 2단계: 현재 인증 정보 확인

```bash
aws sts get-caller-identity
```

다음 정보를 확인:
- Account ID가 올바른지
- Role이 올바른지
- 세션이 유효한지

### 3단계: 특정 리소스 접근 테스트

```bash
# ECR 접근 테스트
aws ecr describe-repositories --repository-names travel-recommend-korea-dev --region ap-northeast-2

# IAM 역할 접근 테스트
aws iam get-role --role-name travel-recommend-korea-lambda-execution-dev

# CloudWatch Logs 접근 테스트
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/travel-recommend-korea-dev --region ap-northeast-2
```

### 4단계: Terraform 상태 확인

리소스가 이미 존재하는 경우, Terraform 상태를 확인:

```bash
cd terraform
terraform state list
```

### 5단계: 관리자에게 문의

위 방법으로 해결되지 않으면:

1. **필요한 권한 확인**
   - `ecr:DescribeRepositories`
   - `iam:GetRole`
   - `logs:DescribeLogGroups`

2. **리소스 ARN 확인**
   - ECR: `arn:aws:ecr:ap-northeast-2:391183348418:repository/travel-recommend-korea-dev`
   - IAM: `arn:aws:iam::391183348418:role/travel-recommend-korea-lambda-execution-dev`
   - Logs: `arn:aws:logs:ap-northeast-2:391183348418:log-group:/aws/lambda/travel-recommend-korea-dev`

3. **관리자에게 다음 권한 요청**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "ecr:DescribeRepositories",
           "ecr:GetRepositoryPolicy",
           "ecr:ListImages",
           "iam:GetRole",
           "iam:GetRolePolicy",
           "logs:DescribeLogGroups",
           "logs:DescribeLogStreams"
         ],
         "Resource": [
           "arn:aws:ecr:ap-northeast-2:391183348418:repository/travel-recommend-korea-dev",
           "arn:aws:iam::391183348418:role/travel-recommend-korea-lambda-execution-dev",
           "arn:aws:logs:ap-northeast-2:391183348418:log-group:/aws/lambda/travel-recommend-korea-dev"
         ]
       }
     ]
   }
   ```

## 임시 해결책: Terraform 상태 무시

리소스가 이미 존재하고 읽기만 필요한 경우:

```bash
# 특정 리소스만 import (이미 존재하는 경우)
terraform import aws_ecr_repository.app travel-recommend-korea-dev
terraform import aws_iam_role.lambda_execution travel-recommend-korea-lambda-execution-dev
terraform import aws_cloudwatch_log_group.lambda_logs /aws/lambda/travel-recommend-korea-dev
```

또는 Terraform 상태를 새로 생성:

```bash
# 기존 상태 백업
cp terraform.tfstate terraform.tfstate.backup

# 상태 파일 삭제 후 재생성 (주의: 리소스가 이미 존재하는 경우)
rm terraform.tfstate
terraform init
terraform import ...
```

## 참고

- 이 에러는 읽기 권한 문제이므로, 리소스 생성/수정은 가능할 수 있습니다
- `terraform plan`만 실패하고 `terraform apply`는 성공할 수 있습니다
- 하지만 권한 문제를 해결하는 것이 권장됩니다

