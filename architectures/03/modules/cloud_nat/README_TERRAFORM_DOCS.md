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

- [google_compute_address.nat_address](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_address) (resource)
- [google_compute_router.nat_router](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_router) (resource)
- [google_compute_router_nat.nat](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_router_nat) (resource)

## Required Inputs

The following input variables are required:

### <a name="input_bgp_asn"></a> [bgp\_asn](#input\_bgp\_asn)

Description: BGP ASN for Cloud Router

Type: `number`

### <a name="input_subnet_id"></a> [subnet\_id](#input\_subnet\_id)

Description: Subnet ID for the Cloud NAT

Type: `string`

### <a name="input_vpc_network_id"></a> [vpc\_network\_id](#input\_vpc\_network\_id)

Description: VPC network ID for the Cloud NAT service

Type: `string`

## Optional Inputs

The following input variables are optional (have default values):

### <a name="input_max_ports_per_vm"></a> [max\_ports\_per\_vm](#input\_max\_ports\_per\_vm)

Description: Maximum number of ports allocated to a VM from this NAT

Type: `number`

Default: `4096`

### <a name="input_min_ports_per_vm"></a> [min\_ports\_per\_vm](#input\_min\_ports\_per\_vm)

Description: Minimum number of ports allocated to a VM from this NAT

Type: `number`

Default: `64`

### <a name="input_prefix"></a> [prefix](#input\_prefix)

Description: Prefix for naming resources

Type: `string`

Default: `"test"`

### <a name="input_region"></a> [region](#input\_region)

Description: Region for resources

Type: `string`

Default: `"asia-northeast1"`

### <a name="input_tcp_established_idle_timeout_sec"></a> [tcp\_established\_idle\_timeout\_sec](#input\_tcp\_established\_idle\_timeout\_sec)

Description: Timeout (in seconds) for TCP established connections

Type: `number`

Default: `300`

### <a name="input_tcp_transitory_idle_timeout_sec"></a> [tcp\_transitory\_idle\_timeout\_sec](#input\_tcp\_transitory\_idle\_timeout\_sec)

Description: Timeout (in seconds) for TCP transitory connections

Type: `number`

Default: `30`

## Outputs

The following outputs are exported:

### <a name="output_nat_gateway_name"></a> [nat\_gateway\_name](#output\_nat\_gateway\_name)

Description: Cloud NAT Gateway name for monitoring

### <a name="output_nat_router_name"></a> [nat\_router\_name](#output\_nat\_router\_name)

Description: Cloud NAT Router name for monitoring
<!-- END_TF_DOCS -->