output "input_bucket_name" {
  value       = google_storage_bucket.input.name
  description = "Input bucket name (Eventarc trigger source)"
}

output "output_bucket_name" {
  value       = google_storage_bucket.output.name
  description = "Output bucket name (subscriber writes results here)"
}

output "functions_source_bucket_name" {
  value       = google_storage_bucket.functions_source.name
  description = "Bucket for Cloud Functions source code ZIPs"
}
