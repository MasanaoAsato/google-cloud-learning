resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.location
  repository_id = "ar-${var.prefix}"
  description   = "ar for docker images"
  format        = "DOCKER"


  docker_config {
    immutable_tags = true
  }
}
