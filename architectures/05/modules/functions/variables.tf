variable "prefix" {
  description = "Prefix for naming resources"
  type        = string
}

variable "region" {
  description = "Region for Cloud Functions"
  type        = string
}

variable "gcf_processor_sa_email" {
  description = "Service account email for the processor function"
  type        = string
}

variable "gcf_subscriber_sa_email" {
  description = "Service account email for the subscriber function"
  type        = string
}

variable "functions_source_bucket_name" {
  description = "GCS bucket for storing function source ZIPs"
  type        = string
}

variable "output_bucket_name" {
  description = "GCS bucket for subscriber to write results"
  type        = string
}

variable "processor_output_topic_id" {
  description = "Pub/Sub topic ID for processor to publish messages"
  type        = string
}

variable "processor_max_instance_count" {
  description = "Max instances for processor function"
  type        = number
}

variable "processor_min_instance_count" {
  description = "Min instances for processor function"
  type        = number
}

variable "processor_available_memory" {
  description = "Available memory for processor function (e.g. '256M')"
  type        = string
}

variable "processor_timeout_seconds" {
  description = "Timeout in seconds for processor function"
  type        = number
}

variable "subscriber_max_instance_count" {
  description = "Max instances for subscriber function"
  type        = number
}

variable "subscriber_min_instance_count" {
  description = "Min instances for subscriber function"
  type        = number
}

variable "subscriber_available_memory" {
  description = "Available memory for subscriber function (e.g. '256M')"
  type        = string
}

variable "subscriber_timeout_seconds" {
  description = "Timeout in seconds for subscriber function"
  type        = number
}
