"""Endpoint de mantenimiento: actualiza un módulo sin acceso a la VM.

Es el mismo camino que usa la pantalla de Aplicaciones
(ir.module.module.button_immediate_upgrade), pero disparable por HTTP para
poder aplicar un cambio de esquema cuando el contenedor ya corre el código
nuevo y nadie tiene shell en el servidor.

Temporal: hay que borrar este archivo después de usarlo.
"""

import hmac
import logging
import os
import traceback

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

# Token propio del endpoint. Se puede fijar por variable de entorno; si no,
# vale el que está acá.
TOKEN = os.environ.get("CDA_MAINT_TOKEN", "d8f3a1c95e7b42a6b0c4e2f7a9d1355c")

PERMITIDOS = ("cda_claims", "cda_api", "cda_chatbot")


class MaintController(http.Controller):
    @http.route(
        "/api/v1/admin/upgrade",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
        save_session=False,
    )
    def upgrade(self, **params):
        recibido = request.httprequest.headers.get("X-Maint-Token") or ""
        if not hmac.compare_digest(recibido, TOKEN):
            return request.make_json_response(
                {"detail": "No autorizado."}, status=403
            )

        modulo = (params.get("module") or "cda_claims").strip()
        if modulo not in PERMITIDOS:
            return request.make_json_response(
                {"detail": "Módulo no permitido."}, status=400
            )

        # El route es público: se corre como superusuario para poder actualizar.
        env = request.env(user=1, su=True)
        registro = env["ir.module.module"].search(
            [("name", "=", modulo)], limit=1
        )
        if not registro:
            return request.make_json_response(
                {"detail": "Módulo inexistente.", "module": modulo}, status=404
            )

        anterior = registro.latest_version
        try:
            registro.button_immediate_upgrade()
        except Exception as error:  # noqa: BLE001 - se devuelve el detalle
            _logger.exception("Fallo la actualización de %s", modulo)
            return request.make_json_response(
                {
                    "ok": False,
                    "module": modulo,
                    "type": type(error).__name__,
                    "error": str(error),
                    "traceback": traceback.format_exc()[-2500:],
                },
                status=500,
            )

        return request.make_json_response(
            {
                "ok": True,
                "module": modulo,
                "version_antes": anterior,
                "version_ahora": registro.latest_version,
                "estado": registro.state,
            }
        )
