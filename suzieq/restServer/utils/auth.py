from fastapi import Security, HTTPException, Depends
from fastapi.security import APIKeyHeader, APIKeyQuery

from suzieq.restServer.utils.settings import get_settings
from suzieq.restServer.utils.types import KeyPermission
from suzieq.restServer.utils.helpers import append_error_id


_key_name = "access_token"
_previous_api_key_header = APIKeyHeader(name=_key_name, auto_error=False)
_api_key_header = APIKeyHeader(name="Authorization", auto_error=False)
_api_key_query = APIKeyQuery(name=_key_name, auto_error=False)


def check_auth(
    required_permission: str,
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
    required_permission_enum = KeyPermission[required_permission]
    if not api_key_obj.has_permission(required_permission_enum):
        raise HTTPException(
            status_code=403,
            detail=append_error_id("Insufficient permissions"),
        )
    return api_key


# Wrapper to require a specific permission and
# not have it show in swagger as query param
def require_permission(required_permission: str):
    def _require_permission(
        previous_api_key_header: str = Security(_previous_api_key_header),
        api_key_header: str = Security(_api_key_header),
        api_key_query: str = Security(_api_key_query),
    ):
        return check_auth(
            required_permission,
            previous_api_key_header,
            api_key_header,
            api_key_query,
        )

    return Depends(_require_permission)


REQUIRE_READ = require_permission("READ")
REQUIRE_WRITE = require_permission("WRITE")
REQUIRE_DELETE = require_permission("DELETE")
REQUIRE_EXECUTE = require_permission("EXECUTE")
REQUIRE_ADMIN = require_permission("ADMIN")
