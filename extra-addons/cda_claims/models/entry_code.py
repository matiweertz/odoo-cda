from odoo import api, fields, models

ENTRY_CODE_CATEGORIES = [
    ("users_public", "Usuarios y público"),
    ("own_staff", "Personal propio"),
    ("formal", "Formales y seguimiento"),
]


class CdaClaimEntryCode(models.Model):
    _name = "cda.claim.entry.code"
    _description = "Medio de entrada"
    _order = "sequence, code"
    _rec_names_search = ["code", "name"]

    _code_uniq = models.Constraint(
        "UNIQUE (code)",
        "El código del medio de entrada debe ser único.",
    )

    code = fields.Char(string="Código", required=True, index=True, copy=False)
    name = fields.Char(string="Descripción", required=True, translate=True)
    category = fields.Selection(
        ENTRY_CODE_CATEGORIES,
        string="Categoría",
        required=True,
        default="users_public",
        index=True,
    )
    is_automated = fields.Boolean(string="Carga automática")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    @api.depends("code", "name")
    def _compute_display_name(self):
        for entry in self:
            if entry.code:
                entry.display_name = f"{entry.code} - {entry.name}"
            else:
                entry.display_name = entry.name
