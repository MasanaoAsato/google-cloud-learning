module "network" {
  source = "../modules/network"
  prefix = local.prefix
  region = local.region
}

module "cloud_armor" {
  source = "../modules/cloud_armor"
  prefix = local.prefix
}

module "cloud_run" {
  source                  = "../modules/cloud_run"
  prefix                  = local.prefix
  location                = local.location
  vpc_network_id          = module.network.vpc_network_id
  subnet_id               = module.network.subnet_id
  crun_cpu                = local.crun_cpu
  crun_memory             = local.crun_memory
  crun_min_instance_count = local.crun_min_instance_count
  crun_max_instance_count = local.crun_max_instance_count
  crun_timeout_seconds    = local.crun_timeout_seconds
}

module "load_balancer" {
  source                           = "../modules/load_balancer"
  prefix                           = local.prefix
  region                           = local.region
  dns_authorization_domain         = local.dns_authorization_domain
  certification_domains            = local.certification_domains
  certification_map_entry_hostname = local.certification_map_entry_hostname
  cloud_run_service_name           = module.cloud_run.crun_service_name
  enable_cdn                       = local.enable_cdn
  security_policy_self_link        = module.cloud_armor.security_policy_self_link

  depends_on = [module.cloud_run, module.cloud_armor]
}

module "cloud_dns" {
  source                    = "../modules/cloud_dns"
  dns_managed_zone_name     = local.dns_managed_zone_name
  dns_managed_zone_dns_name = local.dns_managed_zone_dns_name
  domain_name               = local.certification_map_entry_hostname
  lb_ip_address             = module.load_balancer.lb_ip_address
  dns_auth_record_name      = module.load_balancer.dns_auth_record_name
  dns_auth_record_type      = module.load_balancer.dns_auth_record_type
  dns_auth_record_data      = module.load_balancer.dns_auth_record_data

  depends_on = [module.load_balancer]
}

module "artifact_registry" {
  source   = "../modules/artifact_registry"
  prefix   = local.prefix
  location = local.location
}

module "cloud_nat" {
  source                           = "../modules/cloud_nat"
  prefix                           = local.prefix
  region                           = local.region
  vpc_network_id                   = module.network.vpc_network_id
  subnet_id                        = module.network.subnet_id
  bgp_asn                          = local.bgp_asn
  min_ports_per_vm                 = local.min_ports_per_vm
  max_ports_per_vm                 = local.max_ports_per_vm
  tcp_established_idle_timeout_sec = local.tcp_established_idle_timeout_sec
  tcp_transitory_idle_timeout_sec  = local.tcp_transitory_idle_timeout_sec
}
