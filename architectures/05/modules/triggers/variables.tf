variable "prefix" {
  description = "Prefix for naming resources"
  type        = string
}

variable "region" {
  description = "Region for resources"
  type        = string
}

variable "eventarc_invoker_sa_email" {
  description = "Service account email used for Eventarc invocation and Push subscription OIDC token"
  type        = string
}

variable "input_bucket_name" {
  description = "Input GCS bucket name (trigger source for processor)"
  type        = string
}

variable "processor_function_name" {
  description = "Cloud Run service name of the processor function"
  type        = string
}

variable "eventarc_max_attempts" {
  description = "Max retry attempts for the GCS → processor Eventarc trigger"
  type        = number
}

variable "processor_output_topic_name" {
  description = "Pub/Sub topic name for processor output"
  type        = string
}

variable "subscriber_function_uri" {
  description = "URI of the subscriber Cloud Function (push endpoint)"
  type        = string
}

variable "dlq_topic_id" {
  description = "Full ID of the Dead Letter Queue topic"
  type        = string
}

variable "max_delivery_attempts" {
  description = "Max delivery attempts before forwarding to DLQ (min: 5, max: 100)"
  type        = number

  validation {
    condition     = var.max_delivery_attempts >= 5 && var.max_delivery_attempts <= 100
    error_message = "max_delivery_attempts must be between 5 and 100."
  }
}

variable "message_retention_duration" {
  description = "Message retention duration for the subscriber subscription"
  type        = string
}
