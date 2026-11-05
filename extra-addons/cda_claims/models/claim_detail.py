from odoo import fields, models

EXTRA_KINDS = [
    ("none", "Ninguno"),
    ("equipment", "¿Se usa equipo?"),
    ("crane", "¿Con o sin grúa?"),
]


class CdaClaimDetail(models.Model):
    _name = "cda.claim.detail"
    _description = "Detalle de reclamo"
    _order = "type_id, subtype_id, sequence, id"
    _rec_names_search = ["code", "name"]

    _code_uniq = models.Constraint(
        "UNIQUE (subtype_id, code)",
        "El código del detalle debe ser único dentro del subtipo.",
    )

    subtype_id = fields.Many2one(
        "cda.claim.subtype",
        string="Subtipo",
        required=True,
        ondelete="cascade",
        index=True,
    )
    type_id = fields.Many2one(
        related="subtype_id.type_id",
        store=True,
        index=True,
        string="Tipo de reclamo",
    )
    code = fields.Char(string="Código", required=True, copy=False)
    name = fields.Char(string="Nombre", required=True)
    extra = fields.Selection(
        EXTRA_KINDS,
        string="Pregunta adicional",
        default="none",
        help="Si el detalle necesita un dato extra al cargar el reclamo.",
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)