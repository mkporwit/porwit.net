variable "domain_name" {
  description = "Custom domain name (e.g. app.example.com)"
  type        = string
}

variable "certificate_arn" {
  description = "ACM certificate ARN in us-east-1"
  type        = string
}

variable "s3_website_endpoint" {
  description = "S3 bucket website endpoint"
  type        = string
}

variable "api_gateway_id" {
  description = "API Gateway REST API ID"
  type        = string
}

variable "api_stage_name" {
  description = "API Gateway stage name"
  type        = string
}

variable "aws_region" {
  description = "AWS region for API Gateway origin (empty = current region)"
  type        = string
  default     = ""
}

variable "api_path_pattern" {
  description = "CloudFront path pattern for API routes"
  type        = string
  default     = "/api/*"
}

variable "api_forwarded_headers" {
  description = "Headers to forward to API origin"
  type        = list(string)
  default     = ["Authorization", "Content-Type"]
}

variable "price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_100"
}
