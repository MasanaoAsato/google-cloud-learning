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

- [google_project_service.apis](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/project_service) (resource)

## Required Inputs

The following input variables are required:

### <a name="input_project_id"></a> [project\_id](#input\_project\_id)

Description: GCP Project ID

Type: `string`

### <a name="input_services"></a> [services](#input\_services)

Description: List of GCP APIs to enable

Type: `list(string)`

## Optional Inputs

No optional inputs.

## Outputs

The following outputs are exported:

### <a name="output_enabled_services"></a> [enabled\_services](#output\_enabled\_services)

Description: Map of enabled GCP service names
<!-- END_TF_DOCS -->