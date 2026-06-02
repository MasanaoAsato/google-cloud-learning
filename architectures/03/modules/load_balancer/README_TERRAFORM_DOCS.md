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

- [google_certificate_manager_certificate.lb](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/certificate_manager_certificate) (resource)
- [google_certificate_manager_certificate_map.lb](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/certificate_manager_certificate_map) (resource)
- [google_certificate_manager_certificate_map_entry.lb](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/certificate_manager_certificate_map_entry) (resource)
- [google_certificate_manager_dns_authorization.lb](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/certificate_manager_dns_authorization) (resource)
- [google_compute_backend_service.backend](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_backend_service) (resource)
- [google_compute_global_address.lb_ip](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_global_address) (resource)
- [google_compute_global_forwarding_rule.http](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_global_forwarding_rule) (resource)
- [google_compute_global_forwarding_rule.https](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_global_forwarding_rule) (resource)
- [google_compute_region_network_endpoint_group.neg](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_region_network_endpoint_group) (resource)
- [google_compute_ssl_policy.ssl_policy](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_ssl_policy) (resource)
- [google_compute_target_http_proxy.http](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_target_http_proxy) (resource)
- [google_compute_target_https_proxy.https](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_target_https_proxy) (resource)
- [google_compute_url_map.http_redirect](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_url_map) (resource)
- [google_compute_url_map.https](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_url_map) (resource)

## Required Inputs

The following input variables are required:

### <a name="input_certification_domains"></a> [certification\_domains](#input\_certification\_domains)

Description: List of domains for certificate management

Type: `list(string)`

### <a name="input_certification_map_entry_hostname"></a> [certification\_map\_entry\_hostname](#input\_certification\_map\_entry\_hostname)

Description: Hostname for certificate map entry

Type: `string`

### <a name="input_cloud_run_service_name"></a> [cloud\_run\_service\_name](#input\_cloud\_run\_service\_name)

Description: Cloud Run service name to be used in the Load Balancer

Type: `string`

### <a name="input_dns_authorization_domain"></a> [dns\_authorization\_domain](#input\_dns\_authorization\_domain)

Description: Domain for DNS authorization

Type: `string`

### <a name="input_security_policy_self_link"></a> [security\_policy\_self\_link](#input\_security\_policy\_self\_link)

Description: Security policy for the Load Balancer

Type: `string`

## Optional Inputs

The following input variables are optional (have default values):

### <a name="input_enable_cdn"></a> [enable\_cdn](#input\_enable\_cdn)

Description: Whether to enable CDN for the Load Balancer

Type: `bool`

Default: `false`

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

### <a name="output_dns_auth_record_data"></a> [dns\_auth\_record\_data](#output\_dns\_auth\_record\_data)

Description: The data of the DNS record for certificate authorization

### <a name="output_dns_auth_record_name"></a> [dns\_auth\_record\_name](#output\_dns\_auth\_record\_name)

Description: The name of the DNS record for certificate authorization

### <a name="output_dns_auth_record_type"></a> [dns\_auth\_record\_type](#output\_dns\_auth\_record\_type)

Description: The type of the DNS record for certificate authorization

### <a name="output_lb_ip_address"></a> [lb\_ip\_address](#output\_lb\_ip\_address)

Description: The global IP address of the load balancer
<!-- END_TF_DOCS -->