from fastapi import Depends, APIRouter

from suzieq.restServer.services.sq_poller_services import (
    create_poller,
)
from suzieq.restServer.utils.auth import (
    REQUIRE_WRITE,
    REQUIRE_DELETE,
    REQUIRE_EXECUTE,
)
from suzieq.restServer.utils.types import Poller, SqPollerRequest

router = APIRouter()


@router.post(
    "/sqPoller", dependencies=[Depends(REQUIRE_WRITE), Depends(REQUIRE_EXECUTE)]
)
async def create(request: SqPollerRequest):
    return await create_poller(request)


@router.patch("/sqPoller/{poller_id}", dependencies=[Depends(REQUIRE_WRITE)])
async def update(poller_id: str, poller: Poller):
    pass


@router.delete("/sqPoller/{poller_id}", dependencies=[Depends(REQUIRE_DELETE)])
async def delete(poller_id: str):
    pass


@router.post("/sqPoller/{poller_id}/start", dependencies=[Depends(REQUIRE_EXECUTE)])
async def start(poller_id: str):
    pass


@router.post("/sqPoller/{poller_id}/stop", dependencies=[Depends(REQUIRE_EXECUTE)])
async def stop(poller_id: str):
    pass
