from typing import Any


def success_response(data: Any = None, message: str = "success") -> dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "data": data,
    }


def error_response(message: str, details: Any = None) -> dict[str, Any]:
    payload = {
        "success": False,
        "message": message,
    }
    if details is not None:
        payload["details"] = details
    return payload
