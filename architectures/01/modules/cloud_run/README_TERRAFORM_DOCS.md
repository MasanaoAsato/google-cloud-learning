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

- [google_cloud_run_v2_service.default](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_run_v2_service) (resource)
- [google_cloud_run_v2_service_iam_policy.noauth](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_run_v2_service_iam_policy) (resource)
- [google_iam_policy.noauth](https://registry.terraform.io/providers/hashicorp/google/latest/docs/data-sources/iam_policy) (data source)

## Required Inputs

No required inputs.

## Optional Inputs

The following input variables are optional (have default values):

### <a name="input_crun_cpu"></a> [crun\_cpu](#input\_crun\_cpu)

Description: CPU value for Cloud Run service

Type: `string`

Default: `"2"`

### <a name="input_crun_max_instance_count"></a> [crun\_max\_instance\_count](#input\_crun\_max\_instance\_count)

Description: Maximum instance count for Cloud Run service

Type: `number`

Default: `3`

### <a name="input_crun_memory"></a> [crun\_memory](#input\_crun\_memory)

Description: Memory value for Cloud Run service

Type: `string`

Default: `"256Mi"`

### <a name="input_crun_min_instance_count"></a> [crun\_min\_instance\_count](#input\_crun\_min\_instance\_count)

Description: Minimum instance count for Cloud Run service

Type: `number`

Default: `0`

### <a name="input_crun_timeout_seconds"></a> [crun\_timeout\_seconds](#input\_crun\_timeout\_seconds)

Description: Timeout in seconds for Cloud Run service

Type: `string`

Default: `"30s"`

### <a name="input_location"></a> [location](#input\_location)

Description: Location for resources

Type: `string`

Default: `"asia-northeast1"`

### <a name="input_prefix"></a> [prefix](#input\_prefix)

Description: Prefix for naming resources

Type: `string`

Default: `"test"`

## Outputs

The following outputs are exported:

### <a name="output_crun_service_name"></a> [crun\_service\_name](#output\_crun\_service\_name)

Description: The name of the Cloud Run service
<!-- END_TF_DOCS -->