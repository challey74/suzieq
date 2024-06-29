import os
import tempfile
import uuid
import yaml

from suzieq.poller.sq_poller import start_controller
from suzieq.restServer.utils.types import SqPollerRequest
from suzieq.restServer.utils.config import get_settings


class TempResourceContext:
    def __init__(self):
        self.temp_envs = {}
        self.temp_files = []

    def create_temp_env(self, key, value):
        env_name = f"SQPOLLER_{key}_{uuid.uuid4().hex}"
        os.environ[env_name] = value
        self.temp_envs[env_name] = value
        return env_name

    def create_temp_file(self, content):
        temp_dir = get_settings().temp_inventory_dir
        os.makedirs(temp_dir, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w+", delete=False, dir=temp_dir, encoding="utf-8"
        ) as temp_file:
            yaml.dump(content, temp_file)
            self.temp_files.append(temp_file.name)

    def cleanup(self):
        for env_name in self.temp_envs:
            del os.environ[env_name]
        for file_path in self.temp_files:
            if os.path.exists(file_path):
                os.unlink(file_path)


def create_inventory_file(inventory_data, run_once, temp_resource_context=None):
    inventory_dir = get_settings().inventory_dir

    if run_once and temp_resource_context:
        return temp_resource_context.create_temp_file(inventory_data)

    inventory_file = os.path.join(inventory_dir, f"inventory_{uuid.uuid4().hex}.yaml")
    os.makedirs(inventory_dir, exist_ok=True)
    with open(inventory_file, "w+", encoding="utf-8") as file:
        yaml.dump(inventory_data, file)
    return inventory_file


def generate_host_url(host, run_once, temp_resource_context=None):
    if host.username:
        username = f"username={host.username}"
    elif host.username_env:
        username = f"username=env:{host.username_env}"
    elif run_once and temp_resource_context:
        username_env = temp_resource_context.create_temp_env("USERNAME", host.username)
        username = f"username=env:{username_env}"
    else:
        raise ValueError("Either 'username' or 'username_env' must be provided.")

    if host.password:
        password_or_keyfile = f"password={host.password}"
    elif host.password_env:
        password_or_keyfile = f"password=env:{host.password_env}"
    elif host.keyfile:
        password_or_keyfile = f"keyfile={host.keyfile}"
    elif run_once and temp_resource_context:
        password_env = temp_resource_context.create_temp_env("PASSWORD", host.password)
        password_or_keyfile = f"password=env:{password_env}"
    else:
        raise ValueError(
            "One of 'password', 'password_env', or 'keyfile' must be provided."
        )

    return (
        f"{host.connection_method}://{host.hostname} {username} {password_or_keyfile}"
    )


async def create_poller(request: SqPollerRequest):
    user_args = request.dict()

    run_once = user_args["run_once"]
    temp_resource_context = TempResourceContext() if run_once else None

    hosts = []
    for host in user_args["hosts"]:
        url = generate_host_url(host, run_once, temp_resource_context)
        hosts.append({"url": url})

    inventory_data = {"sources": [{"name": "rest-server-native", "hosts": hosts}]}

    if namespace := user_args["namespace"]:
        inventory_data["namespaces"] = [
            {"name": namespace, "source": "rest-server-native"}
        ]

    try:
        inventory_file = create_inventory_file(
            inventory_data, run_once, temp_resource_context
        )
        user_args["inventory"] = inventory_file
        await start_controller(user_args, get_settings().config_data)

        if run_once and temp_resource_context:
            temp_resource_context.cleanup()

        return {"message": "SqPoller started successfully"}
    except Exception as e:
        if run_once and temp_resource_context:
            temp_resource_context.cleanup()
        raise ValueError(str(e))
