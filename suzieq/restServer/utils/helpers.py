import uuid


def append_error_id(message):
    u = uuid.uuid1()
    return f"{message} id={u}"
