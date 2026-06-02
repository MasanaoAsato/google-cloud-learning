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

- [google_compute_security_policy.default](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_security_policy) (resource)
- [google_compute_security_policy_rule.allow_jp_ips](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_security_policy_rule) (resource)
- [google_compute_security_policy_rule.default_deny](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_security_policy_rule) (resource)

## Required Inputs

No required inputs.

## Optional Inputs

The following input variables are optional (have default values):

### <a name="input_prefix"></a> [prefix](#input\_prefix)

Description: Prefix for naming resources

Type: `string`

Default: `"test"`

## Outputs

The following outputs are exported:

### <a name="output_security_policy_self_link"></a> [security\_policy\_self\_link](#output\_security\_policy\_self\_link)

Description: The self link of the Cloud Armor security policy
<!-- END_TF_DOCS -->