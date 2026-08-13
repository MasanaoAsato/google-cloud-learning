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

- [google_service_account.eventarc_invoker](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/service_account) (resource)
- [google_service_account.gcf_processor](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/service_account) (resource)
- [google_service_account.gcf_subscriber](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/service_account) (resource)

## Required Inputs

The following input variables are required:

### <a name="input_prefix"></a> [prefix](#input\_prefix)

Description: Prefix for naming resources

Type: `string`

## Optional Inputs

No optional inputs.

## Outputs

The following outputs are exported:

### <a name="output_eventarc_invoker_sa_email"></a> [eventarc\_invoker\_sa\_email](#output\_eventarc\_invoker\_sa\_email)

Description: Email of the Eventarc invoker SA

### <a name="output_gcf_processor_sa_email"></a> [gcf\_processor\_sa\_email](#output\_gcf\_processor\_sa\_email)

Description: Email of the processor Cloud Functions SA

### <a name="output_gcf_subscriber_sa_email"></a> [gcf\_subscriber\_sa\_email](#output\_gcf\_subscriber\_sa\_email)

Description: Email of the subscriber Cloud Functions SA
<!-- END_TF_DOCS -->