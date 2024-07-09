import os
import uuid

from enum import Enum
from typing import Optional, List, Union, Literal, Dict, Tuple

from pydantic import BaseModel, validator, Field

from suzieq.poller.controller.utils.inventory_models import (
    DeviceModel,
    NamespaceModel,
)
from suzieq.restServer.models.shared_models import WebhookConfig
from suzieq.restServer.utils.settings import get_settings


def validate_sensitive_field(field_name: str):
    def validate_field(cls, v):
        if isinstance(v, str) and v.lower() == "ask":
            raise ValueError(
                f"The 'ask' value is not supported for the '{field_name}'"
                "field with the REST server."
            )
        return v

    return validator(field_name, allow_reuse=True)(validate_field)


def export_sensitive_field(value: str) -> Tuple[str, Optional[str]]:
    if isinstance(value, str) and not (
        value.startswith("env:") or value.startswith("plain:")
    ):
        env_name = f"{get_settings().env_prefix}_{uuid.uuid4().hex.upper()}"
        os.environ[env_name] = value
        return f"env:{env_name}", env_name
    return value, None


class SourceTypes(str, Enum):
    ANSIBLE = "ansible"
    NATIVE = "native"
    NETBOX = "netbox"


class AnsibleSource(BaseModel):
    name: str
    path: str
    type: Literal[SourceTypes.ANSIBLE]

    def dict(self, *args, **kwargs):
        result = super().dict(*args, **kwargs)
        result["type"] = self.type.value
        return result


class NativeSource(BaseModel):
    name: str
    hosts: List[Dict[Literal["url"], str]] = Field(
        ...,
        title="Hosts",
        description="List of host URLs",
        example=[
            {"url": "http://example.com/host1"},
            {"url": "http://example.com/host2"},
        ],
    )
    type: Optional[Literal[SourceTypes.NATIVE]]

    def dict(self, *args, **kwargs):
        result = super().dict(*args, **kwargs)
        result["type"] = self.type.value
        return result


class NetboxSource(BaseModel):
    name: str
    token: str
    url: str
    tag: Optional[List[str]]
    type: Literal[SourceTypes.NETBOX]
    period: Optional[int]
    created_env_names: List[str] = Field([], hidden=True)

    validate_token = validate_sensitive_field("token")

    def __init__(self, **data):
        super().__init__(**data)
        object.__setattr__(self, "created_env_names", [])
        self.token, token_env = export_sensitive_field(self.token)
        self.created_env_names = [token_env] if token_env else []

    def dict(self, *args, **kwargs):
        result = super().dict(*args, **kwargs)
        result["type"] = self.type.value
        del result["created_env_names"]
        return result

    class Config:
        extra = "allow"


class Auth(BaseModel):
    name: str
    path: Optional[str]
    username: Optional[str]
    password: Optional[str]
    enable_password: Optional[str] = Field(None, alias="enable-password")
    key_passphrase: Optional[str] = Field(None, alias="key-passphrase")
    keyfile: Optional[str]

    validate_password = validate_sensitive_field("password")
    validate_username = validate_sensitive_field("username")
    validate_key_passphrase = validate_sensitive_field("key_passphrase")
    validate_enable_password = validate_sensitive_field("enable_password")

    def __init__(self, **data):
        super().__init__(**data)
        object.__setattr__(self, "created_env_names", [])
        self.password, password_env = export_sensitive_field(self.password)
        self.username, username_env = export_sensitive_field(self.username)
        self.key_passphrase, key_passphrase_env = export_sensitive_field(
            self.key_passphrase
        )
        self.enable_password, enable_password_env = export_sensitive_field(
            self.enable_password
        )

        self.created_env_names = [
            env
            for env in [
                password_env,
                username_env,
                key_passphrase_env,
                enable_password_env,
            ]
            if env is not None
        ]

    def dict(self, *args, **kwargs):
        result = super().dict(*args, **kwargs)
        del result["created_env_names"]
        return result

    class Config:
        extra = "allow"


class Inventory(BaseModel):
    sources: List[Union[NetboxSource, AnsibleSource, NativeSource]]
    devices: Optional[List[DeviceModel]]
    auths: Optional[List[Auth]]
    namespaces: List[NamespaceModel]

    class Config:
        arbitrary_types_allowed = True


class PollerArgs(BaseModel):
    config: Optional[str] = Field(None, description="Configuration file")
    logging_level: Optional[str] = Field(None, alias="logging-level")
    period: Optional[int] = Field(
        None, description="Polling period for devices in seconds"
    )
    connect_timeout: Optional[int] = Field(None, alias="connect-timeout")
    logfile: Optional[str] = None
    logsize: Optional[int] = None
    log_stdout: Optional[bool] = Field(None, alias="log-stdout")
    inventory_file: Optional[str] = Field(None, alias="inventory-file")
    inventory_timeout: Optional[int] = Field(None, alias="inventory-timeout")
    update_period: Optional[int] = Field(
        None,
        alias="update-period",
        description="Time between syncing inventory from source in seconds",
    )
    inventory: Optional[str] = None
    input_dir: Optional[str] = Field(None, alias="input-dir")
    debug: Optional[bool] = None
    exclude_services: Optional[str] = Field(None, alias="exclude-services")
    no_coalescer: Optional[bool] = Field(None, alias="no-coalescer")
    outputs: Optional[List[str]] = None
    output_dir: Optional[str] = Field(None, alias="output-dir")
    run_once: Optional[str] = Field(None, alias="run-once")
    service_only: Optional[str] = Field(None, alias="service-only")
    ssh_config_file: Optional[str] = Field(None, alias="ssh-config-file")
    workers: Optional[int] = None
    version: Optional[bool] = None
    syntax_check: Optional[bool] = Field(None, alias="syntax-check")
    max_cmd_pipeline: Optional[int] = Field(None, alias="max-cmd-pipeline")


class PollerRequest(BaseModel):
    name: Optional[str] = None
    inventory: Inventory
    config: Optional[PollerArgs]


class PollerRequestWithWebhook(PollerRequest):
    webhook: Optional[WebhookConfig] = Field(
        None,
        description="Optional webhook configuration. \
        The webhook will be called once the controller has finished running.",
    )
