resource "null_resource" "lambda_build" {
  triggers = {
    requirements = filemd5("${path.module}/../src/requirements.txt")
    handler      = filemd5("${path.module}/../src/handler.py")
    scanner      = filemd5("${path.module}/../src/scanner.py")
    db           = filemd5("${path.module}/../src/db.py")
    auth         = filemd5("${path.module}/../src/auth.py")
    seed_data    = filemd5("${path.module}/../src/seed_data.py")
  }

  provisioner "local-exec" {
    command = <<-EOT
      set -e
      rm -rf ${path.module}/.build
      mkdir -p ${path.module}/.build
      pip3 install -r ${path.module}/../src/requirements.txt -t ${path.module}/.build --quiet --platform manylinux2014_aarch64 --only-binary=:all:
      cp ${path.module}/../src/*.py ${path.module}/.build/
      cp -r ${path.module}/../src/parsers ${path.module}/.build/ 2>/dev/null || true
    EOT
  }
}

data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/.build"
  output_path = "${path.module}/.build/lambda.zip"

  depends_on = [null_resource.lambda_build]
}

# --- API Lambda ---

resource "aws_lambda_function" "api" {
  function_name    = "jobtracker-api"
  role             = aws_iam_role.api_lambda.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  architectures    = ["arm64"]
  memory_size      = 512
  timeout          = 30
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE        = aws_dynamodb_table.jobtracker.name
      FRONTEND_URL          = var.frontend_url
      SSM_PREFIX            = "/jobtracker"
      SCANNER_FUNCTION_NAME = aws_lambda_function.scanner.function_name
    }
  }
}

# --- Scanner Lambda ---

resource "aws_lambda_function" "scanner" {
  function_name    = "jobtracker-scanner"
  role             = aws_iam_role.scanner_lambda.arn
  handler          = "scanner.lambda_handler"
  runtime          = "python3.12"
  architectures    = ["arm64"]
  memory_size      = 512
  timeout          = 300
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.jobtracker.name
    }
  }
}
