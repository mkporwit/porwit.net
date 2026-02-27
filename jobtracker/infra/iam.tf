data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# --- API Lambda Role ---

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
        aws_dynamodb_table.jobtracker.arn,
        "${aws_dynamodb_table.jobtracker.arn}/index/*",
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
      Resource = aws_lambda_function.scanner.arn
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

# --- Scanner Lambda Role ---

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
        aws_dynamodb_table.jobtracker.arn,
        "${aws_dynamodb_table.jobtracker.arn}/index/*",
      ]
    }]
  })
}
