from odoo import fields, models


class CdaClaimStage(models.Model):
    _name = "cda.claim.stage"
    _description = "Etapa del reclamo"
    _order = "sequence, id"

    name = fields.Char(string="Etapa", required=True, translate=True)
    sequence = fields.Integer(default=1)
    unattended = fields.Boolean(string="Sin atender")
    closed = fields.Boolean(string="Cierra el reclamo")
    fold = fields.Boolean(string="Plegada en kanban")
    active = fields.Boolean(default=True)
