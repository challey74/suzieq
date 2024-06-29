import logging
import re

from enum import Flag
from typing import List, Optional

from pydantic import BaseModel, validator, root_validator


class HostConnection(BaseModel):
    hostname: str
    connection_method: str
    username: Optional[str] = None
    username_env: Optional[str] = None
    password: Optional[str] = None
    password_env: Optional[str] = None
    keyfile: Optional[str] = None

    @validator("connection_method")
    def validate_connection_method(cls, v):
        if v not in ["ssh", "https"]:
            raise ValueError('connection_method must be either "ssh" or "https"')
        return v

    @validator("username", "password", "keyfile")
    def validate_ask_value(cls, v):
        if v == "ask":
            raise ValueError("The 'ask' value is not supported with the REST server.")
        return v

    @root_validator
    def validate_username(cls, values):
        username, username_env = values.get("username"), values.get("username_env")
        if username and username_env:
            raise ValueError(
                "Only one of 'username' or 'username_env' can be provided."
            )
        return values

    @root_validator
    def validate_password(cls, values):
        password, password_env, keyfile = (
            values.get("password"),
            values.get("password_env"),
            values.get("keyfile"),
        )
        if password and password_env:
            raise ValueError(
                "Only one of 'password', 'password_env', or 'keyfile' can be provided."
            )
        if password and keyfile:
            raise ValueError(
                "Only one of 'password', 'password_env', or 'keyfile' can be provided."
            )
        if password_env and keyfile:
            raise ValueError(
                "Only one of 'password', 'password_env', or 'keyfile' can be provided."
            )
        return values


class SqPollerRequest(BaseModel):
    hosts: List[HostConnection]
    namespace: Optional[str] = None
    input_dir: Optional[str] = None
    config: Optional[str] = None
    debug: bool = False
    exclude_services: Optional[str] = None
    no_coalescer: bool = False
    outputs: List[str] = ["parquet"]
    run_once: bool = False
    service_only: Optional[str] = None
    ssh_config_file: Optional[str] = None
    update_period: Optional[int] = None
    workers: Optional[int] = None


class Poller(BaseModel):
    name: str
    source: str
    platform: str
    username: str
    password: str
    interval: int
    query: str


class EndpointFilter(logging.Filter):
    def __init__(self, endpoints: List[str]):
        super().__init__()
        self.patterns = [re.compile(re.escape(endpoint)) for endpoint in endpoints]

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return not any(pattern.search(message) for pattern in self.patterns)


class KeyPermission(Flag):
    READ = 1
    WRITE = 2
    DELETE = 4
    EXECUTE = 8
    ADMIN = 15  # All permissions


class ApiKey:
    def __init__(self, permissions: KeyPermission):
        self.permissions = permissions

    def has_permission(self, required_permission: KeyPermission) -> bool:
        return bool(self.permissions & required_permission)
