from functools import lru_cache

from pecha_api import config
from pecha_api.external_clients.open_pecha_client.open_pecha_client.client import (
    AuthenticatedClient,
    Client,
)


@lru_cache()
def get_open_pecha_client() -> Client:
    """Get a configured OpenPecha API client instance.
    
    Returns a cached client instance for reuse across requests.
    Configure via config:
        - EXTERNAL_DEV_PECHA_API_URL: Base URL for the API
    """
    return Client(
        base_url=config.get("EXTERNAL_DEV_PECHA_API_URL"),
        raise_on_unexpected_status=True,
    )


@lru_cache()
def get_authenticated_open_pecha_client() -> AuthenticatedClient:
    """Get a configured authenticated OpenPecha API client instance.
    
    Returns a cached client instance with API key authentication.
    Configure via config:
        - EXTERNAL_DEV_PECHA_API_URL: Base URL for the API
        - EXTERNAL_OPENPECHA_API_KEY: API key for authentication (required)
        - EXTERNAL_PECHA_APP_NAME: Application name header (default: webuddhist)
    
    Raises:
        ValueError: If EXTERNAL_OPENPECHA_API_KEY is not set
    """
    api_key = config.get("EXTERNAL_OPENPECHA_API_KEY")
    if not api_key:
        raise ValueError("EXTERNAL_OPENPECHA_API_KEY is required in config")
    
    app_name = config.get("EXTERNAL_PECHA_APP_NAME")
    
    return AuthenticatedClient(
        base_url=config.get("EXTERNAL_DEV_PECHA_API_URL"),
        token=api_key,
        prefix="",
        auth_header_name="X-API-Key",
        raise_on_unexpected_status=True,
        headers={"X-Application": app_name},
    )
