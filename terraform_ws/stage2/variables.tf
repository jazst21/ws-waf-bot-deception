# Reference the parent terraform state
data "terraform_remote_state" "workshop" {
  backend = "local"
  config = {
    path = "../terraform.tfstate"
  }
}

# Use the same variables from parent
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "bot-deception"
}

# Local values from parent state
locals {
  name_prefix = "bot-deception-dev"  # Hardcoded since not in outputs
  common_tags = {
    Environment = "dev"
    Project     = "bot-deception"
  }
  backend_source_dir = "${path.module}/../../source/backend"
}
