output "group_ids" {
  description = "Okta group IDs for use by the CLI and n8n workflows"
  value = {
    engineering = okta_group.engineering.id
    product     = okta_group.product.id
    finance     = okta_group.finance.id
    hr          = okta_group.hr.id
    it          = okta_group.it.id
    contractors = okta_group.contractors.id
    vendors     = okta_group.vendors.id
  }
}