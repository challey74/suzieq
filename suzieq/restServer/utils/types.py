import logging
import re

from enum import Flag
from typing import List


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
