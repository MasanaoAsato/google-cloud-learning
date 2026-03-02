output "password" {
  description = "Generated DB password (sensitive)"
  value       = random_password.db.result
  sensitive   = true
}

output "secret_name" {
  description = "Secret Manager secret name"
  value       = google_secret_manager_secret.db_password.secret_id
}
