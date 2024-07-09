import uuid


def append_error_id(message: str):
    u = uuid.uuid1()
    return f"{message} id={u}"
