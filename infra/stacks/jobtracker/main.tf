terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.82.0"
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

  backend "s3" {
    bucket         = "jobtracker-tfstate-569397624996"
    key            = "jobtracker/terraform.tfstate"
    region         = "us-west-2"
    dynamodb_table = "jobtracker-tflock"
    encrypt        = true
  }
}

provider "aws" {
  region = "us-west-2"
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  src_dir = "${path.module}/../../../jobtracker/src"
  source_files_hash = sha256(join(",", [
    filemd5("${local.src_dir}/requirements.txt"),
    filemd5("${local.src_dir}/handler.py"),
    filemd5("${local.src_dir}/scanner.py"),
    filemd5("${local.src_dir}/db.py"),
    filemd5("${local.src_dir}/auth.py"),
    filemd5("${local.src_dir}/seed_data.py"),
  ]))
}

# --- DynamoDB ---

module "dynamodb" {
  source = "../../modules/dynamodb-table"

  table_name             = "jobtracker"
  point_in_time_recovery = true
}

# --- S3 Frontend ---

module "frontend_bucket" {
  source = "../../modules/s3-website"

  bucket_name = "jobtracker-frontend-569397624996"
}

# --- Lambda Functions ---

module "api_lambda" {
  source = "../../modules/lambda-function"

  function_name     = "jobtracker-api"
  handler           = "handler.lambda_handler"
  runtime           = "python3.12"
  timeout           = 30
  role_arn          = aws_iam_role.api_lambda.arn
  source_dir        = local.src_dir
  source_files_hash = local.source_files_hash

  environment_variables = {
    DYNAMODB_TABLE        = module.dynamodb.table_name
    FRONTEND_URL          = var.frontend_url
    SSM_PREFIX            = "/jobtracker"
    SCANNER_FUNCTION_NAME = module.scanner_lambda.function_name
  }
}

module "scanner_lambda" {
  source = "../../modules/lambda-function"

  function_name     = "jobtracker-scanner"
  handler           = "scanner.lambda_handler"
  runtime           = "python3.12"
  timeout           = 300
  role_arn          = aws_iam_role.scanner_lambda.arn
  source_dir        = local.src_dir
  source_files_hash = local.source_files_hash

  environment_variables = {
    DYNAMODB_TABLE = module.dynamodb.table_name
  }
}

# --- API Gateway ---

module "api_gateway" {
  source = "../../modules/api-gateway-proxy"

  api_name             = "jobtracker-api"
  lambda_invoke_arn    = module.api_lambda.invoke_arn
  lambda_function_name = module.api_lambda.function_name
  stage_name           = "prod"
  cors_allow_origin    = var.frontend_url
  binary_media_types   = ["multipart/form-data"]
}

# --- CloudFront ---

module "cloudfront" {
  source = "../../modules/cloudfront-spa"

  domain_name         = var.domain_name
  certificate_arn     = var.certificate_arn
  s3_website_endpoint = module.frontend_bucket.website_endpoint
  api_gateway_id      = module.api_gateway.rest_api_id
  api_stage_name      = module.api_gateway.stage_name
}

# --- IAM: API Lambda Role ---

resource "aws_iam_role" "api_lambda" {
  name = "jobtracker-api-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "api_lambda_basic" {
  role       = aws_iam_role.api_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "api_lambda_dynamodb" {
  name = "dynamodb-crud"
  role = aws_iam_role.api_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:BatchWriteItem",
        "dynamodb:BatchGetItem",
      ]
      Resource = [
        module.dynamodb.table_arn,
        "${module.dynamodb.table_arn}/index/*",
      ]
    }]
  })
}

resource "aws_iam_role_policy" "api_lambda_invoke_scanner" {
  name = "invoke-scanner"
  role = aws_iam_role.api_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "lambda:InvokeFunction"
      Resource = module.scanner_lambda.function_arn
    }]
  })
}

resource "aws_iam_role_policy" "api_lambda_ssm" {
  name = "ssm-parameters"
  role = aws_iam_role.api_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath",
      ]
      Resource = [
        "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/jobtracker",
        "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/jobtracker/*",
      ]
    }]
  })
}

# --- IAM: Scanner Lambda Role ---

resource "aws_iam_role" "scanner_lambda" {
  name = "jobtracker-scanner-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "scanner_lambda_basic" {
  role       = aws_iam_role.scanner_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "scanner_lambda_dynamodb" {
  name = "dynamodb-crud"
  role = aws_iam_role.scanner_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:BatchWriteItem",
        "dynamodb:BatchGetItem",
      ]
      Resource = [
        module.dynamodb.table_arn,
        "${module.dynamodb.table_arn}/index/*",
      ]
    }]
  })
}

# --- EventBridge ---

resource "aws_cloudwatch_event_rule" "daily_scan" {
  name                = "jobtracker-daily-scan"
  description         = "Daily career page scan at 6am PT"
  schedule_expression = "cron(0 14 * * ? *)"
}

resource "aws_cloudwatch_event_target" "scanner" {
  rule = aws_cloudwatch_event_rule.daily_scan.name
  arn  = module.scanner_lambda.function_arn
}

resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.scanner_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_scan.arn
}
