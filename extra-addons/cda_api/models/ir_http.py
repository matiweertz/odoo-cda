import logging

from odoo import http, models
from odoo.exceptions import (
    AccessDenied,
    AccessError,
    MissingError,
    UserError,
    ValidationError,
)
from odoo.http import request
from werkzeug.exceptions import HTTPException

from .claim_api import ClaimApiError

_logger = logging.getLogger(__name__)

API_PREFIX = "/api/v1/"
SESSION_MISMATCH = "Session user does not match"
HTTP_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    415: "unsupported_media_type",
    429: "too_many_requests",
}


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _handle_error(cls, exception):
        if not request or not request.httprequest.path.startswith(API_PREFIX):
            return super()._handle_error(exception)
        status, code, detail = cls._api_error(exception)
        return request.make_json_response({"detail": detail, "code": code}, status=status)

    @classmethod
    def _api_error(cls, exception) -> tuple[int, str, str]:
        if isinstance(exception, ClaimApiError):
            return exception.status, exception.code, exception.detail
        if isinstance(exception, HTTPException):
            status = exception.code or 500
            return (
                status,
                HTTP_CODES.get(status, "http_error"),
                exception.description or exception.name,
            )
        if isinstance(exception, AccessDenied):
            if SESSION_MISMATCH in str(exception):
                return (
                    403,
                    "session_mismatch",
                    "La sesión de Odoo no es la dueña de la API key. "
                    "Abrí /api/v1/docs en una ventana incógnita o cerrá la sesión de Odoo.",
                )
            return 403, "forbidden", str(exception)
        if isinstance(exception, AccessError):
            return 403, "forbidden", str(exception)
        if isinstance(exception, MissingError):
            return 404, "not_found", str(exception)
        if isinstance(exception, ValidationError):
            return 422, "validation_error", str(exception)
        if isinstance(exception, UserError):
            return 422, "validation_error", str(exception)
        _logger.exception("Error no controlado en la API REST", exc_info=exception)
        return 500, "internal_error", "Error interno del servicio."
