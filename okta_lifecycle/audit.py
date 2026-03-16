import csv
import sys
from datetime import datetime
from pathlib import Path

from okta.exceptions import OktaAPIException
from okta.models.user_factor import UserFactor as OktaUserFactor
from okta.models.user_profile import UserProfile as OktaUserProfile

from okta_lifecycle.client import get_client

# Workaround for Okta SDK v3 bug: pydantic rejects empty string secondEmail
# values (min_length=5). Strip it from the response before validation.
_original_from_dict = OktaUserProfile.from_dict

@classmethod
def _patched_from_dict(cls, obj):
    if isinstance(obj, dict):
        obj = {**obj, "secondEmail": None}
    return _original_from_dict(obj)

OktaUserProfile.from_dict = _patched_from_dict

# Workaround for Okta SDK v3 bug: factor types like "signed_nonce" (Okta
# FastPass) exist in the UserFactorType enum but are missing from the
# discriminator map in UserFactor.from_dict, causing a ValueError. Fall back
# to constructing the base UserFactor model directly for unknown types.
_original_user_factor_from_dict = OktaUserFactor.from_dict

@classmethod
def _patched_user_factor_from_dict(cls, obj):
    try:
        return _original_user_factor_from_dict(obj)
    except ValueError:
        return OktaUserFactor.model_validate(obj)

OktaUserFactor.from_dict = _patched_user_factor_from_dict


REPORTS_DIR = Path(__file__).parent.parent / "reports"


async def generate_audit_report() -> None:
    """
    Generate a CSV report of all Okta users, their group memberships, 
    MFA enrollment status, and other relevant details
    """
    client = get_client()
    try:
        # Fetch all users
        users, resp, err = await client.list_users()

        rows = []
        for user in users:
            # Fetch group memberships per user
            groups, resp, err = await client.list_user_groups(user.id)

            # Filter out the default Everyone group Okta adds automatically
            group_names = [
                g.profile.actual_instance.name for g in groups
                if g.profile.actual_instance.name != "Everyone"
            ]

            # Fetch enrolled factors per user
            factors, resp, err = await client.list_factors(user.id)

            enrolled_factors = [f.factor_type for f in factors if f.status == "ACTIVE"]

            rows.append({
                "email": user.profile.email,
                "first_name": user.profile.first_name,
                "last_name": user.profile.last_name,
                "status": user.status,
                "groups": ", ".join(group_names) if group_names else "NONE",
                "mfa_enrolled": "YES" if enrolled_factors else "NO",
                "mfa_factors": ", ".join(enrolled_factors) if enrolled_factors else "NONE",
                "flags": _build_flags(user.status, group_names, enrolled_factors),
            })

        # Write report to CSV
        REPORTS_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = REPORTS_DIR / f"audit_{timestamp}.csv"

        fieldnames = [
            "email", "first_name", "last_name", "status",
            "groups", "mfa_enrolled", "mfa_factors", "flags"
        ]

        with open(report_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

            print(f"Audit report written to {report_path}")
            _print_summary(rows)
    except OktaAPIException as err:
        print(f"Error generating audit report: {err}", file=sys.stderr)
        sys.exit(1)


def _build_flags(status: str, groups: list[str], factors: list[str]) -> str:
    """
    Build a comma-separated string of flags for users that are inactive, 
    have no group memberships, or have no MFA enrolled
    """
    flags = []
    if status == "DEPROVISIONED":
        flags.append("INACTIVE")
    if not groups:
        flags.append("NO_GROUPS")
    if not factors:
        flags.append("NO_MFA")
    return ", ".join(flags) if flags else "OK"


def _print_summary(rows: list[dict]) -> None:
    """
    Print a summary of the audit results, including total users, number of users missing MFA, 
    number of users with no group memberships, and number of inactive/deprovisioned users
    """
    total = len(rows)
    no_mfa = sum(1 for r in rows if r["mfa_enrolled"] == "NO")
    no_groups = sum(1 for r in rows if r["groups"] == "NONE")
    inactive = sum(1 for r in rows if r["status"] == "DEPROVISIONED")

    print(f"\nSummary:")
    print(f"  Total users:        {total}")
    print(f"  Missing MFA:        {no_mfa}")
    print(f"  No group membership:{no_groups}")
    print(f"  Inactive/deprovisioned: {inactive}")
