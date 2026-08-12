variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "Region for Cloud Run services"
  type        = string
}

variable "gcf_processor_sa_email" {
  description = "Service account email of the processor function"
  type        = string
}

variable "gcf_subscriber_sa_email" {
  description = "Service account email of the subscriber function"
  type        = string
}

variable "eventarc_invoker_sa_email" {
  description = "Service account email for Eventarc to invoke Cloud Run"
  type        = string
}

variable "input_bucket_name" {
  description = "Input GCS bucket name"
  type        = string
}

variable "output_bucket_name" {
  description = "Output GCS bucket name"
  type        = string
}

variable "processor_output_topic_name" {
  description = "Pub/Sub topic name for processor output"
  type        = string
}

variable "dlq_topic_name" {
  description = "Pub/Sub topic name for Dead Letter Queue"
  type        = string
}

variable "processor_function_name" {
  description = "Cloud Run service name of the processor function"
  type        = string
}

variable "subscriber_function_name" {
  description = "Cloud Run service name of the subscriber function"
  type        = string
}
