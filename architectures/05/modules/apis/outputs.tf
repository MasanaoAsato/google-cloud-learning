output "enabled_services" {
  description = "Map of enabled GCP service names"
  value       = { for k, v in google_project_service.apis : k => v.service }
}
