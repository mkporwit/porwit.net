# --- REST API ---

resource "aws_api_gateway_rest_api" "jobtracker" {
  name        = "jobtracker-api"
  description = "JobTracker API"

  binary_media_types = ["multipart/form-data"]

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

# {proxy+} resource
resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.jobtracker.id
  parent_id   = aws_api_gateway_rest_api.jobtracker.root_resource_id
  path_part   = "{proxy+}"
}

# ANY method on {proxy+}
resource "aws_api_gateway_method" "proxy_any" {
  rest_api_id   = aws_api_gateway_rest_api.jobtracker.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "proxy_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.jobtracker.id
  resource_id             = aws_api_gateway_resource.proxy.id
  http_method             = aws_api_gateway_method.proxy_any.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api.invoke_arn
}

# OPTIONS method for CORS preflight on {proxy+}
resource "aws_api_gateway_method" "proxy_options" {
  rest_api_id   = aws_api_gateway_rest_api.jobtracker.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "proxy_options" {
  rest_api_id = aws_api_gateway_rest_api.jobtracker.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.proxy_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "proxy_options_200" {
  rest_api_id = aws_api_gateway_rest_api.jobtracker.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.proxy_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "proxy_options" {
  rest_api_id = aws_api_gateway_rest_api.jobtracker.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.proxy_options.http_method
  status_code = aws_api_gateway_method_response.proxy_options_200.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PATCH,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'${var.frontend_url}'"
  }

  depends_on = [aws_api_gateway_integration.proxy_options]
}

# Deployment + Stage
resource "aws_api_gateway_deployment" "jobtracker" {
  rest_api_id = aws_api_gateway_rest_api.jobtracker.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.proxy.id,
      aws_api_gateway_method.proxy_any.id,
      aws_api_gateway_integration.proxy_lambda.id,
      aws_api_gateway_method.proxy_options.id,
      aws_api_gateway_integration.proxy_options.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "jobtracker" {
  deployment_id = aws_api_gateway_deployment.jobtracker.id
  rest_api_id   = aws_api_gateway_rest_api.jobtracker.id
  stage_name    = "prod"
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.jobtracker.execution_arn}/*/*"
}
