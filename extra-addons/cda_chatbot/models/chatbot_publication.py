import json
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class CdaChatbotPublication(models.Model):
    """Foto inmutable del árbol.

    Editar los nodos no cambia lo que ve el usuario hasta que se publica.
    `payload` es el JSON que consume el sitio; se guarda como Text y no como
    Json para que el viaje por XML-RPC no convierta None en False.

    El campo se llama `is_current` y no `active` a propósito: en Odoo un campo
    llamado `active` es el de archivado, y las versiones viejas desaparecerían
    de la lista.
    """

    _name = "cda.chatbot.publication"
    _description = "Publicación del árbol del chatbot"
    _order = "version desc"

    _version_uniq = models.Constraint(
        "UNIQUE (version)",
        "La versión de publicación debe ser única.",
    )

    version = fields.Integer(required=True, readonly=True, default=1)
    published_on = fields.Datetime(
        string="Publicado el",
        default=fields.Datetime.now,
        readonly=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Publicado por",
        default=lambda self: self.env.user,
        readonly=True,
    )
    note = fields.Char(string="Nota de la versión")
    is_current = fields.Boolean(
        string="En línea",
        readonly=True,
        help="La versión que consume el sitio. Solo una a la vez.",
    )
    node_count = fields.Integer(string="Nodos", readonly=True)
    payload = fields.Text(
        readonly=True,
        help="Árbol compilado a JSON.",
    )

    # ------------------------------------------------------------------ ORM
    @api.model
    def _active_publication(self):
        return self.search([("is_current", "=", True)], limit=1)

    @api.model
    def _publish(self, note=None):
        """Valida, compila y guarda una versión nueva.

        No pisa la anterior: quedan todas y solo una en línea. Volver atrás es
        poner en línea una publicación vieja.
        """
        Node = self.env["cda.chatbot.node"]

        # Las constraints corren al editar, pero un import o un script puede
        # dejar el árbol roto, así que se revisa entero antes de publicar.
        Node._check_tree()

        last = self.search([], order="version desc", limit=1)
        version = (last.version or 0) + 1

        data = Node._compile(version=version)
        payload = json.dumps(data, ensure_ascii=False, sort_keys=True)

        self.search([("is_current", "=", True)]).write({"is_current": False})
        publication = self.create(
            {
                "version": version,
                "note": note or "",
                "is_current": True,
                "node_count": Node._count_nodes(data["root"]),
                "payload": payload,
            }
        )
        _logger.info(
            "Chatbot: publicada la versión %s con %s nodos (%s bytes)",
            version,
            publication.node_count,
            len(payload),
        )
        return publication

    def action_activate(self):
        """Vuelve a poner en línea una versión anterior."""
        for publication in self:
            self.search([("is_current", "=", True)]).write({"is_current": False})
            publication.write({"is_current": True})
