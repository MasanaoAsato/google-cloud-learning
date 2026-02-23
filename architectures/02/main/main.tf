module "network" {
  source = "../modules/network"

  prefix = local.prefix
}


module "secret_manager" {
  source = "../modules/secret_manager"

  prefix    = local.prefix
  secret_id = local.secret_manager_secret_id
}

module "cloud_sql" {
  source = "../modules/cloud_sql"

  prefix                = local.prefix
  region                = local.region
  vpc_network_self_link = module.network.vpc_network_self_link
  db_password           = module.secret_manager.password
  db_password_version   = local.db_password_version
  disk_size             = local.disk_size
  disk_autoresize_limit = local.disk_autoresize_limit
  db_user_name          = local.db_user_name

  depends_on = [module.secret_manager]
}

module "service_account" {
  source     = "../modules/service_account"
  project_id = local.project_id
  prefix     = local.prefix
}

module "cloud_run" {
  source = "../modules/cloud_run"

  prefix                  = local.prefix
  vpc_network_id          = module.network.vpc_network_id
  subnet_id               = module.network.subnet_id
  crun_cpu                = local.crun_cpu
  crun_memory             = local.crun_memory
  crun_min_instance_count = local.crun_min_instance_count
  crun_max_instance_count = local.crun_max_instance_count
  crun_timeout_seconds    = local.crun_timeout_seconds
  service_account_email   = module.service_account.service_account_email
  secret_name             = module.secret_manager.secret_name
  db_user_name            = module.cloud_sql.db_user_name
  db_private_ip           = module.cloud_sql.db_private_ip
  db_name                 = module.cloud_sql.db_name

  depends_on = [module.secret_manager, module.cloud_sql, module.service_account]
}

