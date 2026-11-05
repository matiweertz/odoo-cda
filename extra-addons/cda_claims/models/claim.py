from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CdaClaim(models.Model):
    _name = "cda.claim"
    _description = "Reclamo"
    _rec_name = "number"
    _rec_names_search = ["number", "name"]
    _order = "id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    _number_uniq = models.Constraint(
        "UNIQUE (number)",
        "Ya existe un reclamo con ese número.",
    )
    _external_ref_uniq = models.Constraint(
        "UNIQUE (external_ref)",
        "Ya existe un reclamo con esa referencia externa.",
    )

    number = fields.Char(
        string="Número",
        readonly=True,
        copy=False,
        index=True,
        default="/",
    )
    name = fields.Char(string="Asunto")
    description = fields.Text(string="Descripción", required=True)
    entry_code_id = fields.Many2one(
        "cda.claim.entry.code",
        string="Medio de entrada",
        required=True,
        tracking=True,
        ondelete="restrict",
        index=True,
    )
    claim_type_id = fields.Many2one(
        "cda.claim.type",
        string="Tipo de reclamo",
        required=True,
        tracking=True,
        ondelete="restrict",
        index=True,
    )
    subtype_id = fields.Many2one(
        "cda.claim.subtype",
        string="Subtipo",
        domain="[('type_id', '=', claim_type_id)]",
        required=True,
        tracking=True,
        ondelete="restrict",
        index=True,
    )
    detail_available = fields.Boolean(
        compute="_compute_detail_available",
        store=True,
    )
    detail_id = fields.Many2one(
        "cda.claim.detail",
        string="Detalle",
        domain="[('subtype_id', '=', subtype_id)]",
        tracking=True,
        ondelete="restrict",
        index=True,
    )
    extra_kind = fields.Selection(
        [
            ("none", "Ninguno"),
            ("equipment", "¿Se usa equipo?"),
            ("crane", "¿Con o sin grúa?"),
        ],
        compute="_compute_extra_kind",
        store=True,
    )
    extra_question = fields.Char(compute="_compute_extra_question")
    extra_choice = fields.Selection(
        [("yes", "Sí"), ("no", "No")],
        string="Respuesta",
    )
    equipment_detail = fields.Char(string="Detalle del equipo")
    crane_plate = fields.Char(string="Patente de la grúa")
    crane_type_id = fields.Many2one(
        "cda.claim.crane.type",
        string="Tipo de grúa",
    )
    crane_date = fields.Date(
        string="Fecha de la grúa",
        default=fields.Date.context_today,
    )
    crane_time_in = fields.Char(string="Hora de entrada")
    crane_time_out = fields.Char(string="Hora de salida")
    claim_date = fields.Date(
        string="Fecha",
        required=True,
        default=fields.Date.context_today,
    )
    phone = fields.Char(string="Teléfono")
    email = fields.Char(string="Correo electrónico")
    address = fields.Char(string="Dirección")
    stage_id = fields.Many2one(
        "cda.claim.stage",
        string="Estado",
        default=lambda self: self._default_stage_id(),
        tracking=True,
        group_expand="_read_group_stage_ids",
        ondelete="restrict",
        index=True,
        copy=False,
    )
    closed = fields.Boolean(
        related="stage_id.closed",
        store=True,
        string="Cerrado",
    )
    unattended = fields.Boolean(
        related="stage_id.unattended",
        store=True,
        string="Sin atender",
    )
    user_id = fields.Many2one(
        "res.users",
        string="Asignado a",
        tracking=True,
        index=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    external_ref = fields.Char(
        string="Referencia externa",
        index=True,
        copy=False,
    )
    attachment_ids = fields.One2many(
        "cda.claim.attachment",
        "claim_id",
        string="Adjuntos",
    )
    active = fields.Boolean(default=True)
    merged_into_id = fields.Many2one(
        "cda.claim",
        string="Combinado en",
        readonly=True,
        copy=False,
        index=True,
    )
    merged_ids = fields.One2many(
        "cda.claim",
        "merged_into_id",
        string="Reclamos combinados",
    )
    entry_code = fields.Char(
        related="entry_code_id.code",
        string="Código del medio de entrada",
    )

    @api.model
    def _default_stage_id(self):
        return self.env["cda.claim.stage"].search(
            [("closed", "=", False)], order="sequence, id", limit=1
        )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if "user_id" in fields_list and not res.get("user_id"):
            res["user_id"] = self.env.uid
        return res

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        return self.env["cda.claim.stage"].search([])

    @api.depends("number", "name")
    def _compute_display_name(self):
        for claim in self:
            claim.display_name = claim.number or claim.name or ""

    @api.depends("subtype_id")
    def _compute_detail_available(self):
        for claim in self:
            claim.detail_available = bool(claim.subtype_id.detail_ids)

    @api.depends("detail_id")
    def _compute_extra_kind(self):
        for claim in self:
            claim.extra_kind = claim.detail_id.extra or "none"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("number") or vals["number"] == "/":
                vals["number"] = self._next_number(vals)
        return super().create(vals_list)

    def _next_number(self, vals):
        sequence = self.env["ir.sequence"]
        if vals.get("company_id"):
            sequence = sequence.with_company(vals["company_id"])
        digits = (sequence.next_by_code("cda.claim.sequence") or "0").strip()
        entry_code = self.env["cda.claim.entry.code"].browse(
            vals.get("entry_code_id")
        )
        claim_type = self.env["cda.claim.type"].browse(vals.get("claim_type_id"))
        subtype = self.env["cda.claim.subtype"].browse(vals.get("subtype_id"))
        medio = entry_code.code or "GEN"
        tipo = claim_type.code or "GEN"
        subtipo = subtype.code or "GEN"
        return "%s-%s-%s-%s" % (medio, tipo, subtipo, digits.zfill(5))

    def _build_number(self):
        self.ensure_one()
        partes = (self.number or "").split("-")
        if len(partes) < 4:
            return self.number
        return "%s-%s-%s-%s" % (
            self.entry_code_id.code or "GEN",
            self.claim_type_id.code or "GEN",
            self.subtype_id.code or "GEN",
            partes[-1],
        )

    @api.depends("detail_id")
    def _compute_extra_question(self):
        for claim in self:
            extra = claim.detail_id.extra
            if extra == "equipment":
                claim.extra_question = "¿Se usa equipo?"
            elif extra == "crane":
                claim.extra_question = "¿Con o sin grúa?"
            else:
                claim.extra_question = False

    def _reset_extras(self):
        self.extra_choice = False
        self.equipment_detail = False
        self.crane_plate = False
        self.crane_type_id = False
        self.crane_date = False
        self.crane_time_in = False
        self.crane_time_out = False

    @api.onchange("claim_type_id")
    def _onchange_claim_type_id(self):
        if self.subtype_id.type_id != self.claim_type_id:
            self.subtype_id = False
        if self.detail_id.subtype_id != self.subtype_id:
            self.detail_id = False
        self._reset_extras()

    @api.onchange("subtype_id")
    def _onchange_subtype_id(self):
        if self.detail_id.subtype_id != self.subtype_id:
            self.detail_id = False
        self._reset_extras()

    @api.onchange("detail_id")
    def _onchange_detail_id(self):
        self._reset_extras()

    def write(self, vals):
        if "claim_type_id" in vals and "subtype_id" not in vals:
            claim_type = self.env["cda.claim.type"].browse(vals["claim_type_id"])
            for claim in self:
                if claim.subtype_id and claim.subtype_id.type_id != claim_type:
                    raise ValidationError(
                        "El subtipo actual no corresponde al nuevo tipo de "
                        "reclamo. Elegí un subtipo."
                    )
        if "subtype_id" in vals and "detail_id" not in vals:
            subtype = self.env["cda.claim.subtype"].browse(vals["subtype_id"])
            for claim in self:
                if claim.detail_id and claim.detail_id.subtype_id != subtype:
                    vals = dict(vals, detail_id=False)
                    break
        res = super().write(vals)
        if "detail_id" in vals and not vals["detail_id"]:
            for claim in self:
                claim._reset_extras()
        if {"claim_type_id", "subtype_id"} & set(vals):
            for claim in self:
                if claim.detail_id and claim.detail_id.subtype_id != claim.subtype_id:
                    claim.detail_id = False
                    claim._reset_extras()
        if {"entry_code_id", "claim_type_id", "subtype_id"} & set(vals):
            for claim in self:
                numero = claim._build_number()
                if numero and numero != claim.number:
                    claim.number = numero
        return res

    def action_claim_start(self):
        stage = self.env.ref("cda_claims.claim_stage_in_progress")
        self.write({"stage_id": stage.id})

    def action_claim_lawyers(self):
        stage = self.env.ref("cda_claims.claim_stage_lawyers")
        self.write({"stage_id": stage.id})

    def action_claim_close(self):
        stage = self.env.ref("cda_claims.claim_stage_closed")
        self.write({"stage_id": stage.id})
