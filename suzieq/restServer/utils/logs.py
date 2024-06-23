import logging
import re

from typing import List

import uvicorn


class EndpointFilter(logging.Filter):
    def __init__(self, endpoints: List[str]):
        super().__init__()
        self.patterns = [re.compile(re.escape(endpoint)) for endpoint in endpoints]

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return not any(pattern.search(message) for pattern in self.patterns)


def configure_uvicorn_logging(
    log_stdout: bool, log_to_file: bool, logfile: str, logsize: int
):
    """Configure uvicorn logging to log to stdout and/or file.
    This contains the default behavior of only logging
    to a file if logfile is present and log_stdout is False and only logging to
    stdout if log_stdout is True. log_to_file was added to allow
    for disabling file logging or logging to both a file and stdout.
    """
    log_config = uvicorn.config.LOGGING_CONFIG

    endpoint_filter = EndpointFilter(excluded_endpoints)

    log_config["handlers"]["default"]["filters"] = ["endpoint_filter"]
    log_config["handlers"]["access"]["filters"] = ["endpoint_filter"]

    log_config["filters"] = {
        "endpoint_filter": {
            "()": "configure_uvicorn_logging.EndpointFilter",
            "endpoints": excluded_endpoints,
        }
    }

    def set_rotating_file_handler(logname):
        log_config["handlers"][logname]["filename"] = logfile
        log_config["handlers"][logname][
            "class"
        ] = "logging.handlers.RotatingFileHandler"
        log_config["handlers"][logname]["maxBytes"] = logsize
        log_config["handlers"][logname]["backupCount"] = 2

    def remove_stream_handler(logname):
        if "stream" in log_config["handlers"][logname]:
            del log_config["handlers"][logname]["stream"]

    if log_to_file:
        if logfile:
            set_rotating_file_handler("default")
            set_rotating_file_handler("access")

        if not log_stdout:
            remove_stream_handler("default")
            remove_stream_handler("access")

    elif logfile and not log_stdout:
        set_rotating_file_handler("access")
        remove_stream_handler("default")
        remove_stream_handler("access")
        set_rotating_file_handler("default")
