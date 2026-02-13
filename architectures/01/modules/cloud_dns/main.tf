resource "google_dns_record_set" "a_record" {
  name         = "${var.domain_name}."
  type         = "A"
  ttl          = 300
  managed_zone = var.dns_managed_zone_name
  rrdatas      = [var.lb_ip_address]
}

resource "google_dns_record_set" "cname_record" {
  name         = var.dns_auth_record_name
  type         = var.dns_auth_record_type
  ttl          = 300
  managed_zone = var.dns_managed_zone_name
  rrdatas      = [var.dns_auth_record_data]
}
