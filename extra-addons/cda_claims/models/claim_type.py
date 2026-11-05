from odoo import fields, models


class CdaClaimType(models.Model):
    _name = "cda.claim.type"
    _description = "Tipo de reclamo"
    _order = "sequence, id"
    _rec_names_search = ["code", "name"]

    _code_uniq = models.Constraint(
        "UNIQUE (code)",
        "El código del tipo de reclamo debe ser único.",
    )

    code = fields.Char(string="Código", required=True, index=True, copy=False)
    name = fields.Char(string="Nombre", required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
