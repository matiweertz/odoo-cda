from odoo import fields, models
from odoo.exceptions import ValidationError
from odoo.http import request


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cda_api_require_auth = fields.Boolean(
        string="Requerir API key",
        config_parameter="cda_api.require_auth",
        help="Si está desactivado, la API acepta llamadas sin "
        "Authorization y trabaja con el usuario de servicio.",
    )
    cda_api_service_user_id = fields.Many2one(
        "res.users",
        string="Usuario de servicio",
        config_parameter="cda_api.service_user_id",
        help="Usuario con el que corre la API cuando no se exige API key. "
        "Define el techo de permisos.",
    )
    cda_api_docs_path = fields.Char(
        string="Ruta de documentación",
        config_parameter="cda_api.docs_path",
        default="/api/v1/docs",
    )

    def _cda_persist(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param(
            "cda_api.require_auth",
            "True" if self.cda_api_require_auth else "False",
        )
        params.set_param(
            "cda_api.service_user_id",
            self.cda_api_service_user_id.id or 0,
        )
        params.set_param(
            "cda_api.docs_path",
            (self.cda_api_docs_path or "").strip(),
        )

    def write(self, vals):
        res = super().write(vals)
        if {
            "cda_api_require_auth",
            "cda_api_service_user_id",
            "cda_api_docs_path",
        } & set(vals):
            for record in self:
                record._cda_persist()
        return res

    def _cda_docs_url(self):
        self.ensure_one()
        path = (self.cda_api_docs_path or "").strip()
        if not path:
            raise ValidationError("Configurá la ruta de documentación.")
        if path.startswith("http://") or path.startswith("https://"):
            return path
        try:
            origin = request.httprequest.host_url.rstrip("/")
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
