variable "function_name" {
  description = "Lambda function name"
  type        = string
}

variable "handler" {
  description = "Lambda handler (e.g. handler.lambda_handler)"
  type        = string
}

variable "runtime" {
  description = "Lambda runtime (e.g. python3.12)"
  type        = string
}

variable "architectures" {
  description = "Lambda architectures"
  type        = list(string)
  default     = ["arm64"]
}

variable "memory_size" {
  description = "Lambda memory in MB"
  type        = number
  default     = 512
}

variable "timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 30
}

variable "role_arn" {
  description = "IAM role ARN for the Lambda function"
  type        = string
}

variable "environment_variables" {
  description = "Environment variables for the Lambda function"
  type        = map(string)
  default     = {}
}

variable "source_dir" {
  description = "Path to the source directory containing Python files and requirements.txt"
  type        = string
}

variable "requirements_file" {
  description = "Name of the requirements file"
  type        = string
  default     = "requirements.txt"
}

variable "source_files_hash" {
  description = "Hash of source files to trigger rebuilds"
  type        = string
}
