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

- [google_dns_record_set.a_record](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/dns_record_set) (resource)
- [google_dns_record_set.cname_record](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/dns_record_set) (resource)

## Required Inputs

The following input variables are required:

### <a name="input_dns_auth_record_data"></a> [dns\_auth\_record\_data](#input\_dns\_auth\_record\_data)

Description: The data of the DNS record for key authorization.

Type: `string`

### <a name="input_dns_auth_record_name"></a> [dns\_auth\_record\_name](#input\_dns\_auth\_record\_name)

Description: The name of the DNS record for key authorization.

Type: `string`

### <a name="input_dns_auth_record_type"></a> [dns\_auth\_record\_type](#input\_dns\_auth\_record\_type)

Description: The type of the DNS record for key authorization.

Type: `string`

### <a name="input_dns_managed_zone_name"></a> [dns\_managed\_zone\_name](#input\_dns\_managed\_zone\_name)

Description: The name of the Cloud DNS managed zone.

Type: `string`

### <a name="input_domain_name"></a> [domain\_name](#input\_domain\_name)

Description: The domain name for the A record.

Type: `string`

### <a name="input_lb_ip_address"></a> [lb\_ip\_address](#input\_lb\_ip\_address)

Description: The IP address for the A record.

Type: `string`

## Optional Inputs

No optional inputs.

## Outputs

The following outputs are exported:

### <a name="output_security_policy_self_link"></a> [security\_policy\_self\_link](#output\_security\_policy\_self\_link)

Description: The self link of the Cloud Armor security policy
<!-- END_TF_DOCS -->