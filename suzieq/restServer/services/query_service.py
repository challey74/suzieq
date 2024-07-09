from typing import Any, Dict

from fastapi import Response, HTTPException

from suzieq.shared.exceptions import UserQueryError
from suzieq.shared.utils import DataFormats
from suzieq.sqobjects import get_sqobject
from suzieq.restServer.utils.helpers import append_error_id
from suzieq.restServer.utils.settings import get_settings


def read_shared(command: str, params, config_file: str):
    """all the shared code for each of these read functions"""

    command_args, verb_args = create_filters(params)

    verb = cleanup_verb(params.verb)

    data_format = getattr(params, "format")
    if data_format not in DataFormats:
        raise HTTPException(
            status_code=405,
            detail=append_error_id(
                f"Unsupported output format '{data_format}'. \
            Supported formats are {', '.join(DataFormats)}."
            ),
        )

    response = run_command_verb(
        command, verb, command_args, verb_args, config_file, data_format
    )

    return response


def create_filters(params):
    remove_args = ["verb", "token", "access_token", "format", "request"]
    command_exclusive_args = [
        "start_time",
        "end_time",
        "view",
        "format",
    ]
    shared_args = ["namespace", "hostname", "columns"]

    params = {
        k: v
        for k, v in params.dict().items()
        if v is not None and k not in remove_args
    }
    command_args = {
        k: v
        for k, v in params.items()
        if k in command_exclusive_args or k in shared_args
    }

    verb_args = {
        k: v for k, v in params.items() if k not in command_exclusive_args
    }

    return command_args, verb_args


def cleanup_verb(verb):
    if verb == "show":
        verb = "get"
    if verb == "assert":
        verb = "aver"
    return verb


def run_command_verb(
    command: str,
    verb: str,
    command_args: Dict[str, Any],
    verb_args: Dict[str, Any],
    config_file: str,
    data_format: DataFormats,
):
    """
    Runs the command and verb with the command_args and verb_args

    HTTP Return Codes
        404 -- Missing command or argument (including missing valid path)
        405 -- Missing or incorrect query parameters
        422 -- FastAPI validation errors
        500 -- Exceptions
    """

    svc = get_sqobject(command)
    try:
        svc_inst = svc(
            **command_args,
            config_file=get_settings().config_file,
            engine_name="pandas",
        )
        df = getattr(svc_inst, verb)(**verb_args)
    except AttributeError as err:
        raise HTTPException(status_code=404, detail=(f"{err}"))
    except NotImplementedError as err:
        raise HTTPException(
            status_code=404,
            detail=f"{verb} not supported for {command}: {err}",
        )
    except (TypeError, ValueError) as err:
        raise HTTPException(
            status_code=405,
            detail=f"bad keyword/filter for {command} {verb}: {err}",
        )
    except UserQueryError as err:
        raise HTTPException(status_code=500, detail=f"UserQueryError: {err}")
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"{err}")

    if df.columns.to_list() == ["error"]:
        raise HTTPException(
            status_code=405,
            detail=f"bad keyword/filter for {command} {verb}: \
            {df['error'][0]}",
        )

    res_content = None
    media_type = None
    if data_format == DataFormats.JSON:
        if verb == "summarize":
            json_orient = "columns"
        else:
            json_orient = "records"
        media_type = "application/json"
        res_content = df.to_json(orient=json_orient)
    elif data_format == DataFormats.MARKDOWN:
        res_content = df.to_markdown()
        media_type = "text/plain"
    elif data_format == DataFormats.CSV:
        res_content = df.to_csv()
        media_type = "text/csv"
    elif data_format == DataFormats.TEXT:
        res_content = df.to_string()
        media_type = "text/plain"

    # have to return a Reponse so that it won't turn the markdown into JSON
    return Response(content=res_content, media_type=media_type)
