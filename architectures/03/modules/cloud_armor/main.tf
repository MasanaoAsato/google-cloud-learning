resource "google_compute_security_policy" "default" {
  name = "${var.prefix}-cloud-armor-security-policy"
  type = "CLOUD_ARMOR"
}

resource "google_compute_security_policy_rule" "default_deny" {
  security_policy = google_compute_security_policy.default.name
  priority        = "2147483647"
  action          = "deny(403)"

  match {
    versioned_expr = "SRC_IPS_V1"
    config {
      src_ip_ranges = ["*"]
    }
  }
}

resource "google_compute_security_policy_rule" "allow_jp_ips" {
  security_policy = google_compute_security_policy.default.name
  priority        = "100"
  action          = "allow"

  match {
    expr {
      expression = "origin.region_code == 'JP'"
    }
  }
}
