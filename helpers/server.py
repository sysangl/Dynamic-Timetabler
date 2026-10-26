"""
Functions realted to server
"""

from typing import Any

from flask import Response, jsonify


def _json_success(payload: dict[str, Any] | None = None, status_code:int = 200) -> tuple[Response, int]:
    """Return a JSON payload with ``status: "success"``."""
    result: dict[str, Any] = {"status": "success"}
    if payload:
        result.update(payload)
    return jsonify(result), status_code


def _json_error(message: str, status_code: int = 400) -> tuple[dict[str, Any], int]:
    """Return an error JSON payload with the given HTTP status."""
    return {"status": "error", "message": message}, status_code
