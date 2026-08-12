output "processor_output_topic_id" {
  value       = google_pubsub_topic.processor_output.id
  description = "Full ID of the processor output Pub/Sub topic"
}

output "processor_output_topic_name" {
  value       = google_pubsub_topic.processor_output.name
  description = "Short name of the processor output Pub/Sub topic"
}

output "dlq_topic_id" {
  value       = google_pubsub_topic.dlq.id
  description = "Full ID of the Dead Letter Queue topic"
}

output "dlq_topic_name" {
  value       = google_pubsub_topic.dlq.name
  description = "Short name of the Dead Letter Queue topic"
}
