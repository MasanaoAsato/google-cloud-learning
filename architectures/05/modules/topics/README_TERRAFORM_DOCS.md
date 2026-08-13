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

- [google_pubsub_subscription.dlq_monitor](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/pubsub_subscription) (resource)
- [google_pubsub_topic.dlq](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/pubsub_topic) (resource)
- [google_pubsub_topic.processor_output](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/pubsub_topic) (resource)

## Required Inputs

The following input variables are required:

### <a name="input_dlq_message_retention_duration"></a> [dlq\_message\_retention\_duration](#input\_dlq\_message\_retention\_duration)

Description: Message retention duration for the DLQ topic (e.g. '604800s')

Type: `string`

### <a name="input_message_retention_duration"></a> [message\_retention\_duration](#input\_message\_retention\_duration)

Description: Message retention duration for the processor output topic (e.g. '86600s')

Type: `string`

### <a name="input_prefix"></a> [prefix](#input\_prefix)

Description: Prefix for naming resources

Type: `string`

## Optional Inputs

No optional inputs.

## Outputs

The following outputs are exported:

### <a name="output_dlq_topic_id"></a> [dlq\_topic\_id](#output\_dlq\_topic\_id)

Description: Full ID of the Dead Letter Queue topic

### <a name="output_dlq_topic_name"></a> [dlq\_topic\_name](#output\_dlq\_topic\_name)

Description: Short name of the Dead Letter Queue topic

### <a name="output_processor_output_topic_id"></a> [processor\_output\_topic\_id](#output\_processor\_output\_topic\_id)

Description: Full ID of the processor output Pub/Sub topic

### <a name="output_processor_output_topic_name"></a> [processor\_output\_topic\_name](#output\_processor\_output\_topic\_name)

Description: Short name of the processor output Pub/Sub topic
<!-- END_TF_DOCS -->
