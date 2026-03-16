# okta-lifecycle CLI

The CLI is the main interface for managing users in your Okta org. It wraps the Okta Management API and handles provisioning new users, deactivating departures, managing group memberships, and generating audit reports.

The entry point is `okta-lifecycle.py` in the project root. The `okta_lifecycle/` package contains the underlying implementation.

---

## Installation

Create a virtual environment and install dependencies from the project root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Python 3.13 or later is required.

---

## Configuration

The CLI needs two environment variables set before any command will run:

| Variable | Description |
|---|---|
| `OKTA_ORG_URL` | Your Okta org URL, e.g. `https://dev-123456.okta.com` |
| `OKTA_API_TOKEN` | An Okta API token with sufficient permissions |

You can export them directly in your shell, but the recommended approach is to store them as 1Password secret references in a `.env` file and inject them at runtime using `op run`.

A `.env` file using 1Password references looks like this:

```
OKTA_ORG_URL=op://Personal/Okta Dev/org_url
OKTA_API_TOKEN=op://Personal/Okta Dev/api_token
```

Then prefix every command with:

```bash
op run --env-file=.env -- python okta-lifecycle.py <subcommand> ...
```

The 1Password CLI fetches the actual values at runtime. They never appear in your shell history.

---

## CLI reference

### `provision`

Creates a new user in Okta and optionally adds them to one or more groups.

```
python okta-lifecycle.py provision --first NAME --last NAME --email EMAIL [--groups GROUP1,GROUP2]
```

| Flag | Required | Description |
|---|---|---|
| `--first` | yes | First name |
| `--last` | yes | Last name |
| `--email` | yes | Email address, used as both the login and primary email |
| `--groups` | no | Comma-separated list of group display names to assign at creation time |

Group names are resolved to Okta IDs before the user is created. If any name doesn't match an existing group, the command exits with an error before creating the user.

Provision a user with no group assignments:

```bash
op run --env-file=.env -- python okta-lifecycle.py provision \
  --first "Arjun" --last "Mehta" --email "jane.doe@example.com"
```

Provision a user and add them to Engineering and IT:

```bash
op run --env-file=.env -- python okta-lifecycle.py provision \
  --first "Arjun" --last "Mehta" --email "jane.doe@example.com" \
  --groups "Engineering,IT"
```

---

### `deactivate`

Deactivates an existing Okta user by email.

```
python okta-lifecycle.py deactivate --email EMAIL
```

| Flag | Required | Description |
|---|---|---|
| `--email` | yes | Email address of the user to deactivate |

Note: Okta's deactivate operation is not directly reversible. If you want to temporarily suspend access while preserving the ability to reactivate the account, the Okta API also supports a `suspend` operation. The CLI currently goes straight to deactivation.

```bash
op run --env-file=.env -- python okta-lifecycle.py deactivate \
  --email "jane.doe@example.com"
```

---

### `assign-groups`

Adds an existing user to one or more groups by name.

```
python okta-lifecycle.py assign-groups --email EMAIL --groups GROUP1,GROUP2
```

| Flag | Required | Description |
|---|---|---|
| `--email` | yes | Email address of the user |
| `--groups` | yes | Comma-separated list of group display names |

```bash
op run --env-file=.env -- python okta-lifecycle.py assign-groups \
  --email "jane.doe@example.com" \
  --groups "Finance,HR"
```

---

### `remove-groups`

Removes an existing user from one or more groups by name.

```
python okta-lifecycle.py remove-groups --email EMAIL --groups GROUP1,GROUP2
```

| Flag | Required | Description |
|---|---|---|
| `--email` | yes | Email address of the user |
| `--groups` | yes | Comma-separated list of group display names |

```bash
op run --env-file=.env -- python okta-lifecycle.py remove-groups \
  --email "jane.doe@example.com" \
  --groups "Contractors"
```

---

### `list-groups`

Prints the groups a user currently belongs to, including the Okta group ID for each.

```
python okta-lifecycle.py list-groups --email EMAIL
```

| Flag | Required | Description |
|---|---|---|
| `--email` | yes | Email address of the user |

```bash
op run --env-file=.env -- python okta-lifecycle.py list-groups \
  --email "jane.doe@example.com"
```

Example output:

```
Groups for jane.doe@example.com:
  Engineering (id: 00gAbc123ExampleId1)
  IT (id: 00gAbc123ExampleId2)
```

---

### `find-groups`

Looks up Okta group IDs by display name. Useful when you need to reference IDs directly in scripts or API calls, or want to cross-reference with Terraform output.

```
python okta-lifecycle.py find-groups --names NAME1,NAME2
```

| Flag | Required | Description |
|---|---|---|
| `--names` | yes | Comma-separated list of group display names to look up |

```bash
op run --env-file=.env -- python okta-lifecycle.py find-groups \
  --names "Engineering,Product,HR"
```

Example output:

```
Engineering: 00gAbc123ExampleId1
Product: 00gAbc123ExampleId2
HR: 00gAbc123ExampleId3
```

---

### `audit`

Generates a CSV report of all users in the org, including their Okta status, group memberships, and MFA enrollment state. Results are written to the `reports/` directory.

```
python okta-lifecycle.py audit
```

```bash
op run --env-file=.env -- python okta-lifecycle.py audit
```

Example output:

```
Audit report written to /path/to/reports/audit_20260316_000917.csv

Summary:
  Total users:            24
  Missing MFA:            3
  No group membership:    1
  Inactive/deprovisioned: 2
```

#### Report format

Reports are saved as `audit_YYYYMMDD_HHMMSS.csv` in the `reports/` directory. Each row represents one user.

| Column | Description |
|---|---|
| `email` | User's primary email address |
| `first_name` | First name |
| `last_name` | Last name |
| `status` | Okta lifecycle status, e.g. `ACTIVE`, `DEPROVISIONED` |
| `groups` | Comma-separated group memberships, excluding the built-in `Everyone` group. `NONE` if no custom groups. |
| `mfa_enrolled` | `YES` or `NO` |
| `mfa_factors` | Comma-separated list of enrolled factor types, e.g. `token:software:totp`, `webauthn`. `NONE` if not enrolled. |
| `flags` | `OK` if no issues, otherwise a comma-separated list: `INACTIVE`, `NO_GROUPS`, `NO_MFA` |

#### Performance note

The audit command makes two additional API calls per user — one for group memberships and one for MFA factors. For small orgs this is fine. For orgs with hundreds of users it becomes slow, since the calls run sequentially. This is a known limitation; see the top-level README for more detail.

---

## How group names are resolved

All subcommands that accept group names (`--groups` or `--names`) resolve each name to an Okta group ID before performing any operation. Resolution uses an exact match against the group's display name as it exists in Okta.

If a name matches no groups, the command prints an error to stderr and exits with code 1. No changes are made to Okta until all group names resolve successfully. For `provision` specifically, the user is not created if any group name fails to resolve.

---

## Getting group names from Terraform output

If you provisioned your Okta groups using the Terraform configuration in this repo, you can see all group names alongside their IDs with:

```bash
cd terraform
op run --env-file=../.env -- terraform output -json group_ids
```

This produces output like:

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

The display names used with `--groups` (e.g. `"Engineering"`) match the `name` attribute in `terraform/groups.tf`, not the Terraform resource key (which is lowercase).
