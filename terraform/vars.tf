variable "okta_org_name" {
  description = "The Okta organization name (e.g., dev-123456)"
  type        = string
}

variable "okta_api_token" {
  description = "The Okta API token"
  type        = string
  sensitive   = true
}