<!-- BEGIN_TF_DOCS -->
## Requirements

No requirements.

## Providers

The following providers are used by this module:

- <a name="provider_archive"></a> [archive](#provider\_archive)

- <a name="provider_google"></a> [google](#provider\_google)

## Modules

No modules.

## Resources

The following resources are used by this module:

- [google_cloudfunctions2_function.processor](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloudfunctions2_function) (resource)
- [google_cloudfunctions2_function.subscriber](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloudfunctions2_function) (resource)
- [google_storage_bucket_object.processor_source](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket_object) (resource)
- [google_storage_bucket_object.subscriber_source](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket_object) (resource)
- [archive_file.processor](https://registry.terraform.io/providers/hashicorp/archive/latest/docs/data-sources/file) (data source)
- [archive_file.subscriber](https://registry.terraform.io/providers/hashicorp/archive/latest/docs/data-sources/file) (data source)

## Required Inputs

The following input variables are required:

### <a name="input_functions_source_bucket_name"></a> [functions\_source\_bucket\_name](#input\_functions\_source\_bucket\_name)

Description: GCS bucket for storing function source ZIPs

Type: `string`

### <a name="input_gcf_processor_sa_email"></a> [gcf\_processor\_sa\_email](#input\_gcf\_processor\_sa\_email)

Description: Service account email for the processor function

Type: `string`

### <a name="input_gcf_subscriber_sa_email"></a> [gcf\_subscriber\_sa\_email](#input\_gcf\_subscriber\_sa\_email)

Description: Service account email for the subscriber function

Type: `string`

### <a name="input_output_bucket_name"></a> [output\_bucket\_name](#input\_output\_bucket\_name)

Description: GCS bucket for subscriber to write results

Type: `string`

### <a name="input_prefix"></a> [prefix](#input\_prefix)

Description: Prefix for naming resources

Type: `string`

### <a name="input_processor_available_memory"></a> [processor\_available\_memory](#input\_processor\_available\_memory)

Description: Available memory for processor function (e.g. '256M')

Type: `string`

### <a name="input_processor_max_instance_count"></a> [processor\_max\_instance\_count](#input\_processor\_max\_instance\_count)

Description: Max instances for processor function

Type: `number`

### <a name="input_processor_min_instance_count"></a> [processor\_min\_instance\_count](#input\_processor\_min\_instance\_count)

Description: Min instances for processor function

Type: `number`

### <a name="input_processor_output_topic_id"></a> [processor\_output\_topic\_id](#input\_processor\_output\_topic\_id)

Description: Pub/Sub topic ID for processor to publish messages

Type: `string`

### <a name="input_processor_timeout_seconds"></a> [processor\_timeout\_seconds](#input\_processor\_timeout\_seconds)

Description: Timeout in seconds for processor function

Type: `number`

### <a name="input_region"></a> [region](#input\_region)

Description: Region for Cloud Functions

Type: `string`

### <a name="input_subscriber_available_memory"></a> [subscriber\_available\_memory](#input\_subscriber\_available\_memory)

Description: Available memory for subscriber function (e.g. '256M')

Type: `string`

### <a name="input_subscriber_max_instance_count"></a> [subscriber\_max\_instance\_count](#input\_subscriber\_max\_instance\_count)

Description: Max instances for subscriber function

Type: `number`

### <a name="input_subscriber_min_instance_count"></a> [subscriber\_min\_instance\_count](#input\_subscriber\_min\_instance\_count)

Description: Min instances for subscriber function

Type: `number`

### <a name="input_subscriber_timeout_seconds"></a> [subscriber\_timeout\_seconds](#input\_subscriber\_timeout\_seconds)

Description: Timeout in seconds for subscriber function

Type: `number`

## Optional Inputs

No optional inputs.

## Outputs

The following outputs are exported:

### <a name="output_processor_function_name"></a> [processor\_function\_name](#output\_processor\_function\_name)

Description: Cloud Run service name of the processor function

### <a name="output_processor_function_uri"></a> [processor\_function\_uri](#output\_processor\_function\_uri)

Description: URI of the processor Cloud Function

### <a name="output_subscriber_function_name"></a> [subscriber\_function\_name](#output\_subscriber\_function\_name)

Description: Cloud Run service name of the subscriber function

### <a name="output_subscriber_function_uri"></a> [subscriber\_function\_uri](#output\_subscriber\_function\_uri)

Description: URI of the subscriber Cloud Function
<!-- END_TF_DOCS -->
