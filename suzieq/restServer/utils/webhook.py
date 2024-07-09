import logging

from typing import Dict, Any, Optional

import requests

from suzieq.restServer.models.shared_models import WebhookConfig


def send_webhook(
    webhook: WebhookConfig, controller: Optional[Dict[str, Any]] = None
):
    payload = None
    if webhook.send_config and isinstance(controller, dict):
        payload = controller
    if webhook.custom_payload:
        if not payload:
            payload = {}
        payload["custom"] = webhook.custom_payload

    try:
        response = requests.post(
            webhook.url,
            json=payload,
            verify=webhook.verify_ssl,
            timeout=webhook.timeout,
            headers=webhook.headers,
            params=webhook.params,
            auth=webhook.auth,
            cert=webhook.cert,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending webhook: {e}")
