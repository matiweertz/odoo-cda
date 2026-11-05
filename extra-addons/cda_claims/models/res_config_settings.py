from odoo import fields, models
from odoo.exceptions import ValidationError
from odoo.http import request


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cda_api_key = fields.Char(
        string="API Key",
        config_parameter="cda_claims.api_key",
        help="Se envía en el header X-Api-Key de cada request.",
    )
    cda_service_user_id = fields.Many2one(
        "res.users",
        string="Usuario de servicio",
        config_parameter="cda_claims.service_user_id",
        help="Usuario con el que se firman los reclamos que llegan por la API.",
    )
    cda_api_docs_url = fields.Char(
        string="Ruta de documentación",
        config_parameter="cda_claims.api_docs_url",
        default="/api/v1/docs",
        help="Ruta del Swagger dentro de este mismo servidor. "
        "El dominio se toma del Odoo.",
    )

    def action_cda_save(self):
        self.ensure_one()
        self.set_values()
        return {"type": "ir.actions.client", "tag": "reload"}

    def _cda_docs_url(self):
        self.ensure_one()
        path = (self.cda_api_docs_url or "").strip()
        if not path:
            raise ValidationError("Configurá la ruta de documentación.")
        if path.startswith("http://") or path.startswith("https://"):
            return path
        origin = ""
        try:
            host = request.httprequest.host_url
            origin = host.rstrip("/")
        except Exception:
            origin = ""
        if not origin:
            origin = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("web.base.url", "")
                .rstrip("/")
            )
        if not path.startswith("/"):
            path = "/" + path
        return origin + path

    def action_cda_open_docs(self):
        return {
            "type": "ir.actions.act_url",
            "url": self._cda_docs_url(),
            "target": "new",
        }
