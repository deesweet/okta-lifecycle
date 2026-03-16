# ------------------------------------------------------------------------------
# Password Policies
# ------------------------------------------------------------------------------

resource "okta_policy_password" "default" {
  name            = "Default Password Policy"
  status          = "ACTIVE"
  question_recovery = "INACTIVE"
  groups_included = [
    okta_group.product.id,
    okta_group.finance.id,
    okta_group.hr.id,
  ]

  password_min_length            = 12
  password_min_uppercase         = 1
  password_min_lowercase         = 1
  password_min_number            = 1
  password_min_symbol            = 1
  password_history_count         = 5
  password_max_age_days          = 90
  password_expire_warn_days      = 14
}

resource "okta_policy_password" "privileged" {
  name            = "Privileged User Password Policy"
  status          = "ACTIVE"
  question_recovery = "INACTIVE"
  groups_included = [
    okta_group.engineering.id,
    okta_group.it.id,
  ]

  password_min_length            = 24
  password_min_uppercase         = 1
  password_min_lowercase         = 1
  password_min_number            = 1
  password_min_symbol            = 1
  password_history_count         = 10
  password_max_age_days          = 60
  password_expire_warn_days      = 14
}

resource "okta_policy_password" "external" {
  name            = "External User Password Policy"
  status          = "ACTIVE"
  question_recovery = "INACTIVE"
  groups_included = [
    okta_group.contractors.id,
    okta_group.vendors.id,
  ]

  password_min_length            = 18
  password_min_uppercase         = 1
  password_min_lowercase         = 1
  password_min_number            = 1
  password_min_symbol            = 1
  password_history_count         = 10
  password_max_age_days          = 30
  password_expire_warn_days      = 7
}

# ------------------------------------------------------------------------------
# MFA Enrollment Policies
# ------------------------------------------------------------------------------

resource "okta_factor" "okta_otp" {
  provider_id = "okta_otp"
  active      = true
}

resource "okta_factor" "fido_webauthn" {
  provider_id = "fido_webauthn"
  active      = true
}

resource "okta_policy_mfa" "default" {
  name            = "Default MFA Enrollment Policy"
  status          = "ACTIVE"
  groups_included = [
    okta_group.product.id,
    okta_group.finance.id,
    okta_group.hr.id,
  ]

  okta_password = {
    enroll = "REQUIRED"
  }

  okta_otp = {
    enroll = "REQUIRED"
  }

  fido_webauthn = {
    enroll = "OPTIONAL"
  }

  depends_on = [
    okta_factor.okta_otp,
    okta_factor.fido_webauthn,
  ]
}

resource "okta_policy_mfa" "privileged" {
  name            = "Privileged User MFA Enrollment Policy"
  status          = "ACTIVE"
  groups_included = [
    okta_group.engineering.id,
    okta_group.it.id,
  ]

  okta_password = {
    enroll = "REQUIRED"
  }

  okta_otp = {
    enroll = "REQUIRED"
  }

  fido_webauthn = {
    enroll = "REQUIRED"
  }

  depends_on = [
    okta_factor.okta_otp,
    okta_factor.fido_webauthn,
  ]
}

resource "okta_policy_mfa" "external" {
  name            = "External Party MFA Enrollment Policy"
  status          = "ACTIVE"
  groups_included = [
    okta_group.contractors.id,
    okta_group.vendors.id,
  ]

  okta_password = {
    enroll = "REQUIRED"
  }

  okta_otp = {
    enroll = "REQUIRED"
  }

  fido_webauthn = {
    enroll = "OPTIONAL"
  }

  depends_on = [
    okta_factor.okta_otp,
    okta_factor.fido_webauthn,
  ]
}

# ------------------------------------------------------------------------------
# MFA Authentication Policies
# ------------------------------------------------------------------------------

resource "okta_policy_signon" "default" {
  name            = "Default Authentication Policy"
  status          = "ACTIVE"
  groups_included = [
    okta_group.product.id,
    okta_group.finance.id,
    okta_group.hr.id,
  ]
}

resource "okta_policy_rule_signon" "default" {
  policy_id          = okta_policy_signon.default.id
  name               = "Require MFA"
  status             = "ACTIVE"
  priority           = 1
  mfa_required       = true
  mfa_remember_device = true
  mfa_prompt        = "DEVICE"
  mfa_lifetime       = 480
  session_lifetime   = 1440
  session_persistent = false
}

resource "okta_policy_signon" "privileged" {
  name            = "Privileged User Authentication Policy"
  status          = "ACTIVE"
  groups_included = [
    okta_group.engineering.id,
    okta_group.it.id,
  ]
}

resource "okta_policy_rule_signon" "privileged" {
  policy_id          = okta_policy_signon.privileged.id
  name               = "Require MFA - Strict"
  status             = "ACTIVE"
  priority           = 1
  mfa_required       = true
  mfa_remember_device = false
  mfa_prompt         = "ALWAYS"
  mfa_lifetime       = 0
  session_lifetime   = 480
  session_persistent = false
}

resource "okta_policy_signon" "external" {
  name            = "External User Authentication Policy"
  status          = "ACTIVE"
  groups_included = [
    okta_group.contractors.id,
    okta_group.vendors.id,
  ]
}

resource "okta_policy_rule_signon" "external" {
  policy_id          = okta_policy_signon.external.id
  name               = "Require MFA - Short Sessions"
  status             = "ACTIVE"
  priority           = 1
  mfa_required       = true
  mfa_remember_device = false
  mfa_prompt         = "ALWAYS"
  mfa_lifetime       = 0
  session_lifetime   = 240
  session_persistent = false
}