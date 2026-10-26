from typing import Any, Optional


def _json_success(payload: Optional[dict[str, Any]] = None) -> tuple[dict[str, Any], int]:
    """Return a 200 JSON payload with ``status: "success"``."""
    result: dict[str, Any] = {"status": "success"}
    if payload:
        result.update(payload)
    return result, 200


def _json_error(message: str, status_code: int = 400) -> tuple[dict[str, Any], int]:
    """Return an error JSON payload with the given HTTP status."""
    return {"status": "error", "message": message}, status_code
