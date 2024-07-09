from typing import Optional, Annotated, List

from fastapi import APIRouter, Query, Depends, HTTPException

from suzieq.poller.orchestrator.orchestrator import Orchestrator
from suzieq.restServer.services.pollers_service import (
    read_controller,
    create_controller,
    update_controller,
    delete_controller,
    start_controller,
    stop_controller,
)
from suzieq.restServer.models.pollers_models import (
    PollerRequest,
    PollerRequestWithWebhook,
    PollerArgs,
    WebhookConfig,
)
from suzieq.restServer.utils.auth import (
    REQUIRE_READ,
    REQUIRE_WRITE,
    REQUIRE_DELETE,
    REQUIRE_EXECUTE,
)
from suzieq.restServer.utils.settings import (
    get_orchestrator,
    get_settings,
    Settings,
)

router = APIRouter()


@router.post(
    "/pollers",
    dependencies=[REQUIRE_WRITE],
)
async def create_poller(
    request: PollerRequest,
    settings: Settings = Depends(get_settings),
):
    try:
        return create_controller(request, settings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/pollers/start",
    dependencies=[
        REQUIRE_WRITE,
        REQUIRE_EXECUTE,
    ],
)
async def create_and_start_poller(
    request: PollerRequestWithWebhook,
    orchestrator: Orchestrator = Depends(get_orchestrator),
    settings: Settings = Depends(get_settings),
):
    try:
        controller = create_controller(request, settings)
        controller = start_controller(
            controller["id"], orchestrator, request.webhook
        )
        return controller
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/pollers/{poller_id}",
    dependencies=[REQUIRE_WRITE, REQUIRE_EXECUTE],
)
async def update_poller(
    poller_id: int,
    args: PollerArgs,
    settings: Settings = Depends(get_settings),
):
    try:
        return await update_controller(poller_id, args, settings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/pollers/{poller_id}",
    dependencies=[REQUIRE_DELETE],
)
async def delete_poller(
    poller_id: int,
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    try:
        return await delete_controller(poller_id, orchestrator)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/pollers/{poller_id}/start",
    dependencies=[REQUIRE_EXECUTE],
)
async def start_poller(
    poller_id: int,
    orchestrator: Orchestrator = Depends(get_orchestrator),
    webhook_config: Optional[WebhookConfig] = None,
):
    try:
        return start_controller(poller_id, orchestrator, webhook_config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/pollers/{poller_id}/stop",
    dependencies=[REQUIRE_EXECUTE],
)
async def stop_poller(
    poller_id: int,
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    try:
        return await stop_controller(poller_id, orchestrator)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pollers", dependencies=[REQUIRE_READ])
async def read_pollers(
    orchestrator: Orchestrator = Depends(get_orchestrator),
    poller_ids: Annotated[Optional[List[int]], Query(alias="id")] = None,
    names: Annotated[Optional[List[str]], Query(alias="name")] = None,
):
    try:
        return read_controller(orchestrator, poller_ids, names)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pollers/{poller_id}", dependencies=[REQUIRE_READ])
async def read_poller(
    poller_id: int,
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    try:
        return read_controller(orchestrator, [poller_id])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
