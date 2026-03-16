# okta-lifecycle

A CLI tool and supporting Terraform configuration for managing user lifecycle in Okta. The CLI handles provisioning new users, deactivating departures, and managing group memberships on a day-to-day basis. The Terraform configuration provisions the Okta groups and access policies that the CLI operates against.

This was built against an Okta developer org and is intended as a working reference rather than a production-ready product.

---

## How the pieces fit together

```
┌─────────────────────────────────────┐
│          Terraform                  │
│  Creates and manages:               │
│  - Okta groups                      │
│  - Password policies                │
│  - MFA enrollment policies          │
│  - Sign-on policies                 │
└──────────────┬──────────────────────┘
               │ creates groups
               ▼
┌─────────────────────────────────────┐
│           Okta org                  │◄──── okta-lifecycle CLI
└─────────────────────────────────────┘
```

The general workflow is: run Terraform once to get your groups and policies into Okta, then use the CLI day-to-day for user operations. The CLI doesn't manage groups or policies — that's Terraform's job.

---

## Prerequisites

- Python 3.13 or later
- `pip` and `venv` (part of the Python standard library)
- An [Okta developer account](https://developer.okta.com/) with an API token
- An AWS account with an S3 bucket for Terraform state
- [Terraform](https://developer.hashicorp.com/terraform/install) 1.14.5 or later
- [1Password CLI](https://developer.1password.com/docs/cli/) (`op`) — optional but strongly recommended for secret injection

---

## Repository structure

```
okta-lifecycle/
├── okta-lifecycle.py          # CLI entry point
├── okta_lifecycle/            # CLI package
│   ├── audit.py               # Audit report generation
│   ├── client.py              # Okta client factory
│   ├── groups.py              # Group management
│   └── users.py               # User provisioning and deactivation
├── terraform/                 # Okta environment configuration
│   ├── groups.tf
│   ├── policies.tf
│   ├── outputs.tf
│   ├── vars.tf
│   ├── terraform.tf
│   ├── backend.hcl            # Not committed — your S3 backend settings
│   └── backend.hcl.example    # Copy this and fill in your values
├── reports/                   # Generated audit CSVs (add to .gitignore)
└── requirements.txt
```

---

## Getting started

### 1. Set up Terraform

Before you can do anything useful with the CLI, the Okta groups need to exist. Terraform creates them.

See [terraform/README.md](terraform/README.md) for the full setup walkthrough.

### 2. Set up the CLI

Once Terraform has run and your groups exist in Okta:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

See [okta_lifecycle/README.md](okta_lifecycle/README.md) for configuration and usage.

---

## Security design

Credentials are never committed. The Okta API token and org URL are passed through environment variables (`OKTA_ORG_URL`, `OKTA_API_TOKEN`). The Terraform variables `okta_api_token` and `okta_org_name` are likewise passed at runtime, not stored in any `.tfvars` file checked into the repo.

1Password CLI is the recommended way to inject secrets. Running commands through `op run --env-file=.env -- <command>` means the actual secret values are fetched from 1Password at runtime. The `.env` file contains only 1Password secret references (e.g. `op://vault/item/field`) rather than raw tokens, so they never appear in your shell history or environment.

Terraform state is stored in S3 with native state locking. The state file is encrypted at rest.

Security question recovery is disabled across all password policies. Security questions are a weak recovery mechanism and are turned off everywhere.

---

## What I'd add with more time

**Pagination in the audit report.** The `list_users` call returns the first page of results from the Okta API. For any org with more than a few hundred users, the audit would silently miss people. Following the `next` link headers to paginate through all results is straightforward but not yet implemented.

**Concurrent per-user API calls in the audit.** For each user, the audit makes two additional API calls — one for group memberships and one for MFA factors. These run sequentially, so the time to generate the report scales linearly with the number of users. Running them concurrently with `asyncio.gather` would make this substantially faster at scale.

**A proper two-step deprovisioning flow.** The current `deactivate` command calls Okta's deactivate endpoint directly, which moves the user straight to `DEPROVISIONED`. The better approach is to suspend first (which immediately revokes all active sessions and tokens and is reversible) and then deactivate after confirmation. Deactivation in Okta is permanent — group memberships and factor enrollments are lost.

**Input validation before making API calls.** The CLI accepts email addresses and group names as raw strings with no format checking. Adding basic validation before hitting the API would produce better error messages and catch typos earlier.

**A `--dry-run` flag.** Useful for seeing what a `provision` or `deactivate` command would do without actually doing it.

**Automated tests.** Setting up unit tests using mocked Okta responses would make the codebase safer to change.
