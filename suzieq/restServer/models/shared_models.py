import os

from typing import Any, Dict, Optional, Tuple

from pydantic import BaseModel, Field, HttpUrl, validator


class WebhookConfig(BaseModel):
    url: HttpUrl
    send_config: bool = Field(
        False,
        alias="send-config",
        description="If true, the poller configuration and \
        state will be included in the webhook payload.",
    )
    custom_payload: Optional[Dict[str, Any]] = Field(
        None,
        alias="custom-payload",
        description="Custom payload included in the 'custom' \
        key of the webhook payload.",
    )
    verify_ssl: bool = True
    timeout: Optional[int] = 60
    headers: Optional[Dict[str, str]] = {"Content-Type": "application/json"}
    params: Optional[Dict[str, Any]] = None
    auth: Optional[Tuple[str, str]] = None
    cert: Optional[str] = None

    @validator("cert")
    def validate_cert(cls, v):
        if v and not os.path.exists(v):
            raise ValueError(f"Cert file {v} does not exist")
        return v
