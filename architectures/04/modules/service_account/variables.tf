variable "prefix" {
  description = "Prefix for naming resources"
  type        = string

  default = "test"
}

variable "location" {
  description = "Location for resources"
  type        = string

  default = "asia-northeast1"
}

variable "project_id" {
  description = "The ID of the project"
  type        = string
}
