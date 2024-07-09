import asyncio

from copy import deepcopy
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Any, Callable, Tuple, List
from argparse import Namespace

from suzieq.poller.controller.controller import Controller


class ControllerStates(Enum):
    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"
    DELETED = "deleted"


class ControllerWithMetadata(Controller):
    """Controller class with metadata."""

    def __init__(
        self,
        args: Namespace,
        config: Dict[str, Any],
        controller_id: int,
        name: Optional[str] = None,
    ):
        super().__init__(args, config)
        self.id: int = controller_id
        self.name: str = name or f"controller-{controller_id}"
        self.created_time: str = datetime.now().isoformat()
        self.start_time: Optional[str] = None
        self.stop_time: Optional[str] = None
        self.updated_time: Optional[str] = None
        self.state: ControllerStates = ControllerStates.CREATED

    def dict(self):
        """Return the metadata and config of the controller."""
        config = deepcopy(self._config)
        if manager_config := config.get("manager"):

            manager_config.pop("config-dict", None)

        return {
            "id": self.id,
            "name": self.name,
            "created_time": self.created_time,
            "last_start_time": self.start_time,
            "last_stop_time": self.stop_time,
            "last_updated_time": self.updated_time,
            "state": self.state.value,
            "config": config,
        }

    async def stop(self):
        """Stop the controller and update its state"""

        await super().stop()
        self.stop_time = datetime.now().isoformat()
        self.state = ControllerStates.STOPPED

    def start(self, callback: Optional[Callable] = None) -> asyncio.Task:
        """Start the controller and update its state"""

        def _callback(_):
            self.state = ControllerStates.STOPPED
            self.stop_time = datetime.now().isoformat()
            if callback:
                callback(self)

        self.init()

        self.state = ControllerStates.RUNNING
        self.start_time = datetime.now().isoformat()

        task = asyncio.create_task(super().run())
        task.add_done_callback(_callback)

        return task

    def update(self, args: Dict[str, Any], config: Dict[str, Any]):
        """Reinitialize the controller with the updated config."""

        self.updated_time = datetime.now().isoformat()
        super().__init__(Namespace(**args), config)

    def deleted(self):
        """Update the state of the controller to deleted"""

        self.state = ControllerStates.DELETED


class Orchestrator:
    """Orchestrator class to manage controllers."""

    def __init__(self) -> None:
        self._next_controller_id: int = 0
        self._released_controller_ids: List[int] = []
        self.controllers: Dict[int, ControllerWithMetadata] = {}
        self.name_to_id_map: Dict[str, int] = {}

    def create_controller(
        self,
        args: Dict[str, Any],
        config: Dict[str, Any],
        name: Optional[str] = None,
    ) -> ControllerWithMetadata:
        """Create a new controller."""

        namespace_args = Namespace(**args)

        controller = ControllerWithMetadata(
            namespace_args, config, self._generate_controller_id(), name
        )

        self.controllers[controller.id] = controller
        self.name_to_id_map[controller.name] = controller.id

        return controller

    def _generate_controller_id(self) -> int:
        if len(self._released_controller_ids) > 0:
            return self._released_controller_ids.pop()

        r = self._next_controller_id
        self._next_controller_id += 1

        return r

    def get_controller(
        self, controller_id: int
    ) -> Optional[ControllerWithMetadata]:
        """Get the controller with the given ID."""

        controller = self.controllers.get(controller_id)
        return controller

    def get_controller_by_name(
        self, name: str
    ) -> Optional[ControllerWithMetadata]:
        """Get the controller with the given name."""

        controller_id = self.name_to_id_map.get(name)
        return (
            self.get_controller(controller_id)
            if controller_id is not None
            else None
        )

    def start_controller(
        self, controller_id: int, callback: Optional[Callable] = None
    ) -> Tuple[ControllerWithMetadata, asyncio.Task]:
        """Start the controller with the given ID."""

        controller = self.get_controller(controller_id)
        if not controller:
            raise ValueError(f"Controller with ID: {controller_id} not found")

        task = controller.start(callback)

        return controller, task

    async def stop_controller(
        self, controller_id: int
    ) -> ControllerWithMetadata:
        """Stop the controller with the given ID."""

        controller = self.get_controller(controller_id)
        if not controller:
            raise ValueError(f"Controller with ID: {controller_id} not found")

        if controller.state == ControllerStates.RUNNING:
            await controller.stop()

        return controller

    async def delete_controller(self, controller_id: int) -> Dict[str, Any]:
        """Stop controller and remove it from the orchestrator."""

        controller = self.get_controller(controller_id)
        if not controller:
            raise ValueError(f"Controller with ID: {controller_id} not found")

        if controller.state == ControllerStates.RUNNING:
            await controller.stop()

        controller = self.controllers.pop(controller_id)
        self._released_controller_ids.append(controller_id)
        controller.deleted()

        return controller.dict()

    async def update_controller(
        self, controller_id: int, args: Dict[str, Any], config: Dict
    ) -> ControllerWithMetadata:
        """Update the config of the controller with the given ID."""

        controller = self.get_controller(controller_id)
        if not controller:
            raise ValueError(f"Controller with ID: {controller_id} not found")

        was_running = False
        if controller.state == ControllerStates.RUNNING:
            was_running = True
            await controller.stop()

        if not args.get("inventory"):
            args["inventory"] = controller._config["source"]["path"]

        config = deepcopy(config)
        config.update({"poller": deepcopy(controller._config)})

        controller.update(args, config)

        if was_running:
            controller.start()

        return controller
