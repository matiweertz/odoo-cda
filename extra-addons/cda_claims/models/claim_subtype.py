from odoo import fields, models


class CdaClaimSubtype(models.Model):
    _name = "cda.claim.subtype"
    _description = "Subtipo de reclamo"
    _order = "type_id, sequence, id"
    _rec_names_search = ["code", "name"]

    _code_uniq = models.Constraint(
        "UNIQUE (type_id, code)",
        "El código del subtipo debe ser único dentro del tipo.",
    )

    type_id = fields.Many2one(
        "cda.claim.type",
        string="Tipo de reclamo",
        required=True,
        ondelete="cascade",
        index=True,
    )
    code = fields.Char(string="Código", required=True, copy=False)
    name = fields.Char(string="Nombre", required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    detail_ids = fields.One2many(
        "cda.claim.detail",
        "subtype_id",
        string="Detalles",
    )
    detail_count = fields.Integer(compute="_compute_detail_count")

    def _compute_detail_count(self):
        for subtype in self:
            subtype.detail_count = len(subtype.detail_ids)