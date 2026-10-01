variable "region" {
  type    = string
  default = "ap-southeast-2"
}

variable "name" {
  description = "Prefix for all resources"
  type        = string
  default     = "loan-api-lab"
}

variable "github_repo" {
  description = "GitHub repo allowed to deploy (owner/name). Students: set this to YOUR fork."
  type        = string
  default     = "eddiez0719/loan-api-lab"
}

variable "create_github_oidc_provider" {
  description = "Set to false if the AWS account already has the token.actions.githubusercontent.com OIDC provider."
  type        = bool
  default     = true
}

variable "desired_count" {
  type    = number
  default = 1
}
