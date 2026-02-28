variable "table_name" {
  description = "Name of the DynamoDB table"
  type        = string
}

variable "hash_key" {
  description = "Hash key attribute name"
  type        = string
  default     = "pk"
}

variable "range_key" {
  description = "Range key attribute name"
  type        = string
  default     = "sk"
}

variable "additional_attributes" {
  description = "Additional attribute definitions (for GSI keys)"
  type = list(object({
    name = string
    type = string
  }))
  default = []
}

variable "global_secondary_indexes" {
  description = "Global secondary index definitions"
  type = list(object({
    name            = string
    hash_key        = string
    range_key       = optional(string)
    projection_type = optional(string, "ALL")
  }))
  default = []
}

variable "ttl_attribute" {
  description = "TTL attribute name (null to disable)"
  type        = string
  default     = null
}

variable "point_in_time_recovery" {
  description = "Enable point-in-time recovery"
  type        = bool
  default     = false
}
