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

- [google_storage_bucket.functions_source](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket) (resource)
- [google_storage_bucket.input](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket) (resource)
- [google_storage_bucket.output](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket) (resource)
- [google_project.project](https://registry.terraform.io/providers/hashicorp/google/latest/docs/data-sources/project) (data source)

## Required Inputs

The following input variables are required:

### <a name="input_prefix"></a> [prefix](#input\_prefix)

Description: Prefix for naming resources

Type: `string`

### <a name="input_region"></a> [region](#input\_region)

Description: Region for Cloud Storage buckets

Type: `string`

## Optional Inputs

No optional inputs.

## Outputs

The following outputs are exported:

### <a name="output_functions_source_bucket_name"></a> [functions\_source\_bucket\_name](#output\_functions\_source\_bucket\_name)

Description: Bucket for Cloud Functions source code ZIPs

### <a name="output_input_bucket_name"></a> [input\_bucket\_name](#output\_input\_bucket\_name)

Description: Input bucket name (Eventarc trigger source)

### <a name="output_output_bucket_name"></a> [output\_bucket\_name](#output\_output\_bucket\_name)

Description: Output bucket name (subscriber writes results here)
<!-- END_TF_DOCS -->