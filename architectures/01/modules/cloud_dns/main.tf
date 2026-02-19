resource "google_dns_managed_zone" "default" {
  name        = var.dns_managed_zone_name
  dns_name    = var.dns_managed_zone_dns_name
  description = "Managed zone for ${var.domain_name}"
}

resource "google_dns_record_set" "a_record" {
  name         = "${var.domain_name}."
  type         = "A"
  ttl          = 300
  managed_zone = google_dns_managed_zone.default.name
  rrdatas      = [var.lb_ip_address]
}

resource "google_dns_record_set" "cname_record" {
  name         = var.dns_auth_record_name
  type         = var.dns_auth_record_type
  ttl          = 300
  managed_zone = google_dns_managed_zone.default.name
  rrdatas      = [var.dns_auth_record_data]
}
