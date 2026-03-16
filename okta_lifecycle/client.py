import os
import sys
from okta.client import Client as OktaClient


def get_client() -> OktaClient:
    org_url = os.environ.get("OKTA_ORG_URL")
    api_token = os.environ.get("OKTA_API_TOKEN")

    if not org_url:
        print("Error: OKTA_ORG_URL environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    if not api_token:
        print("Error: OKTA_API_TOKEN environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    config = {
        "orgUrl": org_url,
        "token": api_token,
        "raiseException": True,  # Let the client raise exceptions for easier error handling
    }

    return OktaClient(config)
