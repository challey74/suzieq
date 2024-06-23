from functools import partial

from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader, APIKeyQuery

from suzieq.restServer.utils.config import get_settings
from suzieq.restServer.utils.types import KeyPermission
from suzieq.restServer.utils.helpers import append_error_id

_key_name = "access_token"
_previous_api_key_header = APIKeyHeader(name=_key_name, auto_error=False)
_api_key_header = APIKeyHeader(name="Authorization", auto_error=False)
_api_key_query = APIKeyQuery(name=_key_name, auto_error=False)


def check_auth(
    required_permission: KeyPermission,
    previous_api_key_header: str = Security(_previous_api_key_header),
    api_key_header: str = Security(_api_key_header),
    api_key_query: str = Security(_api_key_query),
) -> str:
    api_key = None
    if previous_api_key_header:
        api_key = previous_api_key_header
    elif api_key_header:
        parts = api_key_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            api_key = parts[1]
    elif api_key_query:
        api_key = api_key_query

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail=append_error_id("API key not provided"),
            headers={"WWW-Authenticate": "Bearer"},
        )

    settings = get_settings()
    api_key_obj = settings.api_keys.get(api_key)
    if not api_key_obj:
        raise HTTPException(
            status_code=401,
            detail=append_error_id("Invalid API key"),
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not api_key_obj.has_permission(required_permission):
        raise HTTPException(
            status_code=403,
            detail=append_error_id("Insufficient permissions"),
        )

    return api_key


REQUIRE_READ = partial(check_auth, required_permission=KeyPermission.READ)
REQUIRE_WRITE = partial(check_auth, required_permission=KeyPermission.WRITE)
REQUIRE_DELETE = partial(check_auth, required_permission=KeyPermission.DELETE)
REQUIRE_EXECUTE = partial(check_auth, required_permission=KeyPermission.EXECUTE)
REQUIRE_ADMIN = partial(check_auth, required_permission=KeyPermission.ADMIN)
