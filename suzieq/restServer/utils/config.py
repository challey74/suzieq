from typing import Optional, Dict, List, Any

import logging
import os

from pydantic import BaseModel, validator, Field

import uvicorn

from suzieq.restServer.utils.types import KeyPermission, ApiKey, EndpointFilter
from suzieq.shared.utils import load_sq_config


class Settings(BaseModel):
    _instance = None

    API_KEY: Optional[str] = None
    api_keys: Dict[str, ApiKey] = Field(
        default_factory=dict, description="API keys with permissions"
    )
    logging_level: str = "WARNING"
    address: str = "127.0.0.1"
    port: int = 8000
    rest_certfile: Optional[str] = None
    rest_keyfile: Optional[str] = None
    keyfile_permissions_check: bool = True
    no_https: bool = False
    logfile: Optional[str] = "/tmp/sq-rest-server.log"
    logsize: Optional[int] = 1000000
    log_stdout: bool = False
    log_to_file: Optional[bool] = None
    log_filter_endpoints: Optional[List[str]] = Field(
        default_factory=list, description="Full endpoints to filter from logs"
    )
    inventory_dir: str = "/var/lib/suzieq/inventory"
    temp_inventory_dir: str = "/tmp/suzieq/inventory"
    config_file: str
    config_data: Dict[str, Any]

    class Config:
        arbitrary_types_allowed = True

    @validator("log_filter_endpoints", pre=True)
    def parse_log_filter_endpoints(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [endpoint.strip() for endpoint in v.split(",") if endpoint.strip()]
        elif isinstance(v, list):
            return [str(endpoint).strip() for endpoint in v if str(endpoint).strip()]

        return v

    @validator("logging_level", pre=True)
    def parse_log_level(cls, v):
        levels = {
            logging.DEBUG: "debug",
            logging.INFO: "info",
            logging.WARNING: "warning",
            logging.ERROR: "error",
            logging.CRITICAL: "critical",
        }

        if isinstance(v, str):
            lower_v = v.lower()
            if lower_v in levels.values():
                return lower_v
        elif isinstance(v, int):
            if v in levels:
                return levels[v]

        available_levels = ", ".join(levels.values())
        raise ValueError(
            f"Invalid log level: {v}. Available levels are: {available_levels}"
        )

    @validator("api_keys", pre=True)
    def parse_api_keys(cls, v, values):
        keys = {}

        # Add API_KEY with READ permission if it's defined
        api_key = values.get("API_KEY")
        if api_key:
            keys[api_key] = ApiKey(KeyPermission.READ)

        def parse_permissions(perms_str: str) -> KeyPermission:
            permissions = KeyPermission(0)
            for perm in perms_str.upper().split("|"):
                try:
                    permissions |= KeyPermission[perm]
                except KeyError:
                    raise ValueError(
                        f"Invalid permission: {perm}. "
                        f"Valid permissions are: \
                        {', '.join(KeyPermission.__members__.keys())}"
                    )
            if permissions == KeyPermission(0):
                raise ValueError("No valid permissions specified")
            return permissions

        if isinstance(v, dict):
            for key, perms in v.items():
                if isinstance(perms, str):
                    keys[key] = ApiKey(parse_permissions(perms))
                else:
                    raise ValueError(
                        f"Invalid permission format for key {key}. \
                        Expected string, got {type(perms)}"
                    )

        elif isinstance(v, str):
            for key_perm in v.split(","):
                parts = key_perm.split(":")
                if len(parts) != 2:
                    raise ValueError(
                        f"Invalid key-permission format: {key_perm}. \
                        Expected 'key:permissions'"
                    )
                key, perms = parts

                keys[key.strip()] = ApiKey(parse_permissions(perms))

        else:
            raise ValueError(
                f"Invalid type for API_KEYS: {type(v)}. Expected dict or str"
            )

        if not keys:
            raise ValueError("No valid API keys provided")

        return keys

    @validator("rest_certfile", "rest_keyfile")
    def check_file_exists(cls, v, field):
        if v is not None:
            if not os.path.isfile(v):
                raise FileNotFoundError(f"{field.name} file does not exist: {v}")
            if not os.access(v, os.R_OK):
                raise PermissionError(f"{field.name} file is not readable: {v}")

        return v

    @validator("rest_keyfile")
    def check_key_file_permissions(cls, v, values):
        if v is not None:
            if os.name == "posix":
                stat = os.stat(v)

                # Check if group or others have any permissions
                if values.get("keyfile_permissions_check") and stat.st_mode & 0o077:
                    raise PermissionError(
                        f"Insecure permissions on key file: {v}. "
                        f"The key file should have strict permissions (e.g. 600) "
                        f"to restrict access to the owner only. "
                        f"If you want to disable this check, "
                        f"set 'keyfile_permissions_check' to False."
                    )

        return v

    @classmethod
    def from_config(cls, config_file: str):
        if cls._instance is not None:
            raise ValueError("Settings instance already exists")

        suzieq_config = load_sq_config(config_file=config_file)
        rest_config = suzieq_config.get("rest", {})
        config = {k.lower().replace("-", "_"): v for k, v in rest_config.items()}

        env_prefix = config.get("env_prefix", "")

        for field in cls.__fields__:
            env_var = env_prefix + field.upper()
            if env_var in os.environ:
                config[field] = os.environ[env_var]

        config["config_file"] = config_file
        config["config_data"] = suzieq_config
        cls._instance = cls(**config)

        return cls._instance

    def configure_uvicorn_logging(self):
        """Configure uvicorn logging to log to stdout and/or rotating file.
        This contains the default behavior of only logging
        to a file if logfile is present and log_stdout is False and only logging to
        stdout if log_stdout is True. log_to_file was added to allow
        for disabling file logging while log_stdout is False
        or logging to both a file and stdout.
        """
        log_config = uvicorn.config.LOGGING_CONFIG

        if self.log_filter_endpoints:
            log_config["handlers"]["default"]["filters"] = ["endpoint_filter"]
            log_config["handlers"]["access"]["filters"] = ["endpoint_filter"]
            log_config["filters"] = {
                "endpoint_filter": {
                    "()": f"{EndpointFilter.__module__}.EndpointFilter",
                    "endpoints": self.log_filter_endpoints,
                }
            }

        def set_rotating_file_handler(logname):
            log_config["handlers"][logname]["filename"] = self.logfile
            log_config["handlers"][logname][
                "class"
            ] = "logging.handlers.RotatingFileHandler"
            log_config["handlers"][logname]["maxBytes"] = self.logsize
            log_config["handlers"][logname]["backupCount"] = 2

        def remove_stream_handler(logname):
            if "stream" in log_config["handlers"][logname]:
                del log_config["handlers"][logname]["stream"]

        if self.log_to_file and self.logfile:
            set_rotating_file_handler("default")
            set_rotating_file_handler("access")
            if not self.log_stdout:
                remove_stream_handler("default")
                remove_stream_handler("access")
        elif self.logfile and not self.log_stdout:
            set_rotating_file_handler("default")
            set_rotating_file_handler("access")
            remove_stream_handler("default")
            remove_stream_handler("access")


def get_settings() -> Settings:
    if not Settings._instance:
        raise ValueError("No settings instance available")

    return Settings._instance
