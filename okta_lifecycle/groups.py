import sys

from okta.exceptions import OktaAPIException

from okta_lifecycle.client import get_client


async def find_groups_by_name(names: list[str]) -> None:
    """
    Look up Okta group IDs by their display names
    """
    client = get_client()
    try:
        for name in names:
            groups, resp, err = await client.list_groups(
                search=f'profile.name eq "{name}"'
            )
            if not groups:
                print(f"No group found matching '{name}'", file=sys.stderr)
                continue

            for group in groups:
                print(f"{group.profile.actual_instance.name}: {group.id}")
    except OktaAPIException as err:
        print(f"Error searching for groups: {err}", file=sys.stderr)
        sys.exit(1)


async def assign_groups(user_id: str, group_ids: list[str]) -> None:
    """
    Assign a user to multiple groups in Okta
    """
    client = get_client()
    try:
        for group_id in group_ids:
            await client.assign_user_to_group(group_id, user_id)
            print(f"Assigned user {user_id} to group {group_id}")
    except OktaAPIException as err:
        print(f"Error assigning user to groups: {err}", file=sys.stderr)
        sys.exit(1)


async def remove_groups(user_id: str, group_ids: list[str]) -> None:
    """
    Remove a user from multiple groups in Okta
    """
    client = get_client()
    try:
        for group_id in group_ids:
            await client.unassign_user_from_group(group_id, user_id)
            print(f"Removed user {user_id} from group {group_id}")
    except OktaAPIException as err:
        print(f"Error removing user from groups: {err}", file=sys.stderr)
        sys.exit(1)


async def list_user_groups(email: str) -> None:
    """
    List all groups a user belongs to in Okta using their email address
    """
    client = get_client()
    try:
        users, resp, err = await client.list_users(filter=f'profile.email eq "{email}"')
        if not users:
            print(f"Error: no user found with email {email}", file=sys.stderr)
            sys.exit(1)

        user = users[0]

        groups, resp, err = await client.list_user_groups(user.id)
        print(f"Groups for {email}:")
        for group in groups:
            print(f"  {group.profile.actual_instance.name} (id: {group.id})")
    except OktaAPIException as err:
        print(f"Error fetching groups for {email}: {err}", file=sys.stderr)
        sys.exit(1)
