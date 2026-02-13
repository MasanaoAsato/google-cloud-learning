locals {
  # General values
  prefix   = "test"
  location = "asia-northeast1"
  region   = "asia-northeast1"

  # Cloud Run values
  crun_cpu                = "1"
  crun_memory             = "512Mi"
  crun_min_instance_count = 0
  crun_max_instance_count = 3
  crun_timeout_seconds    = 30

  # load balancer values
  dns_authorization_domain         = "example.com"
  certification_domains            = ["example.com", "*.example.com"]
  certification_map_entry_hostname = "dev.example.com"
  enable_cdn                       = false
}
