module "network" {
  source = "../modules/network"

  prefix = local.prefix
}

module "gke" {
  source = "../modules/gke"

  prefix                       = local.prefix
  location                     = local.location
  vpc_network_id               = module.network.vpc_network_id
  subnet_id                    = module.network.subnet_id
  subnet_pod_ip_range_name     = module.network.subnet_pod_ip_range_name
  subnet_service_ip_range_name = module.network.subnet_service_ip_range_name
}

module "service_account" {
  source     = "../modules/service_account"
  prefix     = local.prefix
  project_id = local.project_id

  depends_on = [module.gke]
}
