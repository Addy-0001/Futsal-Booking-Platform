import logging

from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Uniform error envelope so the Vue/Nuxt client always parses the same shape:
        {"error": {"type": "...", "detail": ..., "status": <int>}}
    Never leaks stack traces. Unhandled exceptions become a clean 500.
    """
    # Map Django's own exceptions into DRF's so they get a structured response too.
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()

    response = exception_handler(exc, context)

    if response is None:
        # Unhandled -> log for Sentry and return a generic 500 (no internals).
        logger.exception("Unhandled exception", exc_info=exc)
        return Response(
            {"error": {"type": "server_error",
                       "detail": "Something went wrong. Please try again.",
                       "status": 500}},
            status=500,
        )

    response.data = {
        "error": {
            "type": exc.__class__.__name__,
            "detail": response.data,
            "status": response.status_code,
        }
    }
    return response
