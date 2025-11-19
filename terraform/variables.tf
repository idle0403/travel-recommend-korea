variable "aws_region" {
  description = "AWS 리전"
  type        = string
  default     = "ap-northeast-2"
}

variable "environment" {
  description = "환경 (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "프로젝트 이름"
  type        = string
  default     = "travel-recommend-korea"
}

variable "lambda_memory_size" {
  description = "Lambda 함수 메모리 크기 (MB)"
  type        = number
  default     = 1024
}

variable "lambda_timeout" {
  description = "Lambda 함수 타임아웃 (초)"
  type        = number
  default     = 300
}

variable "lambda_reserved_concurrent_executions" {
  description = "Lambda 동시 실행 제한 (null이면 제한 없음)"
  type        = number
  default     = null
}

variable "function_url_cors_origins" {
  description = "Function URL CORS 허용 오리진"
  type        = list(string)
  default     = ["*"]
}

variable "function_url_cors_methods" {
  description = "Function URL CORS 허용 메서드"
  type        = list(string)
  default     = ["*"]
}

variable "function_url_cors_headers" {
  description = "Function URL CORS 허용 헤더"
  type        = list(string)
  default     = ["*"]
}

variable "enable_function_url" {
  description = "Function URL 활성화 여부"
  type        = bool
  default     = true
}

variable "function_url_auth_type" {
  description = "Function URL 인증 타입 (AWS_IAM 또는 NONE)"
  type        = string
  default     = "NONE"
  validation {
    condition     = contains(["AWS_IAM", "NONE"], var.function_url_auth_type)
    error_message = "function_url_auth_type은 AWS_IAM 또는 NONE이어야 합니다."
  }
}

variable "environment_variables" {
  description = "Lambda 환경 변수"
  type        = map(string)
  default     = {}
  sensitive   = true
}

variable "enable_xray_tracing" {
  description = "AWS X-Ray 추적 활성화"
  type        = bool
  default     = false
}

variable "log_retention_days" {
  description = "CloudWatch Logs 보관 기간 (일)"
  type        = number
  default     = 7
}

