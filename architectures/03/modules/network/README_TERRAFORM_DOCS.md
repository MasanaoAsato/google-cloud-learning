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

- [google_compute_network.vpc_network](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_network) (resource)
- [google_compute_subnetwork.nat](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_subnetwork) (resource)

## Required Inputs

No required inputs.

## Optional Inputs

The following input variables are optional (have default values):

### <a name="input_prefix"></a> [prefix](#input\_prefix)

Description: Prefix for naming resources

Type: `string`

Default: `"test"`

### <a name="input_region"></a> [region](#input\_region)

Description: Region for resources

Type: `string`

Default: `"asia-northeast1"`

## Outputs

The following outputs are exported:

### <a name="output_subnet_id"></a> [subnet\_id](#output\_subnet\_id)

Description: The ID of the subnetwork

### <a name="output_vpc_network_id"></a> [vpc\_network\_id](#output\_vpc\_network\_id)

Description: The ID of the VPC network
<!-- END_TF_DOCS -->