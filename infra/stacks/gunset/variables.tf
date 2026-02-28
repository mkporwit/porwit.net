variable "domain_name" {
  description = "Custom domain name for CloudFront"
  type        = string
  default     = "gunset.porwit.net"
}

variable "certificate_arn" {
  description = "ACM certificate ARN in us-east-1"
  type        = string
  default     = "arn:aws:acm:us-east-1:569397624996:certificate/8aee7563-ef07-44eb-9e1c-071ddcd3f5b0"
}

variable "frontend_url" {
  description = "Frontend URL for CORS headers"
  type        = string
  default     = "https://gunset.porwit.net"
}

variable "from_email" {
  description = "Verified SES email address for sending magic links"
  type        = string
  default     = "mkporwit@porwit.net"
}
