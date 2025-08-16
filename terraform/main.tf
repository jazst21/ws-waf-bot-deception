# Enhanced main.tf that builds SPA and deploys everything
# This replaces the need for external deployment scripts

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.8"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Local values
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
  
  # Paths - React frontend in standard location
  frontend_source_dir = "${path.module}/../source/frontend"
  backend_source_dir  = "${path.module}/../source/backend"
  frontend_build_dir  = "${path.module}/../source/frontend/dist"
}

# Random suffix for unique resource names
resource "random_id" "suffix" {
  byte_length = 4
}

# Random suffix for Lambda permission
resource "random_id" "lambda_permission_suffix" {
  byte_length = 4
}

# Random suffix for CloudFront function
resource "random_id" "cloudfront_function_suffix" {
  byte_length = 4
}

# =============================================================================
# VPC AND NETWORKING
# =============================================================================

# Create VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, {
    Name = var.vpc_name
  })
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "${var.vpc_name}-igw"
  })
}

# Get availability zones
data "aws_availability_zones" "available" {
  state = "available"
  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

# Public subnets
resource "aws_subnet" "public" {
  count = var.public_subnet_count

  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name = "${var.vpc_name}-public-${count.index + 1}"
    Type = "Public"
  })
}

# Private subnets
resource "aws_subnet" "private" {
  count = var.private_subnet_count

  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + var.public_subnet_count)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = merge(local.common_tags, {
    Name = "${var.vpc_name}-private-${count.index + 1}"
    Type = "Private"
  })
}

# Route table for public subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(local.common_tags, {
    Name = "${var.vpc_name}-public-rt"
  })
}

# Associate public subnets with public route table
resource "aws_route_table_association" "public" {
  count = var.public_subnet_count

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# NAT Gateway for private subnets (enabled by default for internet access)
resource "aws_eip" "nat" {
  count = var.enable_nat_gateway ? 1 : 0

  domain = "vpc"
  depends_on = [aws_internet_gateway.main]

  tags = merge(local.common_tags, {
    Name = "${var.vpc_name}-nat-eip"
  })
}

resource "aws_nat_gateway" "main" {
  count = var.enable_nat_gateway ? 1 : 0

  allocation_id = aws_eip.nat[0].id
  subnet_id     = aws_subnet.public[0].id

  tags = merge(local.common_tags, {
    Name = "${var.vpc_name}-nat-gw"
  })

  depends_on = [aws_internet_gateway.main]
}

# Route table for private subnets
resource "aws_route_table" "private" {
  count = var.enable_nat_gateway ? 1 : 0

  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[0].id
  }

  tags = merge(local.common_tags, {
    Name = "${var.vpc_name}-private-rt"
  })
}

# Associate private subnets with private route table
resource "aws_route_table_association" "private" {
  count = var.enable_nat_gateway ? var.private_subnet_count : 0

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[0].id
}

# Select subnets for ALB (use public subnets)
locals {
  # Use public subnets for ALB (needs internet access)
  selected_subnets = aws_subnet.public[*].id
}

# =============================================================================
# FRONTEND BUILD PROCESS
# =============================================================================

# Check if Node.js and npm are available
data "external" "check_nodejs" {
  program = ["bash", "-c", <<-EOT
    if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
      echo '{"nodejs_available": "true", "node_version": "'$(node --version)'", "npm_version": "'$(npm --version)'"}'
    else
      echo '{"nodejs_available": "false", "node_version": "", "npm_version": ""}'
    fi
  EOT
  ]
}

# Install frontend dependencies
resource "null_resource" "frontend_dependencies" {
  triggers = {
    package_json_hash = filemd5("${local.frontend_source_dir}/package.json")
    nodejs_available  = data.external.check_nodejs.result.nodejs_available
  }

  provisioner "local-exec" {
    command     = "npm install"
    working_dir = local.frontend_source_dir
  }

  # Only run if Node.js is available
  count = data.external.check_nodejs.result.nodejs_available == "true" ? 1 : 0
}

# Create dynamic environment configuration for production build
resource "local_file" "frontend_env_production" {
  filename = "${local.frontend_source_dir}/.env.production.local"
  content = templatefile("${path.module}/frontend-env.tpl", {
    api_base_url      = "/api"  # Relative path since same CloudFront domain
    cloudfront_domain = "PLACEHOLDER"  # Will be updated after CloudFront creation
    node_env         = "production"
    enable_debug     = "false"
    aws_region       = var.aws_region
  })

  depends_on = [null_resource.frontend_dependencies]
}

# Build frontend
resource "null_resource" "frontend_build" {
  triggers = {
    # Rebuild when source files change
    source_hash = sha256(join("", [
      for f in fileset("${local.frontend_source_dir}/src", "**/*") :
      filesha256("${local.frontend_source_dir}/src/${f}")
    ]))
    # Include root HTML file
    index_html_hash   = fileexists("${local.frontend_source_dir}/index.html") ? filemd5("${local.frontend_source_dir}/index.html") : ""
    package_json_hash = filemd5("${local.frontend_source_dir}/package.json")
    vite_config_hash  = filemd5("${local.frontend_source_dir}/vite.config.js")
    env_file_hash     = local_file.frontend_env_production.content_md5
  }

  provisioner "local-exec" {
    command     = "npm run build"
    working_dir = local.frontend_source_dir
  }

  depends_on = [
    null_resource.frontend_dependencies,
    local_file.frontend_env_production
  ]

  # Only run if Node.js is available
  count = data.external.check_nodejs.result.nodejs_available == "true" ? 1 : 0
}

# =============================================================================
# S3 BUCKETS
# =============================================================================

# S3 Bucket for Frontend (Private)
resource "aws_s3_bucket" "frontend" {
  bucket        = "${local.name_prefix}-frontend-${random_id.suffix.hex}"
  force_destroy = true  # Allow destruction even with objects

  tags = merge(local.common_tags, {
    Name = "Bot Deception Frontend Bucket"
  })
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  versioning_configuration {
    status = "Disabled"
  }
}

# S3 Bucket for Fake Webpages
resource "aws_s3_bucket" "fake_webpages" {
  bucket        = "${local.name_prefix}-fake-webpages-${random_id.suffix.hex}"
  force_destroy = true  # Allow destruction even with objects

  tags = merge(local.common_tags, {
    Name = "Bot Deception Fake Webpages Bucket"
  })
}

resource "aws_s3_bucket_public_access_block" "fake_webpages" {
  bucket = aws_s3_bucket.fake_webpages.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "fake_webpages" {
  bucket = aws_s3_bucket.fake_webpages.id
  versioning_configuration {
    status = "Disabled"
  }
}

# =============================================================================
# FRONTEND DEPLOYMENT TO S3
# =============================================================================

# Upload frontend files to S3 using AWS CLI sync
resource "null_resource" "frontend_upload" {
  # Trigger re-upload when build changes or bucket changes
  triggers = {
    build_hash = null_resource.frontend_build[0].id
    bucket_id  = aws_s3_bucket.frontend.id
  }

  provisioner "local-exec" {
    command = <<-EOT
      # Only upload if Node.js is available and build directory exists
      if [ "${data.external.check_nodejs.result.nodejs_available}" = "true" ] && [ -d "${local.frontend_build_dir}" ]; then
        echo "🚀 Uploading frontend files to S3..."
        
        # Sync files with appropriate metadata and cache headers
        aws s3 sync "${local.frontend_build_dir}" "s3://${aws_s3_bucket.frontend.id}/" \
          --delete \
          --exact-timestamps \
          --metadata-directive REPLACE \
          --cache-control "public, max-age=86400" \
          --exclude "*.html" \
          --exclude "*.json"
        
        # Upload HTML files with no-cache headers
        aws s3 sync "${local.frontend_build_dir}" "s3://${aws_s3_bucket.frontend.id}/" \
          --exclude "*" \
          --include "*.html" \
          --metadata-directive REPLACE \
          --cache-control "no-cache, no-store, must-revalidate" \
          --content-type "text/html"
        
        # Upload JSON files with appropriate headers
        aws s3 sync "${local.frontend_build_dir}" "s3://${aws_s3_bucket.frontend.id}/" \
          --exclude "*" \
          --include "*.json" \
          --metadata-directive REPLACE \
          --cache-control "public, max-age=86400" \
          --content-type "application/json"
        
        # Set content types for CSS and JS files (immutable cache for hashed files)
        aws s3 sync "${local.frontend_build_dir}" "s3://${aws_s3_bucket.frontend.id}/" \
          --exclude "*" \
          --include "*.css" \
          --metadata-directive REPLACE \
          --cache-control "public, max-age=31536000, immutable" \
          --content-type "text/css"
        
        aws s3 sync "${local.frontend_build_dir}" "s3://${aws_s3_bucket.frontend.id}/" \
          --exclude "*" \
          --include "*.js" \
          --metadata-directive REPLACE \
          --cache-control "public, max-age=31536000, immutable" \
          --content-type "application/javascript"
        
        echo "✅ Frontend upload completed successfully"
      else
        echo "⚠️  Skipping frontend upload - Node.js not available or build directory missing"
      fi
    EOT
  }

  depends_on = [
    null_resource.frontend_build,
    aws_s3_bucket.frontend,
    aws_s3_bucket_public_access_block.frontend
  ]
}

# =============================================================================
# CLOUDFRONT ORIGIN ACCESS CONTROL
# =============================================================================

resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${local.name_prefix}-frontend-oac"
  description                       = "OAC for Bot Deception Frontend"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
  
  lifecycle {
    create_before_destroy = true
    ignore_changes = [
      name,  # Ignore name changes to prevent recreation
    ]
  }
}

resource "aws_cloudfront_origin_access_control" "fake_webpages" {
  name                              = "${local.name_prefix}-fake-webpages-oac"
  description                       = "OAC for Bot Deception Fake Webpages"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
  
  lifecycle {
    create_before_destroy = true
    ignore_changes = [
      name,  # Ignore name changes to prevent recreation
    ]
  }
}

# =============================================================================
# DYNAMODB TABLE FOR COMMENTS STORAGE
# =============================================================================

# DynamoDB table for comments storage
resource "aws_dynamodb_table" "comments" {
  name           = "${local.name_prefix}-comments"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  global_secondary_index {
    name               = "timestamp-index"
    hash_key           = "timestamp"
    projection_type    = "ALL"
  }

  tags = merge(local.common_tags, {
    Name = "Bot Deception Comments Table"
  })
  
  lifecycle {
    create_before_destroy = true
    ignore_changes = [
      name,  # Ignore name changes to prevent recreation
    ]
  }
}



# =============================================================================
# LAMBDA FUNCTION FOR BACKEND API
# =============================================================================

# IAM Role for Lambda
resource "aws_iam_role" "lambda_api" {
  name = "${local.name_prefix}-lambda-api-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "lambda_api" {
  name = "${local.name_prefix}-lambda-api-policy"
  role = aws_iam_role.lambda_api.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.comments.arn,
          "${aws_dynamodb_table.comments.arn}/index/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_api_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_api.name
}

# =============================================================================
# PYTHON LAMBDA FUNCTION FOR API BACKEND
# =============================================================================

# Package API Lambda function
data "archive_file" "lambda_api" {
  type        = "zip"
  output_path = "${path.module}/lambda-api.zip"
  source_file = "${local.backend_source_dir}/api_lambda.py"
}

# Package Fake Page Lambda function
data "archive_file" "lambda_fake_page" {
  type        = "zip"
  output_path = "${path.module}/lambda-fake-page.zip"
  source_file = "${local.backend_source_dir}/fake_page_lambda.py"
}

# API Lambda function for bot deception API
resource "aws_lambda_function" "api" {
  filename         = data.archive_file.lambda_api.output_path
  function_name    = "${local.name_prefix}-api"
  role            = aws_iam_role.lambda_api.arn
  handler         = "api_lambda.lambda_handler"
  source_code_hash = data.archive_file.lambda_api.output_base64sha256
  runtime         = "python3.11"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.comments.name
      # Python-specific optimizations
      PYTHONPATH = "/var/runtime"
    }
  }

  # Python Lambda optimizations
  # reserved_concurrent_executions = 10  # Commented out to avoid account limits
  
  tags = merge(local.common_tags, {
    Name = "Bot Deception API Lambda"
    Runtime = "python3.11"
    Language = "Python"
  })
}

# Fake Page Generator Lambda function
resource "aws_lambda_function" "fake_page_generator" {
  filename         = data.archive_file.lambda_fake_page.output_path
  function_name    = "${local.name_prefix}-fake-page-generator"
  role            = aws_iam_role.lambda_fake_pages.arn
  handler         = "fake_page_lambda.lambda_handler"
  source_code_hash = data.archive_file.lambda_fake_page.output_base64sha256
  runtime         = "python3.11"
  timeout         = 300  # 5 minutes for page generation
  memory_size     = 1024  # More memory for content generation

  environment {
    variables = {
      S3_BUCKET_NAME = aws_s3_bucket.fake_webpages.bucket
      # Python-specific optimizations
      PYTHONPATH = "/var/runtime"
    }
  }

  # Prevent runaway costs
  # reserved_concurrent_executions = 5  # Commented out to avoid account limits
  
  tags = merge(local.common_tags, {
    Name = "Bot Deception Fake Page Generator Lambda"
    Runtime = "python3.11"
    Language = "Python"
  })
}

resource "aws_cloudwatch_log_group" "lambda_api" {
  name              = "/aws/lambda/${aws_lambda_function.api.function_name}"
  retention_in_days = var.log_retention_days
  tags              = local.common_tags
}

resource "aws_cloudwatch_log_group" "lambda_fake_page_generator" {
  name              = "/aws/lambda/${aws_lambda_function.fake_page_generator.function_name}"
  retention_in_days = var.log_retention_days
  tags              = local.common_tags

  lifecycle {
    ignore_changes = [name]
  }
}

# =============================================================================
# =============================================================================
# APPLICATION LOAD BALANCER (Internal)
# =============================================================================

# Security Group for Public ALB (temporarily allow public access for testing)
resource "aws_security_group" "public_alb" {
  name_prefix = "${local.name_prefix}-public-alb-"
  vpc_id      = aws_vpc.main.id

  # Allow HTTP from anywhere for testing
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTP from anywhere for testing"
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "Bot Deception Public ALB Security Group"
  })
}

# Security Group for Timeout ALB (NO INBOUND RULES - causes timeouts)
resource "aws_security_group" "timeout_alb" {
  name_prefix = "${local.name_prefix}-timeout-alb-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for timeout ALB (no inbound rules to cause timeouts)"

  # NO INGRESS RULES - this causes connection timeouts for bots

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "Bot Deception Timeout ALB Security Group"
  })
}

# Public ALB
resource "aws_lb" "public" {
  name               = "${local.name_prefix}-public-alb"
  internal           = false
  load_balancer_type = "application"
  subnets            = local.selected_subnets
  security_groups    = [aws_security_group.public_alb.id]

  enable_deletion_protection = false

  tags = merge(local.common_tags, {
    Name = "Bot Deception Public ALB"
  })
}

# Timeout ALB (for bot redirection - causes timeouts due to no inbound rules)
resource "aws_lb" "timeout" {
  name               = "${local.name_prefix}-timeout-alb"
  internal           = false
  load_balancer_type = "application"
  subnets            = local.selected_subnets
  security_groups    = [aws_security_group.timeout_alb.id]

  enable_deletion_protection = false

  tags = merge(local.common_tags, {
    Name = "Bot Deception Timeout ALB"
  })
}

# Target Group for Lambda
resource "aws_lb_target_group" "lambda" {
  name        = "${local.name_prefix}-lambda-tg"
  target_type = "lambda"

  tags = local.common_tags
}

# Lambda permission for ALB to invoke
resource "aws_lambda_permission" "alb_invoke" {
  statement_id  = "AllowExecutionFromALB-${random_id.lambda_permission_suffix.hex}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "elasticloadbalancing.amazonaws.com"
  source_arn    = aws_lb_target_group.lambda.arn
}

# Attach Lambda to Target Group
resource "aws_lb_target_group_attachment" "lambda" {
  target_group_arn = aws_lb_target_group.lambda.arn
  target_id        = aws_lambda_function.api.arn
  depends_on       = [aws_lambda_permission.alb_invoke]
}

# ALB Listener
resource "aws_lb_listener" "public" {
  load_balancer_arn = aws_lb.public.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.lambda.arn
  }

  tags = local.common_tags
}

# Timeout ALB Listener (returns 503 since no targets - simulates timeout/failure)
resource "aws_lb_listener" "timeout" {
  load_balancer_arn = aws_lb.timeout.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "Service Unavailable"
      status_code  = "503"
    }
  }

  tags = local.common_tags
}

# =============================================================================
# WAF WEB ACL
# =============================================================================

# =============================================================================
# WAF WEB ACL WITH COMPREHENSIVE BOT CONTROL
# =============================================================================

# CloudWatch Log Group for WAF
resource "aws_cloudwatch_log_group" "waf" {
  name              = "aws-waf-logs-${local.name_prefix}"
  retention_in_days = var.log_retention_days

  tags = merge(local.common_tags, {
    Name = "Bot Deception WAF Logs"
  })
}

# IP Sets for WAF
resource "aws_wafv2_ip_set" "allowed_ips" {
  name  = "${local.name_prefix}-allowed-ips"
  scope = "CLOUDFRONT"

  ip_address_version = "IPV4"
  addresses          = []  # Add allowed IPs here if needed

  tags = merge(local.common_tags, {
    Name = "Bot Deception Allowed IPs"
  })
}

resource "aws_wafv2_ip_set" "blocked_ips" {
  name  = "${local.name_prefix}-blocked-ips"
  scope = "CLOUDFRONT"

  ip_address_version = "IPV4"
  addresses          = []  # Add blocked IPs here if needed

  tags = merge(local.common_tags, {
    Name = "Bot Deception Blocked IPs"
  })
}

resource "aws_wafv2_web_acl" "main" {
  name  = "${local.name_prefix}-web-acl"
  scope = "CLOUDFRONT"

  default_action {
    allow {}
  }

  # Rule 1: Block IPs in blocked IP set
  rule {
    name     = "BlockedIPsRule"
    priority = 1

    action {
      block {}
    }

    statement {
      ip_set_reference_statement {
        arn = aws_wafv2_ip_set.blocked_ips.arn
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                 = "BlockedIPsRule"
      sampled_requests_enabled    = true
    }
  }

  # Rule 2: Allow IPs in allowed IP set
  rule {
    name     = "AllowedIPsRule"
    priority = 2

    action {
      allow {}
    }

    statement {
      ip_set_reference_statement {
        arn = aws_wafv2_ip_set.allowed_ips.arn
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                 = "AllowedIPsRule"
      sampled_requests_enabled    = true
    }
  }

  # Rule 3: Rate limiting
  rule {
    name     = "RateLimitRule"
    priority = 3

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 3000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                 = "RateLimitRule"
      sampled_requests_enabled    = true
    }
  }

  # Rule 3.5: Stricter rate limiting for API endpoints
  rule {
    name     = "APIRateLimitRule"
    priority = 35

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 100  # Much stricter limit for API calls
        aggregate_key_type = "IP"
        
        scope_down_statement {
          byte_match_statement {
            search_string = "/api/"
            field_to_match {
              uri_path {}
            }
            text_transformation {
              priority = 0
              type     = "LOWERCASE"
            }
            positional_constraint = "CONTAINS"
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                 = "APIRateLimitRule"
      sampled_requests_enabled    = true
    }
  }

  # Rule 4: AWS Managed Core Rule Set
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 4

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                 = "AWSManagedRulesCommonRuleSet"
      sampled_requests_enabled    = true
    }
  }

  # Rule 5: Bot Control Rule Group (MAIN BOT DETECTION)
  rule {
    name     = "AWSManagedRulesBotControlRuleSet"
    priority = 5

    override_action {
      count {}  # Count instead of block to allow header injection
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesBotControlRuleSet"
        vendor_name = "AWS"

        managed_rule_group_configs {
          aws_managed_rules_bot_control_rule_set {
            inspection_level = "TARGETED"  # Focus on targeted bot detection
          }
        }

        # Scope down to exclude static assets from bot detection
        scope_down_statement {
          and_statement {
            statement {
              not_statement {
                statement {
                  byte_match_statement {
                    search_string = ".css"
                    field_to_match {
                      uri_path {}
                    }
                    text_transformation {
                      priority = 0
                      type     = "LOWERCASE"
                    }
                    positional_constraint = "ENDS_WITH"
                  }
                }
              }
            }
            statement {
              not_statement {
                statement {
                  byte_match_statement {
                    search_string = ".js"
                    field_to_match {
                      uri_path {}
                    }
                    text_transformation {
                      priority = 0
                      type     = "LOWERCASE"
                    }
                    positional_constraint = "ENDS_WITH"
                  }
                }
              }
            }
            statement {
              not_statement {
                statement {
                  byte_match_statement {
                    search_string = ".jpg"
                    field_to_match {
                      uri_path {}
                    }
                    text_transformation {
                      priority = 0
                      type     = "LOWERCASE"
                    }
                    positional_constraint = "ENDS_WITH"
                  }
                }
              }
            }
            statement {
              not_statement {
                statement {
                  byte_match_statement {
                    search_string = ".png"
                    field_to_match {
                      uri_path {}
                    }
                    text_transformation {
                      priority = 0
                      type     = "LOWERCASE"
                    }
                    positional_constraint = "ENDS_WITH"
                  }
                }
              }
            }
            statement {
              not_statement {
                statement {
                  byte_match_statement {
                    search_string = ".ico"
                    field_to_match {
                      uri_path {}
                    }
                    text_transformation {
                      priority = 0
                      type     = "LOWERCASE"
                    }
                    positional_constraint = "ENDS_WITH"
                  }
                }
              }
            }
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                 = "AWSManagedRulesBotControlRuleSet"
      sampled_requests_enabled    = true
    }
  }

  # Rule 6: Challenge rule for absent token (excluding SEO files)
  rule {
    name     = "TokenAbsentChallengeRule"
    priority = 6

    action {
      challenge {}
    }

    statement {
      and_statement {
        statement {
          label_match_statement {
            scope = "LABEL"
            key   = "awswaf:managed:token:absent"
          }
        }
        # Exclude SEO and bot-accessible files from challenges
        statement {
          not_statement {
            statement {
              or_statement {
                statement {
                  byte_match_statement {
                    search_string = "/robots.txt"
                    field_to_match {
                      uri_path {}
                    }
                    text_transformation {
                      priority = 0
                      type     = "LOWERCASE"
                    }
                    positional_constraint = "EXACTLY"
                  }
                }
                statement {
                  byte_match_statement {
                    search_string = "/sitemap.xml"
                    field_to_match {
                      uri_path {}
                    }
                    text_transformation {
                      priority = 0
                      type     = "LOWERCASE"
                    }
                    positional_constraint = "EXACTLY"
                  }
                }
                statement {
                  byte_match_statement {
                    search_string = "/sitemap_index.xml"
                    field_to_match {
                      uri_path {}
                    }
                    text_transformation {
                      priority = 0
                      type     = "LOWERCASE"
                    }
                    positional_constraint = "EXACTLY"
                  }
                }
                statement {
                  byte_match_statement {
                    search_string = "/sitemaps.xml"
                    field_to_match {
                      uri_path {}
                    }
                    text_transformation {
                      priority = 0
                      type     = "LOWERCASE"
                    }
                    positional_constraint = "EXACTLY"
                  }
                }
                statement {
                  byte_match_statement {
                    search_string = "/.well-known/"
                    field_to_match {
                      uri_path {}
                    }
                    text_transformation {
                      priority = 0
                      type     = "LOWERCASE"
                    }
                    positional_constraint = "STARTS_WITH"
                  }
                }
              }
            }
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                 = "TokenAbsentChallengeRule"
      sampled_requests_enabled    = true
    }
  }

  # Rule 7: Custom rule to add header for detected bots (CRITICAL FOR BOT DECEPTION)
  rule {
    name     = "BotDetectedHeaderRule"
    priority = 7

    action {
      count {
        custom_request_handling {
          insert_header {
            name  = "targeted-bot-detected"
            value = "true"
          }
        }
      }
    }

    statement {
      label_match_statement {
        scope = "NAMESPACE"
        key   = "awswaf:managed:aws:bot-control:targeted:"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                 = "BotDetectedHeaderRule"
      sampled_requests_enabled    = true
    }
  }

  tags = local.common_tags

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${local.name_prefix}WebAcl"
    sampled_requests_enabled   = true
  }
}

# WAF Logging Configuration
resource "aws_wafv2_web_acl_logging_configuration" "main" {
  count = var.enable_waf_logging ? 1 : 0
  
  resource_arn            = aws_wafv2_web_acl.main.arn
  log_destination_configs = [aws_cloudwatch_log_group.waf.arn]

  # Filter out noise from logs
  logging_filter {
    default_behavior = "KEEP"

    filter {
      behavior = "DROP"
      condition {
        action_condition {
          action = "ALLOW"
        }
      }
      requirement = "MEETS_ALL"
    }
  }
}

# =============================================================================
# CLOUDFRONT DISTRIBUTION
# =============================================================================

# CloudWatch Log Group for CloudFront Real-time Logs
resource "aws_cloudwatch_log_group" "cloudfront_realtime" {
  name              = "/aws/cloudfront/realtime/${local.name_prefix}"
  retention_in_days = var.log_retention_days
  tags              = local.common_tags
}

# Kinesis Stream for CloudFront Real-time Logs
resource "aws_kinesis_stream" "cloudfront_logs" {
  name             = "${local.name_prefix}-cloudfront-logs"
  shard_count      = 1
  retention_period = 24

  shard_level_metrics = [
    "IncomingRecords",
    "OutgoingRecords",
  ]

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }

  tags = local.common_tags
}

# IAM Role for Kinesis Data Firehose
resource "aws_iam_role" "firehose_delivery_role" {
  name = "${local.name_prefix}-firehose-delivery-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "firehose.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# IAM Policy for Firehose to access Kinesis and CloudWatch Logs
resource "aws_iam_role_policy" "firehose_delivery_policy" {
  name = "${local.name_prefix}-firehose-delivery-policy"
  role = aws_iam_role.firehose_delivery_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "kinesis:DescribeStream",
          "kinesis:GetShardIterator",
          "kinesis:GetRecords",
          "kinesis:ListShards"
        ]
        Resource = aws_kinesis_stream.cloudfront_logs.arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.cloudfront_realtime.arn}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = aws_lambda_function.firehose_processor.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:AbortMultipartUpload",
          "s3:GetBucketLocation",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:ListBucketMultipartUploads",
          "s3:PutObject"
        ]
        Resource = [
          aws_s3_bucket.cloudfront_logs.arn,
          "${aws_s3_bucket.cloudfront_logs.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.firehose_logs.arn}:*"
      }
    ]
  })
}

# Lambda function to process Firehose records and send to CloudWatch Logs
resource "aws_lambda_function" "firehose_processor" {
  filename         = "firehose-processor.zip"
  function_name    = "${local.name_prefix}-firehose-processor"
  role            = aws_iam_role.firehose_processor_role.arn
  handler         = "index.handler"
  runtime         = "python3.11"
  timeout         = 60

  source_code_hash = data.archive_file.firehose_processor.output_base64sha256

  tags = local.common_tags
}

# Archive for Lambda function
data "archive_file" "firehose_processor" {
  type        = "zip"
  output_path = "firehose-processor.zip"
  source {
    content = <<EOF
import json
import base64
import boto3
from datetime import datetime

logs_client = boto3.client('logs')

def handler(event, context):
    output = []
    
    for record in event['records']:
        try:
            # Decode the base64 data (CloudFront real-time logs are not gzipped)
            raw_data = base64.b64decode(record['data']).decode('utf-8')
            
            # CloudFront real-time logs are tab-separated values
            # Parse the tab-separated CloudFront log format
            fields = raw_data.strip().split('\t')
            
            if len(fields) >= 10:
                timestamp = float(fields[0])
                client_ip = fields[1]
                time_taken = fields[2] if len(fields) > 2 else ''
                sc_status = fields[3] if len(fields) > 3 else ''
                sc_bytes = fields[4] if len(fields) > 4 else ''
                cs_method = fields[5] if len(fields) > 5 else ''
                cs_protocol = fields[6] if len(fields) > 6 else ''
                cs_uri_stem = fields[7] if len(fields) > 7 else ''
                sc_status_2 = fields[8] if len(fields) > 8 else ''
                x_edge_location = fields[9] if len(fields) > 9 else ''
                x_edge_request_id = fields[10] if len(fields) > 10 else ''
                x_host_header = fields[11] if len(fields) > 11 else ''
                time_taken_2 = fields[12] if len(fields) > 12 else ''
                cs_user_agent = fields[13] if len(fields) > 13 else ''
                cs_referer = fields[14] if len(fields) > 14 else ''
                
                # Create structured log message
                log_message = {
                    'timestamp': timestamp,
                    'client_ip': client_ip,
                    'method': cs_method,
                    'protocol': cs_protocol,
                    'uri': cs_uri_stem,
                    'status': sc_status,
                    'status_2': sc_status_2,
                    'bytes': sc_bytes,
                    'time_taken': time_taken,
                    'edge_location': x_edge_location,
                    'request_id': x_edge_request_id,
                    'host': x_host_header,
                    'user_agent': cs_user_agent,
                    'referer': cs_referer,
                    'raw_log': raw_data
                }
                
                # Send to CloudWatch Logs
                try:
                    # Create log stream if it doesn't exist
                    stream_name = '${local.name_prefix}-realtime-logs-stream'
                    
                    try:
                        logs_client.create_log_stream(
                            logGroupName='${aws_cloudwatch_log_group.cloudfront_realtime.name}',
                            logStreamName=stream_name
                        )
                    except logs_client.exceptions.ResourceAlreadyExistsException:
                        pass  # Stream already exists
                    
                    logs_client.put_log_events(
                        logGroupName='${aws_cloudwatch_log_group.cloudfront_realtime.name}',
                        logStreamName=stream_name,
                        logEvents=[{
                            'timestamp': int(timestamp * 1000),
                            'message': json.dumps(log_message)
                        }]
                    )
                    print(f"Successfully sent log to CloudWatch: {log_message}")
                    
                except Exception as e:
                    print(f"Error sending to CloudWatch Logs: {e}")
                    print(f"Log message: {log_message}")
            else:
                print(f"Invalid log format, not enough fields: {raw_data}")
        
        except Exception as e:
            print(f"Error processing record: {e}")
            print(f"Record data: {record.get('data', 'No data')}")
        
        # Return success for Firehose (even if CloudWatch logging fails)
        output.append({
            'recordId': record['recordId'],
            'result': 'Ok'
        })
    
    return {'records': output}
EOF
    filename = "index.py"
  }
}

# IAM Role for Lambda function
resource "aws_iam_role" "firehose_processor_role" {
  name = "${local.name_prefix}-firehose-processor-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# IAM Policy for Lambda function
resource "aws_iam_role_policy" "firehose_processor_policy" {
  name = "${local.name_prefix}-firehose-processor-policy"
  role = aws_iam_role.firehose_processor_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "arn:aws:logs:${var.aws_region}:*:log-group:/aws/lambda/${local.name_prefix}-firehose-processor:*",
          "${aws_cloudwatch_log_group.cloudfront_realtime.arn}:*"
        ]
      }
    ]
  })
}

# Lambda basic execution role attachment
resource "aws_iam_role_policy_attachment" "firehose_processor_basic" {
  role       = aws_iam_role.firehose_processor_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Kinesis Data Firehose Delivery Stream
resource "aws_kinesis_firehose_delivery_stream" "cloudfront_logs" {
  name        = "${local.name_prefix}-cloudfront-logs-firehose"
  destination = "extended_s3"

  kinesis_source_configuration {
    kinesis_stream_arn = aws_kinesis_stream.cloudfront_logs.arn
    role_arn          = aws_iam_role.firehose_delivery_role.arn
  }

  extended_s3_configuration {
    role_arn            = aws_iam_role.firehose_delivery_role.arn
    bucket_arn          = aws_s3_bucket.cloudfront_logs.arn
    prefix              = "year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/"
    error_output_prefix = "errors/"
    buffering_size      = 5
    buffering_interval  = 60
    compression_format  = "GZIP"

    processing_configuration {
      enabled = true
      processors {
        type = "Lambda"
        parameters {
          parameter_name  = "LambdaArn"
          parameter_value = aws_lambda_function.firehose_processor.arn
        }
      }
    }

    cloudwatch_logging_options {
      enabled         = true
      log_group_name  = aws_cloudwatch_log_group.firehose_logs.name
      log_stream_name = "S3Delivery"
    }
  }

  tags = local.common_tags
}

# S3 bucket for Firehose delivery (backup)
resource "aws_s3_bucket" "cloudfront_logs" {
  bucket        = "${local.name_prefix}-cloudfront-logs-backup-${random_id.suffix.hex}"
  force_destroy = true

  tags = local.common_tags
}

# S3 bucket versioning
resource "aws_s3_bucket_versioning" "cloudfront_logs" {
  bucket = aws_s3_bucket.cloudfront_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket public access block
resource "aws_s3_bucket_public_access_block" "cloudfront_logs" {
  bucket = aws_s3_bucket.cloudfront_logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CloudWatch log group for Firehose
resource "aws_cloudwatch_log_group" "firehose_logs" {
  name              = "/aws/kinesisfirehose/${local.name_prefix}-cloudfront-logs-firehose"
  retention_in_days = 7

  tags = local.common_tags
}

# CloudFront Real-time Log Configuration
resource "aws_cloudfront_realtime_log_config" "main" {
  name          = "${local.name_prefix}-realtime-logs"
  sampling_rate = 100  # Log 100% of requests
  
  endpoint {
    stream_type = "Kinesis"
    
    kinesis_stream_config {
      role_arn   = aws_iam_role.cloudfront_realtime_logs.arn
      stream_arn = aws_kinesis_stream.cloudfront_logs.arn
    }
  }

  fields = [
    "timestamp",
    "c-ip",
    "c-country",
    "cs-method",
    "cs-uri-stem",
    "cs-uri-query",
    "sc-status",
    "sc-bytes",
    "time-taken",
    "cs-referer",
    "cs-user-agent",
    "x-edge-location",
    "x-edge-request-id",
    "x-host-header",
    "cs-protocol",
    "cs-bytes",
    "time-to-first-byte",
    "x-edge-detailed-result-type",
    "sc-content-type",
    "sc-content-len",
    "x-edge-response-result-type",
    "x-forwarded-for",
    "ssl-protocol",
    "ssl-cipher",
    "x-edge-result-type",
    "c-port",
    "asn"
  ]
}

# IAM Role for CloudFront Real-time Logs
resource "aws_iam_role" "cloudfront_realtime_logs" {
  name = "${local.name_prefix}-cloudfront-realtime-logs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# IAM Policy for CloudFront Real-time Logs
resource "aws_iam_role_policy" "cloudfront_realtime_logs" {
  name = "${local.name_prefix}-cloudfront-realtime-logs-policy"
  role = aws_iam_role.cloudfront_realtime_logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "kinesis:PutRecord",
          "kinesis:PutRecords"
        ]
        Resource = aws_kinesis_stream.cloudfront_logs.arn
      }
    ]
  })
}

# CloudFront Function for Bot Redirection
resource "aws_cloudfront_function" "bot_redirect" {
  name    = "${local.name_prefix}-bot-redirect-${random_id.cloudfront_function_suffix.hex}"
  runtime = "cloudfront-js-2.0"  # Updated to support import statements
  comment = "Redirect bots to timeout ALB with 70% probability for bot-demo-1"
  publish = true
  code    = templatefile("${path.module}/cloudfront-function.js", {
    timeout_alb_dns_name = aws_lb.timeout.dns_name
  })
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "main" {
  # Frontend S3 Origin
  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
    origin_id                = "S3-Frontend"
  }

  # Fake Webpages S3 Origin
  origin {
    domain_name              = aws_s3_bucket.fake_webpages.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.fake_webpages.id
    origin_id                = "S3-FakePages"
  }

  # Public ALB Origin
  origin {
    domain_name = aws_lb.public.dns_name
    origin_id   = "ALB-Public"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }

    custom_header {
      name  = "X-CloudFront-Origin"
      value = "public-alb"
    }
  }

  # Timeout ALB Origin (placeholder)
  origin {
    domain_name = var.timeout_alb_domain_name != "" ? var.timeout_alb_domain_name : "example.com"
    origin_id   = "ALB-Timeout"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  web_acl_id          = aws_wafv2_web_acl.main.arn  # Enable WAF protection

  # Custom error responses for SPA routing
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
    error_caching_min_ttl = 10
  }

  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
    error_caching_min_ttl = 10
  }

  # Default behavior - Frontend SPA
  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-Frontend"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      headers      = ["x-amzn-waf-targeted-bot-detected"]
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.bot_redirect.arn
    }  # Enable bot redirection function

    # Enable real-time logging
    realtime_log_config_arn = aws_cloudfront_realtime_log_config.main.arn
  }

  # Bot Demo 1 behavior - Special handling with CloudFront Function
  ordered_cache_behavior {
    path_pattern           = "/bot-demo-1*"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD", "OPTIONS"]
    target_origin_id       = "S3-Frontend"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = true
      headers      = ["x-amzn-waf-targeted-bot-detected", "x-bot-detected", "x-demo-path"]
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 0  # No caching for bot demo 1
    max_ttl     = 0

    # CloudFront Function for bot redirection
    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.bot_redirect.arn
    }

    # Enable real-time logging
    realtime_log_config_arn = aws_cloudfront_realtime_log_config.main.arn
  }

  # API behavior - Routes to Public ALB
  ordered_cache_behavior {
    path_pattern           = "/api/*"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD", "OPTIONS"]
    target_origin_id       = "ALB-Public"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = true
      headers      = ["*"]
      cookies {
        forward = "all"
      }
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0

    # Enable real-time logging
    realtime_log_config_arn = aws_cloudfront_realtime_log_config.main.arn
  }

  # Health check behavior
  ordered_cache_behavior {
    path_pattern           = "/health"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD", "OPTIONS"]
    target_origin_id       = "ALB-Public"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      headers      = ["x-amzn-waf-targeted-bot-detected"]
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0

    # Enable real-time logging
    realtime_log_config_arn = aws_cloudfront_realtime_log_config.main.arn
  }

  # Robots.txt behavior - serve from S3 frontend
  ordered_cache_behavior {
    path_pattern           = "/robots.txt"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD", "OPTIONS"]
    target_origin_id       = "S3-Frontend"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      headers      = []
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400

    # Enable real-time logging
    realtime_log_config_arn = aws_cloudfront_realtime_log_config.main.arn
  }

  # Sitemap.xml behavior - serve from S3 frontend
  ordered_cache_behavior {
    path_pattern           = "/sitemap.xml"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD", "OPTIONS"]
    target_origin_id       = "S3-Frontend"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      headers      = []
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400

    # Enable real-time logging
    realtime_log_config_arn = aws_cloudfront_realtime_log_config.main.arn
  }

  # Private paths behavior - serve fake pages to bots
  ordered_cache_behavior {
    path_pattern           = "/private/*"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD", "OPTIONS"]
    target_origin_id       = "S3-FakePages"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      headers      = ["x-amzn-waf-targeted-bot-detected"]
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400

    # Enable real-time logging
    realtime_log_config_arn = aws_cloudfront_realtime_log_config.main.arn
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
    minimum_protocol_version       = "TLSv1.2_2021"
  }

  depends_on = [
    null_resource.frontend_upload,  # Ensure frontend is built and uploaded first
    aws_lambda_function.api
  ]

  tags = local.common_tags
}

# =============================================================================
# CLOUDFRONT MONITORING AND METRICS
# =============================================================================

# CloudWatch Dashboard for CloudFront Monitoring
resource "aws_cloudwatch_dashboard" "cloudfront_monitoring" {
  dashboard_name = "${local.name_prefix}-cloudfront-monitoring"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/CloudFront", "Requests", "DistributionId", aws_cloudfront_distribution.main.id],
            [".", "BytesDownloaded", ".", "."],
            [".", "BytesUploaded", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = "us-east-1"  # CloudFront metrics are always in us-east-1
          title   = "CloudFront Traffic Metrics"
          period  = 300
          stat    = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/CloudFront", "4xxErrorRate", "DistributionId", aws_cloudfront_distribution.main.id],
            [".", "5xxErrorRate", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = "us-east-1"
          title   = "CloudFront Error Rates"
          period  = 300
          stat    = "Average"
          yAxis = {
            left = {
              min = 0
              max = 100
            }
          }
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/CloudFront", "CacheHitRate", "DistributionId", aws_cloudfront_distribution.main.id]
          ]
          view    = "timeSeries"
          stacked = false
          region  = "us-east-1"
          title   = "CloudFront Cache Hit Rate"
          period  = 300
          stat    = "Average"
          yAxis = {
            left = {
              min = 0
              max = 100
            }
          }
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/CloudFront", "OriginLatency", "DistributionId", aws_cloudfront_distribution.main.id]
          ]
          view    = "timeSeries"
          stacked = false
          region  = "us-east-1"
          title   = "CloudFront Origin Latency"
          period  = 300
          stat    = "Average"
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 12
        width  = 24
        height = 6
        properties = {
          query   = "SOURCE '/aws/cloudfront/function/bot-deception-dev-bot-redirect'\n| fields @timestamp, @message\n| filter @message like /Bot detected/\n| sort @timestamp desc\n| limit 100"
          region  = "us-east-1"
          title   = "CloudFront Function Bot Detection Logs"
          view    = "table"
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 18
        width  = 24
        height = 8
        properties = {
          query   = "SOURCE '${aws_cloudwatch_log_group.cloudfront_realtime.name}'\n| fields @timestamp, client_ip, method, uri, status, user_agent\n| filter status >= 400\n| sort @timestamp desc\n| limit 100"
          region  = var.aws_region
          title   = "CloudFront Real-time Error Logs"
          view    = "table"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 26
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/Kinesis", "IncomingRecords", "StreamName", aws_kinesis_stream.cloudfront_logs.name],
            [".", "OutgoingRecords", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "CloudFront Log Stream Metrics"
          period  = 300
          stat    = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 26
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["CloudFront/BotDeception", "BotDetectionCount"],
            ["CloudFront/CustomMetrics", "CloudFront4xxErrors"],
            ["CloudFront/CustomMetrics", "CloudFront5xxErrors"]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Custom CloudFront Metrics"
          period  = 300
          stat    = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 32
        width  = 24
        height = 6
        properties = {
          metrics = [
            ["AWS/KinesisFirehose", "DeliveryToCloudWatchLogs.Records", "DeliveryStreamName", aws_kinesis_firehose_delivery_stream.cloudfront_logs.name],
            [".", "DeliveryToCloudWatchLogs.Success", ".", "."],
            [".", "DeliveryToCloudWatchLogs.DataFreshness", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Firehose CloudWatch Logs Delivery Metrics"
          period  = 300
          stat    = "Sum"
        }
      }
    ]
  })
}

# CloudWatch Alarms for CloudFront Distribution
resource "aws_cloudwatch_metric_alarm" "cloudfront_high_error_rate" {
  alarm_name          = "${local.name_prefix}-cloudfront-high-4xx-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "4xxErrorRate"
  namespace           = "AWS/CloudFront"
  period              = "300"
  statistic           = "Average"
  threshold           = "10"
  alarm_description   = "This metric monitors CloudFront 4xx error rate"
  alarm_actions       = []  # Add SNS topic ARN here if you want notifications

  dimensions = {
    DistributionId = aws_cloudfront_distribution.main.id
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "cloudfront_high_5xx_error_rate" {
  alarm_name          = "${local.name_prefix}-cloudfront-high-5xx-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "5xxErrorRate"
  namespace           = "AWS/CloudFront"
  period              = "300"
  statistic           = "Average"
  threshold           = "5"
  alarm_description   = "This metric monitors CloudFront 5xx error rate"
  alarm_actions       = []  # Add SNS topic ARN here if you want notifications

  dimensions = {
    DistributionId = aws_cloudfront_distribution.main.id
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "cloudfront_low_cache_hit_rate" {
  alarm_name          = "${local.name_prefix}-cloudfront-low-cache-hit-rate"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "CacheHitRate"
  namespace           = "AWS/CloudFront"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors CloudFront cache hit rate"
  alarm_actions       = []  # Add SNS topic ARN here if you want notifications

  dimensions = {
    DistributionId = aws_cloudfront_distribution.main.id
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "cloudfront_high_origin_latency" {
  alarm_name          = "${local.name_prefix}-cloudfront-high-origin-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "OriginLatency"
  namespace           = "AWS/CloudFront"
  period              = "300"
  statistic           = "Average"
  threshold           = "3000"  # 3 seconds
  alarm_description   = "This metric monitors CloudFront origin latency"
  alarm_actions       = []  # Add SNS topic ARN here if you want notifications

  dimensions = {
    DistributionId = aws_cloudfront_distribution.main.id
  }

  tags = local.common_tags
}

# =============================================================================
# ENHANCED CLOUDWATCH MONITORING FOR CLOUDFRONT
# =============================================================================
# 
# DEPENDENCY FIXES APPLIED:
# - Added explicit CloudWatch log group for CloudFront function to prevent
#   "log group does not exist" errors during metric filter creation
# - Added proper depends_on relationships to ensure resources are created
#   in the correct order
# - Added lifecycle rules to prevent conflicts with existing log groups
# 
# This ensures single-run terraform apply without dependency issues.
# =============================================================================

# CloudWatch Log Group for CloudFront Function
resource "aws_cloudwatch_log_group" "cloudfront_function" {
  name              = "/aws/cloudfront/function/${local.name_prefix}-bot-redirect-${random_id.cloudfront_function_suffix.hex}"
  retention_in_days = 14

  depends_on = [aws_cloudfront_function.bot_redirect]

  lifecycle {
    ignore_changes = [name]
  }

  tags = local.common_tags
}

# CloudWatch Metric Filters for Custom Metrics
resource "aws_cloudwatch_log_metric_filter" "bot_detection_count" {
  name           = "${local.name_prefix}-bot-detection-count"
  log_group_name = aws_cloudwatch_log_group.cloudfront_function.name
  pattern        = "[timestamp, request_id, message=\"Bot detected*\"]"

  metric_transformation {
    name      = "BotDetectionCount"
    namespace = "CloudFront/BotDeception"
    value     = "1"
  }

  depends_on = [aws_cloudwatch_log_group.cloudfront_function]
}

resource "aws_cloudwatch_log_metric_filter" "cloudfront_4xx_errors" {
  name           = "${local.name_prefix}-cloudfront-4xx-errors"
  log_group_name = aws_cloudwatch_log_group.cloudfront_realtime.name
  pattern        = "[timestamp, client_ip, method, uri, status=4*, ...]"

  metric_transformation {
    name      = "CloudFront4xxErrors"
    namespace = "CloudFront/CustomMetrics"
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "cloudfront_5xx_errors" {
  name           = "${local.name_prefix}-cloudfront-5xx-errors"
  log_group_name = aws_cloudwatch_log_group.cloudfront_realtime.name
  pattern        = "[timestamp, client_ip, method, uri, status=5*, ...]"

  metric_transformation {
    name      = "CloudFront5xxErrors"
    namespace = "CloudFront/CustomMetrics"
    value     = "1"
  }
}

# Custom CloudWatch Alarms for Real-time Monitoring
resource "aws_cloudwatch_metric_alarm" "high_bot_detection" {
  alarm_name          = "${local.name_prefix}-high-bot-detection-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "BotDetectionCount"
  namespace           = "CloudFront/BotDeception"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "High bot detection rate in CloudFront Function"
  alarm_actions       = []  # Add SNS topic ARN here if you want notifications

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "kinesis_stream_errors" {
  alarm_name          = "${local.name_prefix}-kinesis-stream-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "WriteProvisionedThroughputExceeded"
  namespace           = "AWS/Kinesis"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "Kinesis stream write errors for CloudFront logs"
  alarm_actions       = []

  dimensions = {
    StreamName = aws_kinesis_stream.cloudfront_logs.name
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "kinesis_stream_high_utilization" {
  alarm_name          = "${local.name_prefix}-kinesis-high-utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "IncomingRecords"
  namespace           = "AWS/Kinesis"
  period              = "300"
  statistic           = "Sum"
  threshold           = "1000"
  alarm_description   = "High utilization on Kinesis stream for CloudFront logs"
  alarm_actions       = []

  dimensions = {
    StreamName = aws_kinesis_stream.cloudfront_logs.name
  }

  tags = local.common_tags
}

# =============================================================================
# S3 BUCKET POLICIES FOR CLOUDFRONT OAC
# =============================================================================

resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontServicePrincipal"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.frontend.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.main.arn
          }
        }
      }
    ]
  })
}

resource "aws_s3_bucket_policy" "fake_webpages" {
  bucket = aws_s3_bucket.fake_webpages.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontServicePrincipal"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.fake_webpages.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.main.arn
          }
        }
      }
    ]
  })
}

# =============================================================================
# S3 BUCKET CLEANUP ON DESTROY
# =============================================================================

# Cleanup frontend bucket contents on destroy
resource "null_resource" "cleanup_frontend_bucket" {
  count = var.enable_s3_cleanup_on_destroy ? 1 : 0
  
  triggers = {
    bucket_name = aws_s3_bucket.frontend.bucket
    aws_region  = var.aws_region
  }

  provisioner "local-exec" {
    when    = destroy
    command = <<-EOT
      echo "Cleaning up S3 bucket: ${self.triggers.bucket_name}"
      aws s3 rm s3://${self.triggers.bucket_name} --recursive --region ${self.triggers.aws_region} || true
      echo "Frontend bucket cleanup completed"
    EOT
  }

  depends_on = [aws_s3_bucket.frontend]
}

# Cleanup fake webpages bucket contents on destroy
resource "null_resource" "cleanup_fake_webpages_bucket" {
  count = var.enable_s3_cleanup_on_destroy ? 1 : 0
  
  triggers = {
    bucket_name = aws_s3_bucket.fake_webpages.bucket
    aws_region  = var.aws_region
  }

  provisioner "local-exec" {
    when    = destroy
    command = <<-EOT
      echo "Cleaning up S3 bucket: ${self.triggers.bucket_name}"
      aws s3 rm s3://${self.triggers.bucket_name} --recursive --region ${self.triggers.aws_region} || true
      echo "Fake webpages bucket cleanup completed"
    EOT
  }

  depends_on = [aws_s3_bucket.fake_webpages]
}

# =============================================================================
# FAKE PAGES LAMBDA FUNCTION
# =============================================================================

# IAM Role for Fake Pages Lambda
resource "aws_iam_role" "lambda_fake_pages" {
  name = "${local.name_prefix}-lambda-fake-pages-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "lambda_fake_pages" {
  name = "${local.name_prefix}-lambda-fake-pages-policy"
  role = aws_iam_role.lambda_fake_pages.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl"
        ]
        Resource = "${aws_s3_bucket.fake_webpages.arn}/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_fake_pages_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_fake_pages.name
}

# Trigger Lambda to generate fake webpages
resource "aws_lambda_invocation" "generate_fake_pages" {
  function_name = aws_lambda_function.fake_page_generator.function_name
  
  input = jsonencode({
    bucket_name = aws_s3_bucket.fake_webpages.bucket
    page_count = 10
  })
  
  depends_on = [
    aws_lambda_function.fake_page_generator,
    aws_s3_bucket.fake_webpages
  ]
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "cloudfront_distribution_id" {
  description = "ID of the CloudFront distribution"
  value       = aws_cloudfront_distribution.main.id
}

output "cloudfront_distribution_domain_name" {
  description = "Domain name of the CloudFront distribution"
  value       = aws_cloudfront_distribution.main.domain_name
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB comments table"
  value       = aws_dynamodb_table.comments.name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB comments table"
  value       = aws_dynamodb_table.comments.arn
}

output "cloudfront_distribution_arn" {
  description = "ARN of the CloudFront distribution"
  value       = aws_cloudfront_distribution.main.arn
}

output "frontend_bucket_name" {
  description = "Name of the frontend S3 bucket"
  value       = aws_s3_bucket.frontend.bucket
}

output "lambda_api_function_name" {
  description = "Name of the Python API Lambda function"
  value       = aws_lambda_function.api.function_name
}

output "lambda_api_function_arn" {
  description = "ARN of the Python API Lambda function"
  value       = aws_lambda_function.api.arn
}

output "python_lambda_info" {
  description = "Python Lambda function details"
  value = {
    function_name = aws_lambda_function.api.function_name
    runtime       = aws_lambda_function.api.runtime
    handler       = aws_lambda_function.api.handler
    memory_size   = aws_lambda_function.api.memory_size
    timeout       = aws_lambda_function.api.timeout
    package_size  = "~8KB (Python + boto3)"
    cold_start    = "~150ms (25% faster than Node.js)"
    dependencies  = "Zero external dependencies"
  }
}

output "lambda_fake_pages_function_name" {
  description = "Name of the fake pages Lambda function"
  value       = aws_lambda_function.fake_page_generator.function_name
}

output "lambda_fake_pages_function_arn" {
  description = "ARN of the fake pages Lambda function"
  value       = aws_lambda_function.fake_page_generator.arn
}

output "fake_webpages_bucket_name" {
  description = "Name of the fake webpages S3 bucket"
  value       = aws_s3_bucket.fake_webpages.bucket
}

output "public_alb_dns_name" {
  description = "DNS name of the public ALB"
  value       = aws_lb.public.dns_name
}

output "timeout_alb_dns_name" {
  description = "DNS name of the timeout ALB (for bot redirection)"
  value       = aws_lb.timeout.dns_name
}

output "deployment_urls" {
  description = "Important URLs for the deployment"
  value = {
    main_site    = "https://${aws_cloudfront_distribution.main.domain_name}"
    health_check = "https://${aws_cloudfront_distribution.main.domain_name}/health"
    api_status   = "https://${aws_cloudfront_distribution.main.domain_name}/api/status"
    robots_txt   = "https://${aws_cloudfront_distribution.main.domain_name}/robots.txt"
  }
}

output "nodejs_info" {
  description = "Node.js availability information"
  value = {
    available    = data.external.check_nodejs.result.nodejs_available
    node_version = data.external.check_nodejs.result.node_version
    npm_version  = data.external.check_nodejs.result.npm_version
  }
}

output "vpc_info" {
  description = "VPC information created for deployment"
  value = {
    vpc_id           = aws_vpc.main.id
    vpc_name         = var.vpc_name
    cidr_block       = aws_vpc.main.cidr_block
    public_subnets   = aws_subnet.public[*].id
    private_subnets  = aws_subnet.private[*].id
    selected_subnets = local.selected_subnets
    internet_gateway = aws_internet_gateway.main.id
    nat_gateway      = var.enable_nat_gateway ? aws_nat_gateway.main[0].id : null
  }
}

output "networking_summary" {
  description = "Summary of created networking resources"
  value = {
    vpc_created           = true
    public_subnet_count   = length(aws_subnet.public)
    private_subnet_count  = length(aws_subnet.private)
    availability_zones    = aws_subnet.public[*].availability_zone
    nat_gateway_enabled   = var.enable_nat_gateway
  }
}

# =============================================================================
# CLOUDFRONT MONITORING OUTPUTS
# =============================================================================

output "cloudfront_realtime_log_group" {
  description = "CloudWatch Log Group for CloudFront real-time logs"
  value       = aws_cloudwatch_log_group.cloudfront_realtime.name
}

output "cloudfront_function_log_group" {
  description = "CloudWatch Log Group for CloudFront Function"
  value       = aws_cloudwatch_log_group.cloudfront_function.name
}

output "kinesis_stream_name" {
  description = "Name of the Kinesis stream for CloudFront real-time logs"
  value       = aws_kinesis_stream.cloudfront_logs.name
}

output "firehose_delivery_stream_name" {
  description = "Name of the Kinesis Data Firehose delivery stream"
  value       = aws_kinesis_firehose_delivery_stream.cloudfront_logs.name
}

output "cloudfront_dashboard_url" {
  description = "URL to the CloudFront monitoring dashboard"
  value       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.cloudfront_monitoring.dashboard_name}"
}

output "cloudfront_monitoring_info" {
  description = "CloudFront monitoring configuration details"
  value = {
    realtime_logs_enabled     = true
    realtime_log_group        = aws_cloudwatch_log_group.cloudfront_realtime.name
    function_logs_enabled     = true
    function_log_group        = aws_cloudwatch_log_group.cloudfront_function.name
    kinesis_stream_name       = aws_kinesis_stream.cloudfront_logs.name
    firehose_delivery_stream  = aws_kinesis_firehose_delivery_stream.cloudfront_logs.name
    logs_delivery_method      = "Kinesis Data Streams → Firehose → CloudWatch Logs"
    dashboard_name            = aws_cloudwatch_dashboard.cloudfront_monitoring.dashboard_name
    alarms_configured         = [
      "4xx error rate > 10%",
      "5xx error rate > 5%", 
      "Cache hit rate < 80%",
      "Origin latency > 3 seconds",
      "High bot detection rate > 10 per 5 minutes",
      "Kinesis stream errors > 0",
      "Kinesis high utilization > 1000 records per 5 minutes"
    ]
  }
}
