import argparse
import asyncio
import sys

from okta.exceptions import OktaAPIException

from okta_lifecycle.audit import generate_audit_report
from okta_lifecycle.client import get_client
from okta_lifecycle.groups import assign_groups, find_groups_by_name, list_user_groups, remove_groups
from okta_lifecycle.users import deactivate_user, provision_user


def parse_args():
    """
    Parse command-line arguments for the Okta lifecycle management CLI
    """
    parser = argparse.ArgumentParser(
        prog="okta-lifecycle",
        description="Okta user lifecycle management CLI",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Provision user
    provision_parser = subparsers.add_parser("provision", help="Provision a new Okta user")
    provision_parser.add_argument("--first", required=True, help="First name")
    provision_parser.add_argument("--last", required=True, help="Last name")
    provision_parser.add_argument("--email", required=True, help="Email address / login")
    provision_parser.add_argument(
        "--groups",
        required=False,
        help="Comma-separated list of Okta group names to assign"
    )

    # Deactivate user
    deactivate_parser = subparsers.add_parser("deactivate", help="Deactivate an Okta user")
    deactivate_parser.add_argument("--email", required=True, help="Email address of user to deactivate")

    # Assign groups to user
    assign_parser = subparsers.add_parser("assign-groups", help="Assign a user to one or more groups")
    assign_parser.add_argument("--email", required=True, help="Email address of user")
    assign_parser.add_argument("--groups", required=True, help="Comma-separated list of Okta group names")

    # Remove groups from user
    remove_parser = subparsers.add_parser("remove-groups", help="Remove a user from one or more groups")
    remove_parser.add_argument("--email", required=True, help="Email address of user")
    remove_parser.add_argument("--groups", required=True, help="Comma-separated list of Okta group names")

    # List groups for user
    list_parser = subparsers.add_parser("list-groups", help="List groups for a user")
    list_parser.add_argument("--email", required=True, help="Email address of user")

    # Find IDs by name
    find_parser = subparsers.add_parser("find-groups", help="Find group IDs by name")
    find_parser.add_argument("--names", required=True, help="Comma-separated list of group names to search")

    # Create user audit report
    subparsers.add_parser("audit", help="Generate a user audit report")

    return parser.parse_args()


async def resolve_user_id(email: str) -> str:
    """Look up a user ID by email for commands that need it."""
    client = get_client()
    try:
        users, resp, err = await client.list_users(
            filter=f'profile.email eq "{email}"'
        )
        if not users:
            print(f"Error: no user found with email {email}", file=sys.stderr)
            sys.exit(1)
        return users[0].id
    except OktaAPIException as err:
        print(f"Error looking up user: {err}", file=sys.stderr)
        sys.exit(1)


async def resolve_group_ids(names: list[str]) -> list[str]:
    """Resolve a list of group display names to their Okta group IDs."""
    client = get_client()
    ids = []
    try:
        for name in names:
            groups, resp, err = await client.list_groups(
                search=f'profile.name eq "{name}"'
            )
            if not groups:
                print(f"Error: no group found with name '{name}'", file=sys.stderr)
                sys.exit(1)
            ids.append(groups[0].id)
    except OktaAPIException as err:
        print(f"Error resolving group names: {err}", file=sys.stderr)
        sys.exit(1)
    return ids


async def main():
    args = parse_args()

    if args.command == "provision":
        group_ids = await resolve_group_ids(args.groups.split(",")) if args.groups else []
        await provision_user(args.first, args.last, args.email, group_ids)

    elif args.command == "deactivate":
        await deactivate_user(args.email)

    elif args.command == "assign-groups":
        user_id = await resolve_user_id(args.email)
        group_ids = await resolve_group_ids(args.groups.split(","))
        await assign_groups(user_id, group_ids)

    elif args.command == "remove-groups":
        user_id = await resolve_user_id(args.email)
        group_ids = await resolve_group_ids(args.groups.split(","))
        await remove_groups(user_id, group_ids)

    elif args.command == "list-groups":
        await list_user_groups(args.email)

    elif args.command == "find-groups":
        names = args.names.split(",")
        await find_groups_by_name(names)

    elif args.command == "audit":
        await generate_audit_report()


if __name__ == "__main__":
    asyncio.run(main())
