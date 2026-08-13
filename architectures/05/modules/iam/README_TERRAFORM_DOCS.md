<!-- BEGIN_TF_DOCS -->
## Requirements

No requirements.

## Providers

The following providers are used by this module:

- <a name="provider_google"></a> [google](#provider\_google)

## Modules

No modules.

## Resources

The following resources are used by this module:

- [google_cloud_run_v2_service_iam_member.eventarc_invoker_processor](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_run_v2_service_iam_member) (resource)
- [google_cloud_run_v2_service_iam_member.eventarc_invoker_subscriber](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_run_v2_service_iam_member) (resource)
- [google_project_iam_member.cloudfunctions_sa_artifactregistry](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/project_iam_member) (resource)
- [google_project_iam_member.eventarc_invoker_eventarc_receiver](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/project_iam_member) (resource)
- [google_project_iam_member.gcf_processor_artifactregistry](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/project_iam_member) (resource)
- [google_project_iam_member.gcf_subscriber_artifactregistry](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/project_iam_member) (resource)
- [google_project_iam_member.gcs_pubsub_publisher](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/project_iam_member) (resource)
- [google_pubsub_topic_iam_member.gcf_processor_publisher](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/pubsub_topic_iam_member) (resource)
- [google_pubsub_topic_iam_member.pubsub_sa_dlq_publisher](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/pubsub_topic_iam_member) (resource)
- [google_service_account_iam_member.pubsub_sa_token_creator](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/service_account_iam_member) (resource)
- [google_storage_bucket_iam_member.gcf_processor_input_viewer](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket_iam_member) (resource)
- [google_storage_bucket_iam_member.gcf_subscriber_output_creator](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket_iam_member) (resource)
- [google_project.project](https://registry.terraform.io/providers/hashicorp/google/latest/docs/data-sources/project) (data source)
- [google_storage_project_service_account.gcs_sa](https://registry.terraform.io/providers/hashicorp/google/latest/docs/data-sources/storage_project_service_account) (data source)

## Required Inputs

The following input variables are required:

### <a name="input_dlq_topic_name"></a> [dlq\_topic\_name](#input\_dlq\_topic\_name)

Description: Pub/Sub topic name for Dead Letter Queue

Type: `string`

### <a name="input_eventarc_invoker_sa_email"></a> [eventarc\_invoker\_sa\_email](#input\_eventarc\_invoker\_sa\_email)

Description: Service account email for Eventarc to invoke Cloud Run

Type: `string`

### <a name="input_gcf_processor_sa_email"></a> [gcf\_processor\_sa\_email](#input\_gcf\_processor\_sa\_email)

Description: Service account email of the processor function

Type: `string`

### <a name="input_gcf_subscriber_sa_email"></a> [gcf\_subscriber\_sa\_email](#input\_gcf\_subscriber\_sa\_email)

Description: Service account email of the subscriber function

Type: `string`

### <a name="input_input_bucket_name"></a> [input\_bucket\_name](#input\_input\_bucket\_name)

Description: Input GCS bucket name

Type: `string`

### <a name="input_output_bucket_name"></a> [output\_bucket\_name](#input\_output\_bucket\_name)

Description: Output GCS bucket name

Type: `string`

### <a name="input_processor_function_name"></a> [processor\_function\_name](#input\_processor\_function\_name)

Description: Cloud Run service name of the processor function

Type: `string`

### <a name="input_processor_output_topic_name"></a> [processor\_output\_topic\_name](#input\_processor\_output\_topic\_name)

Description: Pub/Sub topic name for processor output

Type: `string`

### <a name="input_project_id"></a> [project\_id](#input\_project\_id)

Description: GCP Project ID

Type: `string`

### <a name="input_region"></a> [region](#input\_region)

Description: Region for Cloud Run services

Type: `string`

### <a name="input_subscriber_function_name"></a> [subscriber\_function\_name](#input\_subscriber\_function\_name)

Description: Cloud Run service name of the subscriber function

Type: `string`

## Optional Inputs

No optional inputs.

## Outputs

No outputs.
<!-- END_TF_DOCS -->