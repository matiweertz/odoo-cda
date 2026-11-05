from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import html2plaintext


class CdaClaimMergeWizard(models.TransientModel):
    _name = "cda.claim.merge.wizard"
    _description = "Combinar reclamos"

    claim_ids = fields.Many2many(
        "cda.claim",
        string="Reclamos a combinar",
        required=True,
    )
    target_claim_id = fields.Many2one(
        "cda.claim",
        string="Reclamo principal",
        required=True,
        options={"no_create": True},
    )
    merge_attachments = fields.Boolean(
        string="Trasladar adjuntos al principal",
        default=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        ids = self.env.context.get("active_ids") or []
        if self.env.context.get("active_model") == "cda.claim" and ids:
            res["claim_ids"] = [(6, 0, ids)]
            res["target_claim_id"] = ids[0]
        return res

    @api.constrains("claim_ids", "target_claim_id")
    def _check_selection(self):
        for wizard in self:
            if len(wizard.claim_ids) < 2:
                raise ValidationError("Seleccioná al menos dos reclamos.")
            if wizard.target_claim_id not in wizard.claim_ids:
                raise ValidationError(
                    "El reclamo principal tiene que ser uno de los seleccionados."
                )
            if len(wizard.claim_ids.company_id) > 1:
                raise ValidationError(
                    "Todos los reclamos tienen que ser de la misma empresa."
                )

    def _plain(self, value):
        value = (value or "").strip()
        if "<" in value:
            value = html2plaintext(value).strip()
        return value

    def action_merge(self):
        self.ensure_one()
        target = self.target_claim_id
        others = self.claim_ids - target
        fill = {}
        extra_descriptions = []
        for other in others:
            for campo in ("phone", "email", "address"):
                if not fill.get(campo) and not target[campo] and other[campo]:
                    fill[campo] = other[campo]
            texto = self._plain(other.description)
            if texto:
                extra_descriptions.append("[%s] %s" % (other.number, texto))
            if self.merge_attachments:
                self._move_attachments(other, target)
            other.write({"merged_into_id": target.id, "active": False})
        vals = dict(fill)
        if extra_descriptions:
            propio = self._plain(target.description)
            partes = [propio] if propio else []
            vals["description"] = "\n\n".join(partes + extra_descriptions)
        if vals:
            target.write(vals)
        target.message_post(
            body="Reclamos combinados: %s" % ", ".join(others.mapped("number"))
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "cda.claim",
            "res_id": target.id,
            "view_mode": "form",
            "target": "current",
        }

    def _move_attachments(self, origin, target):
        urls = set(url for url in target.attachment_ids.mapped("url") if url)
        for attachment in origin.attachment_ids:
            if attachment.url and attachment.url in urls:
                attachment.unlink()
                continue
            attachment.claim_id = target.id
            if attachment.url:
                urls.add(attachment.url)
