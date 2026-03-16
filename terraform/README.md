# Terraform

This directory contains the Terraform configuration that sets up the Okta environment the CLI operates against.

It manages seven Okta groups, three tiers of password policies, three MFA enrollment policies, and three sign-on (authentication) policies. The intent is to run this once to provision the baseline environment, and then use it again when group definitions or policy settings need to change.

---

## Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/install) 1.14.5 or later (uses native S3 state locking, which requires 1.10+)
- An Okta developer account and API token with admin privileges
- An AWS account and an S3 bucket for storing Terraform state
- AWS credentials available in your environment (via named profile, instance role, or environment variables)
- [1Password CLI](https://developer.1password.com/docs/cli/) (`op`) — optional but recommended

---

## What Terraform manages

### Groups

Seven groups are created:

| Group | Intended for |
|---|---|
| Engineering | Internal engineering employees |
| Product | Product managers and designers |
| Finance | Finance and accounting |
| HR | Human Resources |
| IT | IT and infrastructure |
| Contractors | External contractors with limited access |
| Vendors | Third-party vendors with scoped access |

These group definitions are in `groups.tf`. Group IDs are exported as Terraform outputs and can be used by the CLI or any other tooling that needs to reference them.

### Password policies

Policies are split into three tiers based on the risk profile of each group:

| Policy | Groups | Min length | Max age | History |
|---|---|---|---|---|
| Default | Product, Finance, HR | 12 characters | 90 days | 5 previous |
| Privileged | Engineering, IT | 24 characters | 60 days | 10 previous |
| External | Contractors, Vendors | 18 characters | 30 days | 10 previous |

All three policies require uppercase, lowercase, numbers, and symbols. Security question recovery is disabled on all three — security questions are a weak recovery path and are turned off everywhere.

Engineering and IT have access to production systems and sensitive infrastructure, so they get a longer minimum password length and a shorter rotation cycle. Contractors and Vendors are external parties whose account security is harder to verify, so they get a shorter expiry and a stricter history requirement.

### MFA enrollment policies

| Policy | Groups | TOTP | WebAuthn / FIDO2 |
|---|---|---|---|
| Default | Product, Finance, HR | Required | Optional |
| Privileged | Engineering, IT | Required | Required |
| External | Contractors, Vendors | Required | Optional |

Privileged users (Engineering, IT) must enroll a hardware or platform authenticator (WebAuthn) in addition to TOTP. For all other tiers, WebAuthn is offered but not required.

### Sign-on policies

| Policy | Groups | MFA prompt | Device trust | Session lifetime |
|---|---|---|---|---|
| Default | Product, Finance, HR | Per device | Remembered | 1440 min (24 hr) |
| Privileged | Engineering, IT | Always | Not remembered | 480 min (8 hr) |
| External | Contractors, Vendors | Always | Not remembered | 240 min (4 hr) |

External users get the shortest sessions (4 hours) and must re-authenticate with MFA on every session with no option to remember the device. Privileged users also cannot remember a device and must authenticate with MFA on every session. The default tier allows device trust within an 8-hour MFA window, and sessions can last up to 24 hours.

The rationale for the external tier's strictness: contractors and vendors often share devices or work from untrusted networks, and we have no visibility into their endpoint security posture. Short sessions and mandatory re-authentication limit the blast radius if a credential is compromised.

---

## Backend configuration

Terraform state is stored in S3. The backend is not configured in committed code — you supply it at init time via a local `backend.hcl` file that is not checked in.

Copy the example file and fill in your values:

```bash
cp backend.hcl.example backend.hcl
```

`backend.hcl.example`:

```hcl
bucket       = "your-tfstate-bucket"
key          = "okta-lifecycle/terraform.tfstate"
region       = "your-default-region"
encrypt      = true
use_lockfile = true
```

`use_lockfile = true` enables native S3 state locking using conditional writes. This requires Terraform 1.10 or later and means you do not need a DynamoDB table for locking — S3 handles it natively.

---

## Bootstrapping

Before running Terraform for the first time, you need an S3 bucket to store state. If you don't have one already, create it.

Versioning is recommended so you can recover a previous state file if something goes wrong during an apply.

---

## Initialize and apply

The Okta API token and org name are Terraform variables. Pass them at runtime rather than storing them in a committed file. The recommended approach is to use 1Password CLI to inject them from a `.env` file.

Initialize (only needed once, or after changing the backend):

```bash
terraform init -backend-config=backend.hcl
```

Preview what Terraform would change:

```bash
op run --env-file=../.env -- terraform plan
```

Apply:

```bash
op run --env-file=../.env -- terraform apply
```

Terraform will show the proposed changes and ask for confirmation before making anything.

---

## Getting group IDs after apply

After a successful apply, you can view all group IDs:

```bash
op run --env-file=../.env -- terraform output -json group_ids
```

Example output:

```json
{
  "contractors": "00gAbc123ExampleId1",
  "engineering": "00gAbc123ExampleId2",
  "finance":     "00gAbc123ExampleId3",
  "hr":          "00gAbc123ExampleId4",
  "it":          "00gAbc123ExampleId5",
  "product":     "00gAbc123ExampleId6",
  "vendors":     "00gAbc123ExampleId7"
}
```

The CLI resolves group names to IDs automatically, so you typically don't need these for day-to-day operations. They are useful if you're building scripts or integrations that call the Okta API directly.
