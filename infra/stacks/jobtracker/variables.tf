variable "domain_name" {
  description = "Custom domain name for CloudFront"
  type        = string
  default     = "jobtracker.porwit.net"
}

variable "certificate_arn" {
  description = "ACM certificate ARN in us-east-1"
  type        = string
  default     = "arn:aws:acm:us-east-1:569397624996:certificate/73f1d25d-4c94-4b7a-9d1e-2f4643b48987"
}

variable "frontend_url" {
  description = "Frontend URL for CORS headers"
  type        = string
  default     = "https://jobtracker.porwit.net"
}
