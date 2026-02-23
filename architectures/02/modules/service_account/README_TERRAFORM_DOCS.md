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

- [google_project_iam_member.cloud_run_invoker](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/project_iam_member) (resource)
- [google_project_iam_member.secret_accessor](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/project_iam_member) (resource)
- [google_service_account.cloud_run](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/service_account) (resource)

## Required Inputs

The following input variables are required:

### <a name="input_prefix"></a> [prefix](#input\_prefix)

Description: Prefix for naming resources

Type: `string`

### <a name="input_project_id"></a> [project\_id](#input\_project\_id)

Description: The project ID

Type: `string`

## Optional Inputs

No optional inputs.

## Outputs

The following outputs are exported:

### <a name="output_service_account_email"></a> [service\_account\_email](#output\_service\_account\_email)

Description: The email of the created service account
<!-- END_TF_DOCS -->