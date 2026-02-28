variable "bucket_name" {
  description = "S3 bucket name"
  type        = string
}

variable "index_document" {
  description = "Index document for website hosting"
  type        = string
  default     = "index.html"
}

variable "error_document" {
  description = "Error document for website hosting"
  type        = string
  default     = "index.html"
}
