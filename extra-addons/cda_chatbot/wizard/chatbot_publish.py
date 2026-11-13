from odoo import api, fields, models, _


class CdaChatbotPublish(models.TransientModel):
    """Confirmación de publicación, con nota de versión."""

    _name = "cda.chatbot.publish"
    _description = "Publicar el árbol del chatbot"

    note = fields.Char(
        string="Nota de la versión",
        help="Qué cambió. Queda guardada junto a la publicación.",
    )
    summary = fields.Char(compute="_compute_summary", string="A publicar")

    @api.depends("note")
    def _compute_summary(self):
        Node = self.env["cda.chatbot.node"]
        total = Node.search_count([])
        active = Node.search_count([("active", "=", True)])
        root = Node._root()
        for wizard in self:
            wizard.summary = _(
                "%(total)s nodos cargados, %(active)s activos. Raíz: %(root)s",
                total=total,
                active=active,
                root=root.name if root else _("— sin raíz —"),
            )

    @api.model
    def _open(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Publicar árbol"),
            "res_model": "cda.chatbot.publish",
            "view_mode": "form",
            "target": "new",
        }

    def action_publish(self):
        self.ensure_one()
        publication = self.env["cda.chatbot.publication"]._publish(note=self.note)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Árbol publicado"),
                "message": _(
                    "Versión %(version)s con %(nodes)s nodos.",
                    version=publication.version,
                    nodes=publication.node_count,
                ),
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
