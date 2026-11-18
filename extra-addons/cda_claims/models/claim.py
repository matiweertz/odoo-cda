import logging

from markupsafe import escape

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


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
    web_form_url = fields.Char(
        string="Link del formulario web",
        compute="_compute_web_form_url",
        help="Enlace a la planilla pública de denuncia para este reclamo.",
    )
    tipo_lesion = fields.Selection(
        [
            ("grave", "Grave"),
            ("leve", "Leve"),
            ("fallecido", "Fallecido"),
        ],
        string="Tipo de lesión",
    )
    cantidad_lesionados = fields.Integer(string="Cantidad de lesionados")
    hay_lesionados = fields.Boolean(
        compute="_compute_hay_lesionados",
        store=True,
        string="Hay lesionados",
        help="Se activa cuando el detalle es Personas lesionadas o Ambos.",
    )
    tipo_accidente = fields.Selection(
        [
            ("vuelco", "Vuelco"),
            ("animal", "Con animal"),
            ("frontal", "Colisión frontal"),
            ("salida_via", "Salida de vía"),
            ("alcance", "Colisión por alcance"),
            ("diagonal", "Colisión diagonal"),
            ("otros", "Otros"),
        ],
        string="Tipo de accidente",
        help="Aplica a los reclamos de Siniestros / Accidente.",
    )
    es_accidente = fields.Boolean(
        compute="_compute_es_accidente",
        store=True,
        string="Es accidente",
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

    @api.depends("detail_id.code")
    def _compute_hay_lesionados(self):
        for claim in self:
            claim.hay_lesionados = (claim.detail_id.code or "") in ("CL", "AM")
    def _claimant_link(self):
        """Enlace al formulario largo, solo para estado de ruta y daños."""
        self.ensure_one()
        if (self.subtype_id.code or "") not in ("ER", "DA"):
            return False
        base = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("cda_claims.web_form_base")
            or "https://www.caminosdelaconcagua.com.ar"
        ).rstrip("/")
        return f"{base}/reclamo/{self.id}"

    def _claimant_email_html(self, saludo, numero, enlace=None):
        partes = [
            '<div style="font-family:Arial,Helvetica,sans-serif;color:#273F4F;max-width:560px">',
            f'<p style="font-size:15px;margin:0 0 14px">{escape(saludo)}</p>',
            '<p style="font-size:15px;line-height:1.6;margin:0 0 14px">'
            "Registramos tu reclamo con el número "
            f'<strong style="font-size:17px;letter-spacing:.03em">{escape(numero)}</strong>.'
            "</p>",
        ]
        if enlace:
            partes += [
                '<p style="font-size:15px;line-height:1.6;margin:0 0 18px">'
                "Podés terminar de completar la denuncia con los datos del hecho, los "
                "daños y las fotos en el siguiente enlace:"
                "</p>",
                '<p style="margin:0 0 18px">'
                f'<a href="{escape(enlace)}" style="background:#273F4F;color:#FFFFFF;'
                "text-decoration:none;padding:12px 20px;border-radius:8px;font-size:15px;"
                'font-weight:600;display:inline-block">Completar la denuncia</a>'
                "</p>",
                '<p style="font-size:13px;color:#537188;line-height:1.6;margin:0 0 6px">'
                f"Si el botón no funciona, copiá este enlace: {escape(enlace)}"
                "</p>",
            ]
        partes += [
            '<p style="font-size:13px;color:#537188;line-height:1.6;margin:0">'
            "Si preferís, respondé este correo o comunicate al 0-800-999-5555."
            "</p>",
            "</div>",
        ]
        return "".join(partes)

    def _mail_servidor_listo(self):
        return bool(self.env["ir.mail_server"].sudo().search_count([]))

    def _remitente_avisos(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("cda_claims.email_from")
            or "atencionalusuario@caminosdelaconcagua.com.ar"
        )

    def _saludo_denunciante(self):
        nombre = (self.den_nombre or "").strip()
        return f"Hola {nombre}:" if nombre else "Hola:"

    def _send_claimant_email(self, force=False):
        """Avisa al vecino que su reclamo existe.

        Devuelve True solo si Odoo se hizo cargo del envío. Si no hay servidor de
        correo, o el reclamo no tiene email, devuelve False para que el sitio lo
        mande: así nunca se pierde el aviso.

        Con force=True se ignora el interruptor: lo usa el botón de reenvío, que
        es una acción explícita de una persona.
        """
        self.ensure_one()
        if not self.email:
            return False

        parametros = self.env["ir.config_parameter"].sudo()
        if not force:
            # El servidor de producción está configurado pero la conexión SMTP no
            # responde: Odoo espera 60 s y eso corta el alta. Mientras no se
            # arregle, el aviso lo manda el sitio.
            interruptor = (
                parametros.get_param("cda_claims.email_from_odoo") or ""
            ).strip().lower()
            if interruptor not in ("1", "true", "yes", "t"):
                return False

        if not self._mail_servidor_listo():
            return False

        numero = self.number or f"#{self.id}"
        html = self._claimant_email_html(
            self._saludo_denunciante(), numero, self._claimant_link()
        )
        correo = (
            self.env["mail.mail"]
            .sudo()
            .create(
                {
                    "subject": f"Reclamo {numero} — Caminos del Aconcagua",
                    "email_to": self.email,
                    "email_from": f"Caminos del Aconcagua <{self._remitente_avisos()}>",
                    "body_html": html,
                    "model": self._name,
                    "res_id": self.id,
                    "auto_delete": True,
                }
            )
        )
        try:
            correo.send()
        except Exception:  # noqa: BLE001 - si falla, el sitio manda el suyo
            _logger.exception("No se pudo enviar el aviso del reclamo %s", numero)
            return False
        if correo.state == "exception":
            _logger.warning(
                "El servidor de correo rechazó el aviso del reclamo %s", numero
            )
            return False
        return True

    def action_resend_claimant_email(self):
        """Botón de Seguimiento: reenvía el aviso al vecino."""
        self.ensure_one()
        if not self.email:
            raise UserError(
                "El reclamo no tiene email cargado. Agregalo antes de reenviar."
            )
        if not self._mail_servidor_listo():
            raise UserError(
                "No hay ningún servidor de correo saliente configurado en Odoo."
            )
        enviado = self._send_claimant_email(force=True)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success" if enviado else "warning",
                "title": "Aviso reenviado" if enviado else "No se pudo enviar",
                "message": (
                    f"Se reenvió el aviso a {self.email}."
                    if enviado
                    else "El servidor de correo rechazó el envío. Revisá la "
                    "configuración en Ajustes → Servidores de correo saliente."
                ),
                "sticky": False,
            },
        }

    def _queue_number_changed_email(self, anterior, nuevo):
        """Avisa al vecino que el número de su reclamo cambió.

        Se deja en la cola de correo (sin enviar en el momento) para no bloquear
        el guardado si el servidor SMTP está lento: lo manda el cron de la cola.
        """
        self.ensure_one()
        if not self.email or not self._mail_servidor_listo():
            return
        html = (
            '<div style="font-family:Arial,Helvetica,sans-serif;color:#273F4F;max-width:560px">'
            f'<p style="font-size:15px;margin:0 0 14px">{escape(self._saludo_denunciante())}</p>'
            '<p style="font-size:15px;line-height:1.6;margin:0 0 14px">'
            "El número de tu reclamo cambió."
            "</p>"
            '<p style="font-size:15px;line-height:1.6;margin:0 0 14px">'
            f'Antes: <strong>{escape(anterior or "-")}</strong><br>'
            'Ahora: <strong style="font-size:17px;letter-spacing:.03em">'
            f"{escape(nuevo)}</strong>"
            "</p>"
            '<p style="font-size:13px;color:#537188;line-height:1.6;margin:0">'
            "Guardá el número nuevo: es el que vas a necesitar para cualquier consulta."
            "</p>"
            "</div>"
        )
        self.env["mail.mail"].sudo().create(
            {
                "subject": f"Tu reclamo cambió de número: {nuevo}",
                "email_to": self.email,
                "email_from": f"Caminos del Aconcagua <{self._remitente_avisos()}>",
                "body_html": html,
                "model": self._name,
                "res_id": self.id,
                "auto_delete": True,
            }
        )
        self.message_post(
            body=f"Se avisó al vecino el cambio de número: {anterior or '-'} → {nuevo}"
        )

    @api.depends()
    def _compute_web_form_url(self):
        base = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("cda_claims.web_form_base")
            or "https://www.caminosdelaconcagua.com.ar"
        ).rstrip("/")
        for claim in self:
            registro = claim._origin.id
            claim.web_form_url = f"{base}/reclamo/{registro}" if registro else False
    @api.depends("subtype_id.code")
    def _compute_es_accidente(self):
        for claim in self:
            claim.es_accidente = (claim.subtype_id.code or "") == "AC"
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
                anterior = claim.number
                numero = claim._build_number()
                if numero and numero != anterior:
                    claim.number = numero
                    # El número figura en la constancia del vecino: se le avisa.
                    claim._queue_number_changed_email(anterior, numero)
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
