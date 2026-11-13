from odoo import fields, models


class CdaClaim(models.Model):
    """Trazabilidad del chat en el reclamo.

    Los reclamos del chatbot no tienen bandeja propia: son cda.claim con el
    medio de entrada BOT. Acá solo se agrega lo que el chat sabe y el reclamo
    tradicional no.
    """

    _inherit = "cda.claim"

    chat_session = fields.Char(
        string="Sesión del chat",
        index=True,
        copy=False,
        help="Identifica la conversación de la que salió el reclamo.",
    )
    chat_node_id = fields.Many2one(
        "cda.chatbot.node",
        string="Se rindió en",
        ondelete="set null",
        index=True,
        copy=False,
        help="Nodo del árbol donde el usuario abandonó. Es el dato que dice "
             "qué le falta al grafo.",
    )
    chat_path = fields.Text(
        string="Camino en el chat",
        copy=False,
        help="Secuencia de nodos por los que pasó, ej: Inicio > Tarifas > Riccheri",
    )
    chat_transcript = fields.Text(
        string="Conversación",
        copy=False,
        help="Lo que se habló en el chat, en texto legible.",
    )
    chat_origin = fields.Char(
        string="Página de origen",
        copy=False,
        help="URL desde donde se abrió el chat.",
    )
