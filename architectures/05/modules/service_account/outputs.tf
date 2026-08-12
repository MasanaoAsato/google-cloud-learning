output "gcf_processor_sa_email" {
  value       = google_service_account.gcf_processor.email
  description = "Email of the processor Cloud Functions SA"
}

output "gcf_subscriber_sa_email" {
  value       = google_service_account.gcf_subscriber.email
  description = "Email of the subscriber Cloud Functions SA"
}

output "eventarc_invoker_sa_email" {
  value       = google_service_account.eventarc_invoker.email
  description = "Email of the Eventarc invoker SA"
}
