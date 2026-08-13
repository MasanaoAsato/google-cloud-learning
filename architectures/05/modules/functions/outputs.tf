output "processor_function_name" {
  value       = google_cloudfunctions2_function.processor.name
  description = "Cloud Run service name of the processor function"
}

output "subscriber_function_name" {
  value       = google_cloudfunctions2_function.subscriber.name
  description = "Cloud Run service name of the subscriber function"
}

output "processor_function_uri" {
  value       = google_cloudfunctions2_function.processor.service_config[0].uri
  description = "URI of the processor Cloud Function"
}

output "subscriber_function_uri" {
  value       = google_cloudfunctions2_function.subscriber.service_config[0].uri
  description = "URI of the subscriber Cloud Function"
}
