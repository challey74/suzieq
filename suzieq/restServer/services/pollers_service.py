import logging
import os

from datetime import datetime
from typing import Optional, Dict, Any, List

import yaml

from fastapi import HTTPException

from suzieq.shared.exceptions import SqPollerConfError
from suzieq.poller.orchestrator.orchestrator import Orchestrator
from suzieq.restServer.models.pollers_models import (
    PollerRequest,
    PollerArgs,
    WebhookConfig,
)
from suzieq.restServer.utils.settings import Settings
from suzieq.restServer.utils.webhook import send_webhook


class ResourceContext:
    _instance = None
    instanciated = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self.instanciated:
            return

        self.controller_resources: Dict[int, Any] = {}
        self.instanciated = True

    def create_inventory_file(
        self,
        request: PollerRequest,
        inventory_dir: str,
    ) -> str:
        inventory_data = request.dict(exclude_none=True, by_alias=True).get(
            "inventory"
        )
        print(inventory_data)
        inventory_file = os.path.join(
            inventory_dir,
            (
                f"{request.name}_"
                if request.name
                else ""
                + f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')}.yml"
            ),
        )
        os.makedirs(inventory_dir, exist_ok=True)

        with open(inventory_file, "w+", encoding="utf-8") as file:
            yaml.dump(inventory_data, file)

        return inventory_file

    def cleanup_controller_resources(self, controller_id: int) -> None:
        data = self.controller_resources.get(controller_id)
        if not data:
            return

        for env in data["envs"]:
            name = env[4:] if env.startswith("env:") else env
            os.environ.pop(name, None)

        os.remove(data["file"])

    def track_controller_resources(
        self, controller_id: int, inventory_file: str, request: PollerRequest
    ) -> None:
        envs = []

        if request.inventory.auths:
            for auth in request.inventory.auths:
                envs.extend(auth.created_env_names)

        for source in request.inventory.sources:
            if hasattr(source, "created_env_names"):
                envs.extend(source.created_env_names)

        self.controller_resources[controller_id] = {
            "envs": envs,
            "file": inventory_file,
        }

    @classmethod
    def cleanup_all_controller_resources(cls) -> None:
        context = cls._instance
        if not context:
            return

        for controller_id in context.controller_resources:
            context.cleanup_controller_resources(controller_id)

    @classmethod
    def handle_error(
        cls, request: PollerRequest, inventory_file: Optional[str] = None
    ):
        if not cls.instanciated:
            return

        for source in request.inventory.sources:
            if hasattr(source, "created_env_names"):
                for env in source.created_env_names:
                    os.environ.pop(env, None)

        if request.inventory.auths:
            for auth in request.inventory.auths:
                for env in auth.created_env_names:
                    os.environ.pop(env, None)

        if inventory_file and os.path.exists(inventory_file):
            os.remove(inventory_file)


def create_controller(
    request: PollerRequest, settings: Settings
) -> Dict[str, Any]:
    args = {}
    try:
        args = request.config.dict() if request.config else PollerArgs().dict()

        resource_context = ResourceContext()
        args["inventory"] = resource_context.create_inventory_file(
            request, settings.inventory_dir
        )

        controller = settings.orchestrator.create_controller(
            args, settings.config_data, request.name
        )

        resource_context.track_controller_resources(
            controller.id, args["inventory"], request
        )

        return controller.dict()

    except (ValueError, SqPollerConfError) as e:
        logging.error(f"Error creating controller: {e}")
        ResourceContext.handle_error(request, args.get("inventory"))

        raise HTTPException(
            status_code=500, detail=f"Error creating controller: {e}"
        )


async def update_controller(
    controller_id: int, args: PollerArgs, settings: Settings
) -> Optional[Dict[str, Any]]:
    controller = await settings.orchestrator.update_controller(
        controller_id, args.dict(), settings.config_data
    )

    return controller.dict()


async def delete_controller(poller_id: int, orchestrator: Orchestrator):
    controller_dict = await orchestrator.delete_controller(poller_id)
    if controller_dict:
        ResourceContext().cleanup_controller_resources(controller_dict["id"])

    return controller_dict


def start_controller(
    poller_id: int,
    orchestrator: Orchestrator,
    webhook_config: Optional[WebhookConfig] = None,
):
    controller = orchestrator.get_controller(poller_id)

    callback = (
        (lambda controller: send_webhook(webhook_config, controller.dict()))
        if webhook_config
        else None
    )

    controller, _ = orchestrator.start_controller(poller_id, callback)

    return controller.dict() if controller else None


async def stop_controller(poller_id: int, orchestrator: Orchestrator):
    controller = await orchestrator.stop_controller(poller_id)
    return controller.dict() if controller else None


def read_controller(
    orchestrator: Orchestrator,
    poller_ids: Optional[List[int]] = None,
    poller_names: Optional[List[str]] = None,
):
    if not poller_ids and not poller_names:
        return [
            controller.dict()
            for controller in orchestrator.controllers.values()
        ]

    controllers = set()

    if poller_ids:
        controllers.update(
            orchestrator.get_controller(poller_id)
            for poller_id in poller_ids
            if poller_id in orchestrator.controllers
        )

    if poller_names:
        controllers.update(
            orchestrator.get_controller_by_name(poller_name)
            for poller_name in poller_names
            if poller_name in orchestrator.name_to_id_map
        )

    return [controller.dict() for controller in controllers]
