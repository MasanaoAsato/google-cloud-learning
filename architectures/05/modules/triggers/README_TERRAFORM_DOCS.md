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

- [google_eventarc_trigger.gcs_to_processor](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/eventarc_trigger) (resource)
- [google_pubsub_subscription.subscriber](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/pubsub_subscription) (resource)

## Required Inputs

The following input variables are required:

### <a name="input_dlq_topic_id"></a> [dlq\_topic\_id](#input\_dlq\_topic\_id)

Description: Full ID of the Dead Letter Queue topic

Type: `string`

### <a name="input_eventarc_invoker_sa_email"></a> [eventarc\_invoker\_sa\_email](#input\_eventarc\_invoker\_sa\_email)

Description: Service account email used for Eventarc invocation and Push subscription OIDC token

Type: `string`

### <a name="input_eventarc_max_attempts"></a> [eventarc\_max\_attempts](#input\_eventarc\_max\_attempts)

Description: Max retry attempts for the GCS → processor Eventarc trigger

Type: `number`

### <a name="input_input_bucket_name"></a> [input\_bucket\_name](#input\_input\_bucket\_name)

Description: Input GCS bucket name (trigger source for processor)

Type: `string`

### <a name="input_max_delivery_attempts"></a> [max\_delivery\_attempts](#input\_max\_delivery\_attempts)

Description: Max delivery attempts before forwarding to DLQ (min: 5, max: 100)

Type: `number`

### <a name="input_message_retention_duration"></a> [message\_retention\_duration](#input\_message\_retention\_duration)

Description: Message retention duration for the subscriber subscription

Type: `string`

### <a name="input_prefix"></a> [prefix](#input\_prefix)

Description: Prefix for naming resources

Type: `string`

### <a name="input_processor_function_name"></a> [processor\_function\_name](#input\_processor\_function\_name)

Description: Cloud Run service name of the processor function

Type: `string`

### <a name="input_processor_output_topic_name"></a> [processor\_output\_topic\_name](#input\_processor\_output\_topic\_name)

Description: Pub/Sub topic name for processor output

Type: `string`

### <a name="input_region"></a> [region](#input\_region)

Description: Region for resources

Type: `string`

### <a name="input_subscriber_function_uri"></a> [subscriber\_function\_uri](#input\_subscriber\_function\_uri)

Description: URI of the subscriber Cloud Function (push endpoint)

Type: `string`

## Optional Inputs

No optional inputs.

## Outputs

No outputs.
<!-- END_TF_DOCS -->