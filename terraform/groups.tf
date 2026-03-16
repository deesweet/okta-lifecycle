resource "okta_group" "engineering" {
  name        = "Engineering"
  description = "Engineering team members"
}

resource "okta_group" "product" {
  name        = "Product"
  description = "Product team members"
}

resource "okta_group" "finance" {
  name        = "Finance"
  description = "Finance team members"
}

resource "okta_group" "hr" {
  name        = "HR"
  description = "Human Resources team members"
}

resource "okta_group" "it" {
  name        = "IT"
  description = "IT team members"
}

resource "okta_group" "contractors" {
  name        = "Contractors"
  description = "External contractors with limited access"
}

resource "okta_group" "vendors" {
  name        = "Vendors"
  description = "Third-party vendors with scoped access"
}
