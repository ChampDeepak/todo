# Version constraints are not bureaucracy. Terraform providers make breaking
# changes between majors; an unpinned provider means the apply that worked today
# fails next month on a colleague's machine for reasons unrelated to your code.
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Local state tonight. In production this would be an S3 backend with a
  # DynamoDB lock table, so state is shared between engineers and two
  # simultaneous applies serialise instead of corrupting each other:
  #
  #   backend "s3" {
  #     bucket         = "my-tfstate"
  #     key            = "taskr/terraform.tfstate"
  #     region         = "ap-south-1"
  #     dynamodb_table = "terraform-locks"
  #     encrypt        = true
  #   }
}

provider "aws" {
  region = var.aws_region

  # Every resource gets these tags automatically. Untagged cloud resources are
  # how organisations end up with a bill nobody can attribute and servers
  # nobody dares delete.
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
