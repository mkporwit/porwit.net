variable "resource_group_name" {
    type = string
    default = "CoreInfrastructure"
    description = "Name of Resource Group for Core Infrastructure resources"
}

variable "availability_zone_name" {
  type        = string
  default     = "westus2"
  description = "AZ for CoreInfrastructure Resource Group"
}

variable "domain_name" {
    type        = string
    default     = "porwit.net"
}