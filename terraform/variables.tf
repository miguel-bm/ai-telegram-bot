variable "aws_profile" {}
variable "aws_region" {}
variable "app_name" {}
variable "env_name" {}
variable "env_vars" {
  type    = map(string)
  default = {}
}
