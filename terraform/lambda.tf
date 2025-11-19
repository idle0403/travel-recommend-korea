# Lambda 함수
resource "aws_lambda_function" "app" {
  function_name = "${var.project_name}-${var.environment}"
  description   = "Travel Recommend Korea - FastAPI 애플리케이션"
  role          = aws_iam_role.lambda_execution.arn
  package_type  = "Image"

  # ECR 이미지 URI
  # 태그 대신 다이제스트를 사용하여 멀티 아키텍처 인덱스 문제 방지
  # 최신 이미지 다이제스트를 사용하려면 terraform apply 전에 이미지를 푸시해야 합니다
  image_uri = "${aws_ecr_repository.app.repository_url}:latest"
  
  # 또는 다이제스트를 직접 사용:
  # image_uri = "${aws_ecr_repository.app.repository_url}@sha256:..."

  # Lambda 설정
  memory_size = var.lambda_memory_size
  timeout     = var.lambda_timeout

  # 동시 실행 제한
  reserved_concurrent_executions = var.lambda_reserved_concurrent_executions

  # 환경 변수
  environment {
    variables = var.environment_variables
  }

  # X-Ray 추적
  tracing_config {
    mode = var.enable_xray_tracing ? "Active" : "PassThrough"
  }

  # 이미지 설정
  image_config {
    # 컨테이너 진입점 (CMD에서 설정)
    # command = []
    # working_directory = "/var/task"
  }

  # 배포 설정
  publish = true

  # 태그
  tags = {
    Name = "${var.project_name}-lambda-${var.environment}"
  }

  # 이미지가 ECR에 존재해야 Lambda 함수를 생성할 수 있습니다.
  # 먼저 ECR 리포지토리를 생성한 후, Docker 이미지를 빌드하고 푸시한 다음
  # 이 리소스를 생성하세요.
  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_cloudwatch_log_group.lambda_logs,
    aws_ecr_repository.app
  ]

  # 이미지가 없을 때 에러를 방지하기 위해 lifecycle 설정
  lifecycle {
    ignore_changes = [image_uri]
  }
}

# Lambda 함수 버전 (자동 생성됨 - publish = true)
# 별도 별칭(alias)이 필요한 경우 추가 가능

# CloudWatch Logs 그룹
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${var.project_name}-lambda-logs-${var.environment}"
  }
}

# Lambda 함수 URL (선택사항)
resource "aws_lambda_function_url" "app" {
  count = var.enable_function_url ? 1 : 0

  function_name      = aws_lambda_function.app.function_name
  authorization_type = var.function_url_auth_type

  cors {
    allow_credentials = true
    allow_origins     = var.function_url_cors_origins
    allow_methods     = var.function_url_cors_methods
    allow_headers     = var.function_url_cors_headers
    expose_headers    = []
    max_age           = 86400
  }
}

