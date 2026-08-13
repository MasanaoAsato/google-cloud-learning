variable "prefix" {
  description = "Prefix for naming resources"
  type        = string
}

variable "message_retention_duration" {
  description = "Message retention duration for the processor output topic (e.g. '86600s')"
  type        = string
}

variable "dlq_message_retention_duration" {
  description = "Message retention duration for the DLQ topic (e.g. '604800s')"
  type        = string
}
