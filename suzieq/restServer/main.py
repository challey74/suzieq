import argparse
import sys

import uvicorn

from fastapi import FastAPI, HTTPException

from suzieq.shared.utils import print_version, sq_get_config_file
from suzieq.restServer.utils.config import Settings
from suzieq.restServer.routes.sq_poller import router as sq_poller_router
from suzieq.restServer.routes.query import router as query_router


app = FastAPI(
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)
app.include_router(sq_poller_router, prefix="/api/v2")
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
        detail=f"{command} command missing a verb. for example /api/v2/{command}/show",
    )


@app.get("/", include_in_schema=False)
def bad_path():
    raise HTTPException(
        status_code=404,
        detail="bad path. Try something like '/api/v2/device/show' or '/api/docs'",
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}
