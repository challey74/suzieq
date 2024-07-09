import argparse
import sys

import uvicorn

from fastapi import FastAPI, HTTPException

from suzieq.restServer.models.shared_models import WebhookConfig
from suzieq.restServer.routes.pollers_route import router as pollers_router
from suzieq.restServer.routes.query_route import router as query_router
from suzieq.restServer.services.pollers_service import ResourceContext
from suzieq.restServer.utils.settings import Settings
from suzieq.restServer.utils.webhook import send_webhook
from suzieq.shared.utils import print_version, sq_get_config_file


app = FastAPI(
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    on_shutdown=[ResourceContext.cleanup_all_controller_resources],
)

app.include_router(pollers_router, prefix="/api/v2")
app.include_router(query_router, prefix="/api/v2")


def rest_main(*args) -> None:
    if not args:
        args = tuple(sys.argv)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--config", type=str, help="alternate config file", default=None
    )
    parser.add_argument(
        "--no-https",
        help="Turn off HTTPS",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--version",
        "-V",
        help="print Suzieq version",
        default=False,
        action="store_true",
    )

    userargs = parser.parse_args()
    if userargs.version:
        print_version()
        sys.exit(0)

    config_file = sq_get_config_file(userargs.config)

    settings = Settings.from_config(config_file)
    settings.configure_uvicorn_logging()
    if settings.no_https:
        uvicorn.run(
            app,
            host=settings.address,
            port=settings.port,
            log_level=settings.logging_level,
        )
    else:
        uvicorn.run(
            app,
            host=settings.address,
            port=settings.port,
            ssl_keyfile=settings.rest_keyfile,
            ssl_certfile=settings.rest_certfile,
            log_level=settings.logging_level,
        )


@app.get("/api/v1/{rest_of_path:path}", deprecated=True)
def deprecated_function(rest_of_path: str):
    return [{"error": "v1 is deprecated, use API version v2"}]


@app.get("/api/v2/{command}", include_in_schema=False)
def missing_verb(command):
    raise HTTPException(
        status_code=404,
        detail=f"{command} command missing a verb. \
        for example /api/v2/{command}/show",
    )


@app.get("/", include_in_schema=False)
def bad_path():
    raise HTTPException(
        status_code=404,
        detail="bad path. Try something like '/api/v2/device/show' \
        or '/api/docs'",
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/v2/test/webhook")
def test_webhook(webhook: WebhookConfig):
    try:
        send_webhook(webhook)
        return {"message": "webhook sent"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error sending webhook: {e}"
        )
