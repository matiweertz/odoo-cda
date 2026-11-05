from odoo import fields, models


class CdaClaimCraneType(models.Model):
    _name = "cda.claim.crane.type"
    _description = "Tipo de grúa"
    _order = "sequence, id"

    name = fields.Char(string="Nombre", required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
