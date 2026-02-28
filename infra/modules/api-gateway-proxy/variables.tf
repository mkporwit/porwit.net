variable "api_name" {
  description = "Name of the REST API"
  type        = string
}

variable "lambda_invoke_arn" {
  description = "Lambda function invoke ARN"
  type        = string
}

variable "lambda_function_name" {
  description = "Lambda function name (for permission)"
  type        = string
}

variable "stage_name" {
  description = "API Gateway stage name"
  type        = string
  default     = "prod"
}

variable "cors_allow_origin" {
  description = "CORS Allow-Origin value"
  type        = string
}

variable "cors_allow_methods" {
  description = "CORS Allow-Methods value"
  type        = string
  default     = "GET,POST,PATCH,DELETE,OPTIONS"
}

variable "cors_allow_headers" {
  description = "CORS Allow-Headers value"
  type        = string
  default     = "Content-Type,Authorization"
}

variable "binary_media_types" {
  description = "Binary media types for the API"
  type        = list(string)
  default     = []
}
