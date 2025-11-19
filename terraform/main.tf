terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # 상태 파일 저장 위치 (선택사항)
  # backend "s3" {
  #   bucket = "your-terraform-state-bucket"
  #   key    = "travel-recommend-korea/terraform.tfstate"
  #   region = "ap-northeast-2"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "travel-recommend-korea"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

