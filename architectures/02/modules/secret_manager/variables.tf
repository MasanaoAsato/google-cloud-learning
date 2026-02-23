variable "prefix" {
  description = "Prefix for naming resources"
  type        = string

  default = "test"
}

variable "secret_id" {
  description = "Secret name suffix (prefixed with var.prefix automatically)"
  type        = string

  default = "db-password"
}

variable "length" {
  description = "Length of the generated password"
  type        = number

  default = 16
}
