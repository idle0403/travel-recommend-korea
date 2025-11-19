# Lambda 실행 역할
resource "aws_iam_role" "lambda_execution" {
  name = "${var.project_name}-lambda-execution-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-lambda-execution-role-${var.environment}"
  }
}

# 기본 Lambda 실행 정책 (CloudWatch Logs)
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# X-Ray 추적 정책 (선택사항)
resource "aws_iam_role_policy_attachment" "lambda_xray" {
  count = var.enable_xray_tracing ? 1 : 0

  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}

# 추가 권한이 필요한 경우 여기에 정책 추가
# 예: Secrets Manager 접근, VPC 접근 등
# 
# 현재는 추가 권한이 필요하지 않으므로 이 정책은 비활성화되어 있습니다.
# 필요시 아래 주석을 해제하고 사용하세요.
#
# resource "aws_iam_role_policy" "lambda_additional" {
#   name = "${var.project_name}-lambda-additional-${var.environment}"
#   role = aws_iam_role.lambda_execution.id
#
#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       # Secrets Manager 접근 (환경 변수를 Secrets Manager에서 가져오는 경우)
#       {
#         Effect = "Allow"
#         Action = [
#           "secretsmanager:GetSecretValue",
#           "secretsmanager:DescribeSecret"
#         ]
#         Resource = "arn:aws:secretsmanager:${var.aws_region}:*:secret:${var.project_name}/*"
#       },
#       # VPC 접근 (ElastiCache Redis 사용 시)
#       {
#         Effect = "Allow"
#         Action = [
#           "ec2:CreateNetworkInterface",
#           "ec2:DescribeNetworkInterfaces",
#           "ec2:DeleteNetworkInterface"
#         ]
#         Resource = "*"
#       }
#     ]
#   })
# }

