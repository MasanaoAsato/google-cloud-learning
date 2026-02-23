<!-- BEGIN_TF_DOCS -->
## Requirements

No requirements.

## Providers

The following providers are used by this module:

- <a name="provider_google"></a> [google](#provider\_google) (7.20.0)

- <a name="provider_random"></a> [random](#provider\_random) (3.8.1)

## Modules

No modules.

## Resources

The following resources are used by this module:

- [google_secret_manager_secret.db_password](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/secret_manager_secret) (resource)
- [google_secret_manager_secret_version.db_password](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/secret_manager_secret_version) (resource)
- [random_password.db](https://registry.terraform.io/providers/hashicorp/random/latest/docs/resources/password) (resource)

## Required Inputs

No required inputs.

## Optional Inputs

The following input variables are optional (have default values):

### <a name="input_length"></a> [length](#input\_length)

Description: Length of the generated password

Type: `number`

Default: `16`

### <a name="input_prefix"></a> [prefix](#input\_prefix)

Description: Prefix for naming resources

Type: `string`

Default: `"test"`

### <a name="input_secret_id"></a> [secret\_id](#input\_secret\_id)

Description: Secret name suffix (prefixed with var.prefix automatically)

Type: `string`

Default: `"db-password"`

## Outputs

The following outputs are exported:

### <a name="output_password"></a> [password](#output\_password)

Description: Generated DB password (sensitive)

### <a name="output_secret_name"></a> [secret\_name](#output\_secret\_name)

Description: Secret Manager secret name
<!-- END_TF_DOCS -->