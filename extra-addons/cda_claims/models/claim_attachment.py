import mimetypes

from odoo import api, fields, models
from odoo.exceptions import ValidationError

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_MIME_PREFIXES = ("image/", "video/", "audio/", "text/")

ATTACHMENT_KINDS = [
    ("image", "Imagen"),
    ("video", "Video"),
    ("audio", "Audio"),
    ("text", "Texto"),
    ("other", "Archivo"),
]


def _kind_from_name(value):
    mime = mimetypes.guess_type(value or "")[0] or ""
    if mime.startswith("image/"):
        return "image"
    if mime.startswith("video/"):
        return "video"
    if mime.startswith("audio/"):
        return "audio"
    if mime.startswith("text/"):
        return "text"
    return "other"


class CdaClaimAttachment(models.Model):
    _name = "cda.claim.attachment"
    _description = "Adjunto del reclamo"
    _order = "id desc"
    _rec_name = "name"

    _url_uniq = models.Constraint(
        "UNIQUE (claim_id, url)",
        "Esa URL ya está adjunta al reclamo.",
    )

    claim_id = fields.Many2one(
        "cda.claim",
        string="Reclamo",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        related="claim_id.company_id",
        store=True,
        index=True,
    )
    name = fields.Char(string="Descripción")
    kind = fields.Selection(
        ATTACHMENT_KINDS,
        string="Tipo",
        compute="_compute_kind",
    )
    note = fields.Text(string="Texto")
    url = fields.Char(string="URL")
    file = fields.Binary(string="Archivo", attachment=True)
    file_name = fields.Char(string="Nombre de archivo")
    file_size = fields.Integer(string="Tamaño (bytes)", readonly=True)
    image_preview = fields.Binary(
        string="Vista previa",
        compute="_compute_image_preview",
    )
    open_url = fields.Char(string="Ver", compute="_compute_open_url")

    @api.depends("file", "file_name", "url", "note")
    def _compute_image_preview(self):
        for attachment in self:
            if attachment.kind == "image" and attachment.file:
                attachment.image_preview = attachment.file
            else:
                attachment.image_preview = False

    @api.depends("file_name", "url")
    def _compute_open_url(self):
        for attachment in self:
            if attachment.url:
                attachment.open_url = attachment.url
            elif attachment.file_name:
                attachment.open_url = (
                    "/web/content/cda.claim.attachment/%s/file/%s?download=false"
                    % (attachment.id, attachment.file_name)
                )
            else:
                attachment.open_url = False

    def action_preview(self):
        self.ensure_one()
        if not self.open_url:
            raise ValidationError("Ese adjunto no tiene archivo ni URL.")
        return {
            "type": "ir.actions.act_url",
            "url": self.open_url,
            "target": "new",
        }

    @api.depends("file_name", "url", "note")
    def _compute_kind(self):
        for attachment in self:
            if attachment.file_name or attachment.url:
                attachment.kind = _kind_from_name(
                    attachment.file_name or attachment.url
                )
            else:
                attachment.kind = "text"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("file"):
                vals["file_size"] = len(vals["file"]) * 3 // 4
        return super().create(vals_list)

    def write(self, vals):
        if "file" in vals:
            vals["file_size"] = len(vals["file"] or "") * 3 // 4
        return super().write(vals)

    @api.constrains("file_size")
    def _check_file_size(self):
        for attachment in self:
            if attachment.file_size > MAX_FILE_SIZE:
                raise ValidationError(
                    "El archivo supera el máximo de 10 MB."
                )

    @api.constrains("file_name")
    def _check_file_name(self):
        for attachment in self:
            mime = mimetypes.guess_type(attachment.file_name or "")[0]
            if mime and not mime.startswith(ALLOWED_MIME_PREFIXES):
                raise ValidationError(
                    "Solo se permiten imágenes, videos, audios o archivos de texto."
                )
