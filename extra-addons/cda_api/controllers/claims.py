import re

from odoo import http
from odoo.http import request

from ..models.claim_api import ClaimApiError

API = "/api/v1"
CLIENT_HEADER = "X-Client"


def _client() -> str | None:
    raw = request.httprequest.headers.get(CLIENT_HEADER) or ""
    cleaned = re.sub(r"[^A-Za-z0-9 ._/-]", "", raw).strip()[:40]
    return cleaned or None


def _error(exc: ClaimApiError):
    return request.make_json_response(
        {"detail": exc.detail, "code": exc.code}, status=exc.status
    )


class CdaApiClaims(http.Controller):
    @http.route(
        f"{API}/claims/search",
        type="http",
        auth="bearer",
        methods=["GET"],
        csrf=False,
    )
    def claims_search(self, **params):
        try:
            result = request.env["cda.claim.api"].search_claims(params)
        except ClaimApiError as exc:
            return _error(exc)
        return request.make_json_response(result)

    @http.route(
        f"{API}/claims/<int:claim_id>",
        type="http",
        auth="bearer",
        methods=["GET"],
        csrf=False,
    )
    def claims_get(self, claim_id, **params):
        try:
            result = request.env["cda.claim.api"].get_claim(claim_id)
        except ClaimApiError as exc:
            return _error(exc)
        return request.make_json_response(result)

    @http.route(
        f"{API}/claims",
        type="json2",
        auth="bearer",
        methods=["POST"],
    )
    def claims_create(self, **payload):
        try:
            result = request.env["cda.claim.api"].create_claim(payload, origin=_client())
        except ClaimApiError as exc:
            return _error(exc)
        return request.make_json_response(result, status=201)

    @http.route(
        f"{API}/claims/<int:claim_id>",
        type="json2",
        auth="bearer",
        methods=["PATCH"],
    )
    def claims_update(self, claim_id, **payload):
        try:
            result = request.env["cda.claim.api"].update_claim(
                claim_id, payload, origin=_client()
            )
        except ClaimApiError as exc:
            return _error(exc)
        return request.make_json_response(result)

    @http.route(
        f"{API}/claims/attachments/<int:attachment_id>",
        type="http",
        auth="bearer",
        methods=["GET"],
        csrf=False,
    )
    def attachment(self, attachment_id, **params):
        api = request.env["cda.claim.api"]
        try:
            attachment = request.env["cda.claim.attachment"].browse(attachment_id)
            if attachment.exists() and attachment.url and not attachment.file_size:
                return request.redirect(attachment.url)
            data, file_name, mime = api.attachment_content(attachment_id)
        except ClaimApiError as exc:
            return _error(exc)
        headers = [
            ("Content-Type", mime),
            ("Content-Length", str(len(data))),
            ("Content-Disposition", f'inline; filename="{file_name}"'),
        ]
        return request.make_response(data, headers=headers)

    @http.route(
        f"{API}/claim-types",
        type="http",
        auth="bearer",
        methods=["GET"],
        csrf=False,
    )
    def claim_types(self, **params):
        return request.make_json_response(request.env["cda.claim.api"].claim_types())
