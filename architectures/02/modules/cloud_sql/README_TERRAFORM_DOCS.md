<!-- BEGIN_TF_DOCS -->
## Requirements

No requirements.

## Providers

The following providers are used by this module:

- <a name="provider_google"></a> [google](#provider\_google) (7.20.0)

## Modules

No modules.

## Resources

The following resources are used by this module:

- [google_sql_database.default](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/sql_database) (resource)
- [google_sql_database_instance.main](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/sql_database_instance) (resource)
- [google_sql_user.app](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/sql_user) (resource)

## Required Inputs

The following input variables are required:

### <a name="input_db_password"></a> [db\_password](#input\_db\_password)

Description: Database user password (received from secret\_manager module)

Type: `string`

### <a name="input_vpc_network_self_link"></a> [vpc\_network\_self\_link](#input\_vpc\_network\_self\_link)

Description: VPC network self link

Type: `string`

## Optional Inputs

The following input variables are optional (have default values):

### <a name="input_database_version"></a> [database\_version](#input\_database\_version)

Description: Database version

Type: `string`

Default: `"POSTGRES_15"`

### <a name="input_db_password_version"></a> [db\_password\_version](#input\_db\_password\_version)

Description: Increment this value to rotate the DB password

Type: `number`

Default: `1`

### <a name="input_db_user_name"></a> [db\_user\_name](#input\_db\_user\_name)

Description: Database user name

Type: `string`

Default: `"app_user"`

### <a name="input_disk_autoresize_limit"></a> [disk\_autoresize\_limit](#input\_disk\_autoresize\_limit)

Description: Disk autoresize limit in GB

Type: `number`

Default: `1000`

### <a name="input_disk_size"></a> [disk\_size](#input\_disk\_size)

Description: Disk size in GB

Type: `number`

Default: `10`

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

### <a name="output_cloud_sql_connection_name"></a> [cloud\_sql\_connection\_name](#output\_cloud\_sql\_connection\_name)

Description: Cloud SQL connection name

### <a name="output_db_name"></a> [db\_name](#output\_db\_name)

Description: Database name

### <a name="output_db_private_ip"></a> [db\_private\_ip](#output\_db\_private\_ip)

Description: Database private IP address

### <a name="output_db_user_name"></a> [db\_user\_name](#output\_db\_user\_name)

Description: Database user name

### <a name="output_instance_name"></a> [instance\_name](#output\_instance\_name)

Description: Cloud SQL instance name
<!-- END_TF_DOCS -->