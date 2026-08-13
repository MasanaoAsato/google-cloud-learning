module "apis" {
  source = "../modules/apis"

  project_id = local.project_id
  services   = local.required_apis
}

module "service_account" {
  source = "../modules/service_account"

  prefix = local.prefix

  depends_on = [module.apis]
}

module "storage" {
  source = "../modules/storage"

  prefix = local.prefix
  region = local.region

  depends_on = [module.service_account]
}

module "topics" {
  source = "../modules/topics"

  prefix                         = local.prefix
  message_retention_duration     = local.message_retention_duration
  dlq_message_retention_duration = local.dlq_message_retention_duration

  depends_on = [module.apis]
}

module "functions" {
  source = "../modules/functions"

  prefix = local.prefix
  region = local.region

  gcf_processor_sa_email       = module.service_account.gcf_processor_sa_email
  gcf_subscriber_sa_email      = module.service_account.gcf_subscriber_sa_email
  functions_source_bucket_name = module.storage.functions_source_bucket_name
  output_bucket_name           = module.storage.output_bucket_name
  processor_output_topic_id    = module.topics.processor_output_topic_id

  processor_max_instance_count = local.processor_max_instance_count
  processor_min_instance_count = local.processor_min_instance_count
  processor_available_memory   = local.processor_available_memory
  processor_timeout_seconds    = local.processor_timeout_seconds

  subscriber_max_instance_count = local.subscriber_max_instance_count
  subscriber_min_instance_count = local.subscriber_min_instance_count
  subscriber_available_memory   = local.subscriber_available_memory
  subscriber_timeout_seconds    = local.subscriber_timeout_seconds

  depends_on = [module.service_account, module.storage, module.topics]
}

module "triggers" {
  source = "../modules/triggers"

  prefix = local.prefix
  region = local.region

  eventarc_invoker_sa_email   = module.service_account.eventarc_invoker_sa_email
  input_bucket_name           = module.storage.input_bucket_name
  processor_function_name     = module.functions.processor_function_name
  subscriber_function_uri     = module.functions.subscriber_function_uri
  processor_output_topic_name = module.topics.processor_output_topic_name
  dlq_topic_id                = module.topics.dlq_topic_id
  max_delivery_attempts       = local.max_delivery_attempts
  message_retention_duration  = local.message_retention_duration
  eventarc_max_attempts       = local.eventarc_max_attempts

  depends_on = [module.service_account, module.storage, module.functions, module.topics, module.iam]
}

module "iam" {
  source = "../modules/iam"

  project_id = local.project_id
  region     = local.region

  gcf_processor_sa_email    = module.service_account.gcf_processor_sa_email
  gcf_subscriber_sa_email   = module.service_account.gcf_subscriber_sa_email
  eventarc_invoker_sa_email = module.service_account.eventarc_invoker_sa_email

  input_bucket_name  = module.storage.input_bucket_name
  output_bucket_name = module.storage.output_bucket_name

  processor_output_topic_name = module.topics.processor_output_topic_name
  dlq_topic_name              = module.topics.dlq_topic_name

  processor_function_name  = module.functions.processor_function_name
  subscriber_function_name = module.functions.subscriber_function_name

  depends_on = [
    module.service_account,
    module.storage,
    module.topics,
    module.functions,
  ]
}
