variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "services" {
  description = "List of GCP APIs to enable"
  type        = list(string)
}
