

# =================================
# Certification Manager関連 
# =================================

resource "google_certificate_manager_dns_authorization" "lb" {
  name        = "${var.prefix}-lb-dns-auth"
  description = "DNS Authorization for Load Balancer"

  domain = var.dns_authorization_domain
  type   = "PER_PROJECT_RECORD"

}

resource "google_certificate_manager_certificate" "lb" {
  name        = "${var.prefix}-lb-cert"
  description = "Certificate for Load Balancer"
  scope       = "DEFAULT"

  managed {
    domains            = var.certification_domains
    dns_authorizations = [google_certificate_manager_dns_authorization.lb.id]
  }
}

resource "google_certificate_manager_certificate_map" "lb" {
  name        = "${var.prefix}-lb-cert-map"
  description = "Certificate Map for Load Balancer"

}

resource "google_certificate_manager_certificate_map_entry" "lb" {
  name         = "${var.prefix}-lb-cert-map-entry"
  description  = "Certificate Map Entry for Load Balancer"
  map          = google_certificate_manager_certificate_map.lb.name
  certificates = [google_certificate_manager_certificate.lb.id]
  hostname     = var.certification_map_entry_hostname
}


# =================================
# Load Balancer関連 
# =================================

# 1. グローバルIPアドレス
resource "google_compute_global_address" "lb_ip" {
  name         = "${var.prefix}-lb-ip"
  address_type = "EXTERNAL"
  ip_version   = "IPV4"
}


# 2. NEG (Network Endpoint Group) - Serverless
resource "google_compute_region_network_endpoint_group" "neg" {
  name                  = "${var.prefix}-lb-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region

  cloud_run {
    service = var.cloud_run_service_name
  }
}

# 3. バックエンドサービス
resource "google_compute_backend_service" "backend" {
  name                  = "${var.prefix}-lb-backend"
  protocol              = "HTTPS"
  port_name             = "http"
  timeout_sec           = 30
  enable_cdn            = var.enable_cdn
  load_balancing_scheme = "EXTERNAL_MANAGED"
  security_policy       = var.security_policy_self_link

  backend {
    group = google_compute_region_network_endpoint_group.neg.id
  }

  log_config {
    enable      = true
    sample_rate = 1.0
  }
}

# 4. HTTPS URL Map (メインルーティング)
resource "google_compute_url_map" "https" {
  name            = "${var.prefix}-lb-url-map"
  default_service = google_compute_backend_service.backend.id
}

# 5. HTTP→HTTPS リダイレクト用 URL Map
resource "google_compute_url_map" "http_redirect" {
  name = "${var.prefix}-lb-http-redirect"

  default_url_redirect {
    https_redirect         = true
    redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
    strip_query            = false
  }
}

# 6. HTTPプロキシ (リダイレクト用)
resource "google_compute_target_http_proxy" "http" {
  name    = "proxy-${var.prefix}-http"
  url_map = google_compute_url_map.http_redirect.id
}

# 7. SSL Policy
resource "google_compute_ssl_policy" "ssl_policy" {
  name            = "${var.prefix}-ssl-policy"
  profile         = "MODERN"
  min_tls_version = "TLS_1_2"
}

# 8. HTTPSプロキシ
resource "google_compute_target_https_proxy" "https" {
  name          = "proxy-${var.prefix}-https"
  url_map       = google_compute_url_map.https.id
  ssl_policy    = google_compute_ssl_policy.ssl_policy.id
  quic_override = "NONE"

  # Certificate Mapを参照
  certificate_map = "//certificatemanager.googleapis.com/${google_certificate_manager_certificate_map.lb.id}"
}

# 9. HTTP Forwarding Rule (ポート80)
resource "google_compute_global_forwarding_rule" "http" {
  name                  = "fwdrule-${var.prefix}-http"
  target                = google_compute_target_http_proxy.http.id
  port_range            = "80"
  ip_protocol           = "TCP"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  ip_address            = google_compute_global_address.lb_ip.id
}

# 10. HTTPS Forwarding Rule (ポート443)
resource "google_compute_global_forwarding_rule" "https" {
  name                  = "fwdrule-${var.prefix}-https"
  target                = google_compute_target_https_proxy.https.id
  port_range            = "443"
  ip_protocol           = "TCP"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  ip_address            = google_compute_global_address.lb_ip.id
}
