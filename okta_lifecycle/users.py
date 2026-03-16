import sys

from okta.exceptions import OktaAPIException
from okta.models import CreateUserRequest, UserProfile

from okta_lifecycle.client import get_client
from okta_lifecycle.groups import assign_groups


async def provision_user(first_name: str, last_name: str, email: str, groups: list[str] | None = None) -> None:
    '''
    Provision a new user in Okta with the given profile information and optional group assignments
    '''
    client = get_client()
    try:
        profile = UserProfile(
            firstName=first_name,
            lastName=last_name,
            email=email,
            login=email,
        )
        user_request = CreateUserRequest(profile=profile)

        user, resp, err = await client.create_user(user_request)
        print(f"Created user: {user.profile.email} (id: {user.id})")

        if groups:
            await assign_groups(user.id, groups)
    except OktaAPIException as err:
        print(f"Error provisioning user: {err}", file=sys.stderr)
        sys.exit(1)


async def deactivate_user(email: str) -> None:
    '''
    Deactivate a user in Okta using their email address
    '''
    client = get_client()
    try:
        # Look up user by email
        users, resp, err = await client.list_users(filter=f'profile.email eq "{email}"')
        if not users:
            print(f"Error: no user found with email {email}", file=sys.stderr)
            sys.exit(1)

        user = users[0]

        # Deactivate the user
        await client.deactivate_user(user.id)
        print(f"Deactivated user: {email} (id: {user.id})")
    except OktaAPIException as err:
        print(f"Error deactivating user: {err}", file=sys.stderr)
        sys.exit(1)
