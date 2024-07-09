from typing import Optional, Dict, List, Any

import logging
import os

from pydantic import BaseModel, validator, Field

import uvicorn

from suzieq.poller.orchestrator.orchestrator import Orchestrator
from suzieq.restServer.utils.types import KeyPermission, ApiKey, EndpointFilter
from suzieq.shared.utils import load_sq_config


class Settings(BaseModel):
    """
    Configuration settings for the Suzieq REST Server.
    """

    _instance = None

    api_key: Optional[str] = Field(None, alias="API_KEY")
    api_keys: Dict[str, ApiKey] = Field(
        default_factory=dict,
        alias="api-keys",
        description="API keys with permissions",
    )
    logging_level: str = Field("WARNING", alias="logging-level")
    address: str = "127.0.0.1"
    port: int = 8000
    rest_certfile: Optional[str] = Field(None, alias="rest-certfile")
    rest_keyfile: Optional[str] = Field(None, alias="rest-keyfile")
    keyfile_permissions_check: bool = Field(
        True, alias="keyfile-permissions-check"
    )
    no_https: bool = Field(False, alias="no-https")
    logfile: Optional[str] = None
    logsize: Optional[int] = 1000000
    log_stdout: bool = Field(False, alias="log-stdout")
    log_filter_endpoints: Optional[List[str]] = Field(
        default_factory=list,
        alias="log-filter-endpoints",
        description="Full endpoints to filter from logs",
    )
    inventory_dir: str = Field(
        "/var/lib/suzieq/inventory",
        alias="inventory-dir",
        description="Inventory directory for non-temporary files",
    )
    temp_inventory_dir: str = Field(
        "/tmp/suzieq/inventory",
        alias="temp-inventory-dir",
        description="Inventory directory for temporary files",
    )
    env_prefix: str = Field(
        "SUZIEQ_",
        alias="env-prefix",
        description="Prefix for all environment variables used \
        and created by the Rest Server",
    )
    config_file: str
    config_data: Dict[str, Any]
    orchestrator: Orchestrator = Orchestrator()

    class Config:
        arbitrary_types_allowed = True
        allow_population_by_field_name = True

    @validator("log_filter_endpoints", pre=True)
    def parse_log_filter_endpoints(cls, v):
        """
        Parse log filter endpoints from a string or list.
        """
        if v is None:
            return []
        return [
            str(endpoint).strip()
            for endpoint in (v.split(",") if isinstance(v, str) else v)
            if str(endpoint).strip()
        ]

    @validator("logging_level", pre=True)
    def parse_log_level(cls, v):
        """
        Parse logging level from a string or integer.
        """
        levels = {
            logging.DEBUG: "debug",
            logging.INFO: "info",
            logging.WARNING: "warning",
            logging.ERROR: "error",
            logging.CRITICAL: "critical",
        }

        raw_v = v
        if isinstance(v, str):
            v = v.lower()
        elif isinstance(v, int):
            v = levels.get(v)

        if v not in levels.values():
            available_levels = ", ".join(levels.values())
            raise ValueError(
                f"Invalid log level: {raw_v}."
                f"Available levels are: {available_levels}"
            )

        return v

    @validator("api_keys", pre=True)
    def parse_api_keys(cls, v, values):
        """
        Parse API keys and their permissions from a dictionary or string.
        """
        keys = {}

        def add_api_key(key, perms_str):
            permissions = KeyPermission(0)
            for perm in perms_str.upper().split("|"):
                try:
                    permissions |= KeyPermission[perm]
                except KeyError:
                    raise ValueError(
                        f"Invalid permission: {perm}."
                        "Valid permissions are:"
                        f"{', '.join(KeyPermission.__members__.keys())}"
                    )
            if permissions == KeyPermission(0):
                raise ValueError("No valid permissions specified")
            keys[key] = ApiKey(permissions)

        # Add API_KEY with READ permission if it's defined
        api_key = values.get("API_KEY")
        if api_key:
            add_api_key(api_key, "READ")

        if isinstance(v, dict):
            for key, perms in v.items():
                if isinstance(perms, str):
                    add_api_key(key, perms)
                else:
                    raise ValueError(
                        f"Invalid permission format for key {key}."
                        f"Expected string, got {type(perms)}"
                    )
        elif isinstance(v, str):
            for key_perm in v.split(","):
                parts = key_perm.split(":")
                if len(parts) != 2:
                    raise ValueError(
                        f"Invalid key-permission format: {key_perm}."
                        f"Expected 'key:permissions'"
                    )
                key, perms = parts
                add_api_key(key.strip(), perms)
        else:
            raise ValueError(
                f"Invalid type for API_KEYS: {type(v)}. Expected dict or str"
            )

        if not keys:
            raise ValueError("No valid API keys provided")

        return keys

    @validator("rest_certfile", "rest_keyfile")
    def check_file_exists_and_permissions(cls, v, field, values):
        """
        Check if the cert/key file exists and has proper permissions.
        """
        if v is not None:
            if not os.path.isfile(v):
                raise FileNotFoundError(
                    f"{field.name} file does not exist: {v}"
                )
            if not os.access(v, os.R_OK):
                raise PermissionError(
                    f"{field.name} file is not readable: {v}"
                )

            if field.name == "rest_keyfile" and os.name == "posix":
                stat = os.stat(v)
                if (
                    values.get("keyfile_permissions_check")
                    and stat.st_mode & 0o077
                ):
                    raise PermissionError(
                        f"Insecure permissions on key file: {v}."
                        f"The key file should have strict permissions (eg 600)"
                        f"to restrict access to the owner only."
                        f"If you want to disable this check,"
                        f"set 'keyfile-permissions-check' to False."
                    )

        return v

    @validator("env_prefix")
    def uppercase_env_prefix(cls, v):
        """
        Convert env_prefix to uppercase.
        """
        return v.upper()

    @classmethod
    def load_config(cls, config_file: str):
        """
        Load configuration from a file.
        """
        try:
            suzieq_config = load_sq_config(config_file=config_file)
            rest_config = suzieq_config.get("rest", {})
            config = {
                k.lower().replace("-", "_"): v for k, v in rest_config.items()
            }

            return config, suzieq_config

        except Exception as e:
            raise ValueError(
                f"Failed to load configuration from {config_file}: {e}"
            )

    @classmethod
    def from_config(cls, config_file: str):
        """
        Create a Settings instance from a configuration file.
        """
        if cls._instance is not None:
            raise ValueError("Settings instance already exists")

        config, suzieq_config = cls.load_config(config_file)

        env_prefix = config.get("env_prefix", "SUZIEQ_")

        for field in cls.__fields__:
            if field in [
                "config_file",
                "config_data",
                "env_prefix",
                "orchestrator",
            ]:
                continue

            env_var = env_prefix + field.upper()
            if env_var in os.environ:
                config[field] = os.environ[env_var]

        config["config_file"] = config_file
        config["config_data"] = suzieq_config

        try:
            cls._instance = cls(**config)
        except Exception as e:
            raise ValueError(f"Failed to create Settings instance: {e}")

        return cls._instance

    def configure_uvicorn_logging(self):
        """
        Configure uvicorn logging to log to stdout and/or rotating file.
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

        if self.logfile:
            set_rotating_file_handler("default")
            set_rotating_file_handler("access")

        if not self.log_stdout:
            remove_stream_handler("default")
            remove_stream_handler("access")


def get_settings() -> Settings:
    """
    Get the current Settings instance.
    """
    if not Settings._instance:
        raise ValueError("No settings instance available")

    return Settings._instance


def get_orchestrator() -> Orchestrator:
    """
    Get the Orchestrator instance from the current Settings.
    """
    return get_settings().orchestrator


def get_config_file() -> str:
    """
    Get the configuration file path from the current Settings.
    """
    return get_settings().config_file
