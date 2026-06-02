output "security_policy_self_link" {
  description = "The self link of the Cloud Armor security policy"
  value       = google_compute_security_policy.default.self_link
}
