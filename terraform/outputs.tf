output "ecr_repository_url" {
  description = "ECR 리포지토리 URL"
  value       = aws_ecr_repository.app.repository_url
}

output "ecr_repository_arn" {
  description = "ECR 리포지토리 ARN"
  value       = aws_ecr_repository.app.arn
}

output "lambda_function_name" {
  description = "Lambda 함수 이름"
  value       = aws_lambda_function.app.function_name
}

output "lambda_function_arn" {
  description = "Lambda 함수 ARN"
  value       = aws_lambda_function.app.arn
}

output "lambda_function_url" {
  description = "Lambda Function URL"
  value       = var.enable_function_url ? aws_lambda_function_url.app[0].function_url : null
}

output "lambda_role_arn" {
  description = "Lambda 실행 역할 ARN"
  value       = aws_iam_role.lambda_execution.arn
}

output "cloudwatch_log_group_name" {
  description = "CloudWatch Logs 그룹 이름"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}

output "aws_region" {
  description = "AWS 리전"
  value       = var.aws_region
}

output "deployment_instructions" {
  description = "배포 지침"
  value = <<-EOT
    ============================================
    배포 방법:
    ============================================
    
    1. ECR 로그인:
       aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${aws_ecr_repository.app.repository_url}
    
    2. Docker 이미지 빌드 (프로젝트 루트에서):
       docker build -f Dockerfile.lambda -t ${var.project_name}:latest .
    
    3. 이미지 태그 지정:
       docker tag ${var.project_name}:latest ${aws_ecr_repository.app.repository_url}:latest
    
    4. ECR에 푸시:
       docker push ${aws_ecr_repository.app.repository_url}:latest
    
    5. Lambda 함수 업데이트 (자동 또는 수동):
       aws lambda update-function-code --function-name ${aws_lambda_function.app.function_name} --image-uri ${aws_ecr_repository.app.repository_url}:latest --region ${var.aws_region}
    
    6. Function URL 접속:
       ${var.enable_function_url ? aws_lambda_function_url.app[0].function_url : "Function URL이 비활성화되어 있습니다."}
    
    또는 배포 스크립트 사용:
       ./terraform/deploy.sh
    
    ============================================
  EOT
}

