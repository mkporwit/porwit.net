terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
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
    key            = "gunset/terraform.tfstate"
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
  src_dir = "${path.module}/../../../gunset/src"
  source_files_hash = sha256(join(",", [
    filemd5("${local.src_dir}/requirements.txt"),
    filemd5("${local.src_dir}/handler.py"),
    filemd5("${local.src_dir}/db.py"),
    filemd5("${local.src_dir}/models.py"),
    filemd5("${local.src_dir}/pdf_generator.py"),
  ]))
}

# --- DynamoDB ---

module "dynamodb" {
  source = "../../modules/dynamodb-table"

  table_name = "gunset-dev"

  additional_attributes = [
    { name = "email", type = "S" },
  ]

  global_secondary_indexes = [
    {
      name      = "email-index"
      hash_key  = "email"
      range_key = "pk"
    },
  ]

  ttl_attribute          = "expires_at"
  point_in_time_recovery = false
}

# --- S3 Frontend ---

module "frontend_bucket" {
  source = "../../modules/s3-website"

  bucket_name = "gunset-frontend-dev-569397624996"
}

# --- Lambda Function ---

module "api_lambda" {
  source = "../../modules/lambda-function"

  function_name     = "gunset-api-dev"
  handler           = "handler.lambda_handler"
  runtime           = "python3.11"
  timeout           = 30
  role_arn          = aws_iam_role.lambda.arn
  source_dir        = local.src_dir
  source_files_hash = local.source_files_hash

  environment_variables = {
    DYNAMODB_TABLE  = module.dynamodb.table_name
    FROM_EMAIL      = var.from_email
    ENVIRONMENT     = "dev"
    AWS_REGION_NAME = data.aws_region.current.name
    FRONTEND_URL    = var.frontend_url
  }
}

# --- API Gateway ---

module "api_gateway" {
  source = "../../modules/api-gateway-proxy"

  api_name             = "gunset-api-dev"
  lambda_invoke_arn    = module.api_lambda.invoke_arn
  lambda_function_name = module.api_lambda.function_name
  stage_name           = "dev"
  cors_allow_origin    = var.frontend_url
  cors_allow_methods   = "GET,POST,OPTIONS"
  binary_media_types   = ["application/pdf"]
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

# --- IAM ---

resource "aws_iam_role" "lambda" {
  name = "gunset-api-dev-GunsetFunctionRole"

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

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_dynamodb" {
  name = "dynamodb-crud"
  role = aws_iam_role.lambda.id

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

resource "aws_iam_role_policy" "lambda_ses" {
  name = "ses-send"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ses:SendEmail",
        "ses:SendRawEmail",
      ]
      Resource = "arn:aws:ses:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:identity/*"
    }]
  })
}
