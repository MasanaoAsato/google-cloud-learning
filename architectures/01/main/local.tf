locals {
  # General values
  prefix     = "test"
  project_id = "your-gcp-project-id"
  location   = "asia-northeast1"
  region     = "asia-northeast1"

  # Cloud DNS values
  dns_managed_zone_name     = "example-zone"
  dns_managed_zone_dns_name = "mystudy.com."

  # Cloud Run values
  crun_cpu                = "1"
  crun_memory             = "512Mi"
  crun_min_instance_count = 0
  crun_max_instance_count = 3
  crun_timeout_seconds    = "30s"

  # load balancer values
  dns_authorization_domain         = "mystudy.com"
  certification_domains            = ["mystudy.com", "*.mystudy.com"]
  certification_map_entry_hostname = "dev.mystudy.com"
  enable_cdn                       = false
}
