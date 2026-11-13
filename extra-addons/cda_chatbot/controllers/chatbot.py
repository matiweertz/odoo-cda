from odoo import http
from odoo.http import request

from odoo.addons.cda_api.controllers.auth import api_user
from odoo.addons.cda_api.models.claim_api import ClaimApiError

API = "/api/v1"


def _error(exc):
    return request.make_json_response(
        {"detail": exc.detail, "code": exc.code}, status=exc.status
    )


class CdaApiChatbot(http.Controller):
    @http.route(
        f"{API}/chatbot/tree",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
    )
    def chatbot_tree(self, **params):
        """Árbol publicado. Inmutable por versión, así que se puede cachear."""
        api_user()
        publication = request.env["cda.chatbot.publication"]._active_publication()
        if not publication:
            return request.make_json_response(
                {"detail": "Todavía no hay una versión publicada.", "code": "no_publication"},
                status=404,
            )

        etag = '"v%s"' % publication.version
        if request.httprequest.headers.get("If-None-Match") == etag:
            return request.make_response("", status=304, headers=[("ETag", etag)])

        return request.make_response(
            publication.payload,
            headers=[
                ("Content-Type", "application/json; charset=utf-8"),
                ("ETag", etag),
                ("Cache-Control", "public, max-age=300"),
            ],
        )

    @http.route(
        f"{API}/chatbot/claim",
        type="json2",
        auth="public",
        methods=["POST"],
    )
    def chatbot_claim(self, **payload):
        api_user()
        try:
            result = request.env["cda.chatbot.node"]._create_claim_from_chat(payload)
        except ClaimApiError as exc:
            return _error(exc)
        return request.make_json_response(result, status=201)
