output "crun_service_name" {
  description = "The name of the Cloud Run service"
  value       = google_cloud_run_v2_service.default.name
}
