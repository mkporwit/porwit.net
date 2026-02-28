resource "null_resource" "build" {
  triggers = {
    source_hash = var.source_files_hash
  }

  provisioner "local-exec" {
    command = <<-EOT
      set -e
      rm -rf ${path.module}/.build/${var.function_name}
      mkdir -p ${path.module}/.build/${var.function_name}
      pip3 install -r ${var.source_dir}/${var.requirements_file} -t ${path.module}/.build/${var.function_name} --quiet --platform manylinux2014_aarch64 --only-binary=:all: --python-version ${replace(var.runtime, "python", "")}
      cp ${var.source_dir}/*.py ${path.module}/.build/${var.function_name}/
      cp -r ${var.source_dir}/parsers ${path.module}/.build/${var.function_name}/ 2>/dev/null || true
    EOT
  }
}

data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/.build/${var.function_name}"
  output_path = "${path.module}/.build/${var.function_name}.zip"

  depends_on = [null_resource.build]
}

resource "aws_lambda_function" "this" {
  function_name    = var.function_name
  role             = var.role_arn
  handler          = var.handler
  runtime          = var.runtime
  architectures    = var.architectures
  memory_size      = var.memory_size
  timeout          = var.timeout
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256

  dynamic "environment" {
    for_each = length(var.environment_variables) > 0 ? [1] : []
    content {
      variables = var.environment_variables
    }
  }
}
