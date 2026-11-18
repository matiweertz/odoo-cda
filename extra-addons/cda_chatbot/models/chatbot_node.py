from odoo import api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.cda_api.models.claim_api import ClaimApiError

ENTRY_CODE = "BOT"
MAX_TRANSCRIPT = 20000


def _text(value, limit=None):
    """Normaliza lo que llega del widget: sin espacios, vacío a False."""
    if value is None:
        return False
    text = str(value).strip()
    if not text:
        return False
    return text[:limit] if limit else text


class CdaChatbotNode(models.Model):
    """Un nodo del grafo. Cada nodo *es* una opción dentro de su padre:
    `name` es el texto del botón, `message` lo que dice el bot al entrar y
    `child_ids` las opciones que ofrece. El árbol sale de ahí."""

    _name = "cda.chatbot.node"
    _description = "Nodo del árbol del chatbot"
    _order = "parent_id, sequence, id"
    _parent_store = True
    _parent_name = "parent_id"
    _rec_name = "name"
    _rec_names_search = ["code", "name"]

    _code_uniq = models.Constraint(
        "UNIQUE (code)",
        "El código del nodo debe ser único.",
    )

    # -- identidad ---------------------------------------------------------
    code = fields.Char(
        string="Código",
        required=True,
        index=True,
        copy=False,
        help="Identificador estable que viaja al widget. Ej: tarifas.riccheri",
    )
    name = fields.Char(
        string="Etiqueta",
        required=True,
        help="Texto del botón dentro del nodo padre.",
    )
    parent_id = fields.Many2one(
        "cda.chatbot.node",
        string="Padre",
        ondelete="cascade",
        index=True,
    )
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many(
        "cda.chatbot.node",
        "parent_id",
        string="Opciones",
    )
    sequence = fields.Integer(default=10, string="Orden")
    is_root = fields.Boolean(
        compute="_compute_is_root",
        store=True,
        string="Es la raíz",
    )
    path_label = fields.Char(
        compute="_compute_path_label",
        recursive=True,
        string="Ruta",
        help="Camino desde la raíz, para ubicarse de un vistazo.",
    )

    # -- comportamiento ----------------------------------------------------
    kind = fields.Selection(
        [
            ("menu", "Menú de opciones"),
            ("message", "Mensaje"),
            ("link", "Abrir un link"),
            ("phone", "Llamar por teléfono"),
            ("whatsapp", "Ir a WhatsApp"),
            ("claim", "Pedir un reclamo"),
        ],
        string="Tipo",
        required=True,
        default="message",
        help="Menú: muestra sus opciones. Mensaje: solo habla. "
             "Link, teléfono y WhatsApp: acciones. Reclamo: pide los datos.",
    )
    message = fields.Text(
        string="Mensaje",
        help="Lo que dice el bot al entrar a este nodo.",
    )
    allow_back = fields.Boolean(
        string='Mostrar "volver al menú"',
        default=True,
        help="Si el widget ofrece volver al menú principal desde este nodo.",
    )

    # -- acciones ----------------------------------------------------------
    url = fields.Char(string="URL", help="Solo para tipo Link.")
    phone = fields.Char(string="Teléfono", help="Solo para tipos Teléfono y WhatsApp.")
    whatsapp_message = fields.Char(
        string="Mensaje precargado",
        help="Texto que se precarga en el mensaje de WhatsApp. "
             "Admite {numero} para insertar el número de reclamo.",
    )

    # -- taxonomía del reclamo --------------------------------------------
    claim_type_id = fields.Many2one(
        "cda.claim.type",
        string="Tipo de reclamo",
        ondelete="restrict",
        help="Con qué tipo de reclamo entra al sistema lo que se cargue acá.",
    )
    subtype_id = fields.Many2one(
        "cda.claim.subtype",
        string="Subtipo",
        domain="[('type_id', '=', claim_type_id)]",
        ondelete="restrict",
    )
    detail_id = fields.Many2one(
        "cda.claim.detail",
        string="Detalle",
        domain="[('subtype_id', '=', subtype_id)]",
        ondelete="restrict",
    )

    active = fields.Boolean(default=True)

    # ------------------------------------------------------------------ ORM
    @api.model_create_multi
    def create(self, vals_list):
        # La unicidad de raíz no se puede dejar solo a un @api.constrains:
        # al crear sin `parent_id`, ese campo no está en los valores escritos
        # y la constraint no se dispara.
        for vals in vals_list:
            if not vals.get("parent_id") and self.search_count(
                [("parent_id", "=", False)]
            ):
                raise ValidationError(
                    "Ya existe un nodo raíz. El árbol solo puede tener uno: "
                    "colgá el nodo nuevo de un padre."
                )
        return super().create(vals_list)

    @api.depends("parent_id")
    def _compute_is_root(self):
        for node in self:
            node.is_root = not node.parent_id

    @api.depends("name", "parent_id", "parent_id.path_label")
    def _compute_path_label(self):
        for node in self:
            partes, puntero, visto = [], node, set()
            while puntero and puntero.id not in visto:
                visto.add(puntero.id)
                partes.append(puntero.name or "?")
                puntero = puntero.parent_id
            node.path_label = " > ".join(reversed(partes))

    @api.onchange("claim_type_id")
    def _onchange_claim_type_id(self):
        if self.subtype_id.type_id != self.claim_type_id:
            self.subtype_id = False
        if self.detail_id.subtype_id != self.subtype_id:
            self.detail_id = False

    @api.onchange("subtype_id")
    def _onchange_subtype_id(self):
        if self.detail_id.subtype_id != self.subtype_id:
            self.detail_id = False

    # ---------------------------------------------------------- validación
    @api.constrains("parent_id")
    def _check_no_cycles(self):
        for node in self:
            visto, puntero = set(), node.parent_id
            while puntero:
                if puntero == node or puntero.id in visto:
                    raise ValidationError(
                        "El nodo «%s» no puede depender de sí mismo." % node.name
                    )
                visto.add(puntero.id)
                puntero = puntero.parent_id

    @api.constrains("parent_id")
    def _check_single_root(self):
        if self.search_count([("parent_id", "=", False)]) > 1:
            raise ValidationError(
                "El árbol solo puede tener una raíz. "
                "Dejá un único nodo sin padre."
            )

    @api.constrains("kind", "child_ids", "parent_id", "url", "phone", "claim_type_id", "subtype_id", "active")
    def _check_kind(self):
        """Lo que se puede validar nodo por nodo.

        Que un menú tenga opciones NO se valida acá: al crear un menú todavía
        no tiene hijos, así que fallaría siempre. Eso se revisa en
        `_check_tree`, al publicar.
        """
        for node in self:
            children = node.child_ids.filtered("active")

            # Un hijo no puede colgar de una acción. Se comprueba desde el
            # hijo porque es el registro que se está escribiendo: la constraint
            # del padre no se dispara al crear un hijo.
            parent = node.parent_id
            if parent and parent.kind in ("link", "phone", "whatsapp", "claim"):
                raise ValidationError(
                    "«%s» es una acción y no admite opciones. "
                    "Cambiá el tipo del padre a menú o mensaje." % parent.name
                )
            if node.kind in ("link", "phone", "whatsapp", "claim") and children:
                raise ValidationError(
                    "El nodo «%s» es una acción y no puede tener opciones "
                    "colgando." % node.name
                )
            if node.kind == "link" and not node.url:
                raise ValidationError(
                    "El nodo «%s» abre un link y no tiene URL." % node.name
                )
            if node.kind in ("phone", "whatsapp") and not node.phone:
                raise ValidationError(
                    "El nodo «%s» necesita un teléfono." % node.name
                )
            if node.kind == "claim" and not (node.claim_type_id and node.subtype_id):
                raise ValidationError(
                    "El nodo «%s» pide un reclamo y le falta el tipo o el "
                    "subtipo." % node.name
                )

    @api.model
    def _check_tree(self):
        """Validación del árbol entero. Corre al publicar, no al guardar."""
        nodes = self.search([])
        if not nodes:
            raise ValidationError("El árbol está vacío.")

        roots = nodes.filtered(lambda n: not n.parent_id)
        if len(roots) > 1:
            raise ValidationError(
                "El árbol tiene %s raíces. Dejá una sola." % len(roots)
            )

        for node in nodes:
            if node.kind == "menu" and not node.child_ids.filtered("active"):
                raise ValidationError(
                    "El menú «%s» no tiene opciones activas: el usuario "
                    "quedaría sin salida." % node.name
                )
        return True

    # -------------------------------------------------------- compilación
    def _serialize(self, node):
        """Un nodo y su descendencia activa, en el JSON que consume el widget."""
        data = {
            "code": node.code,
            "label": node.name,
            "kind": node.kind,
            "message": node.message or "",
            "back": bool(node.allow_back),
        }
        if node.kind == "link":
            data["url"] = node.url or ""
        elif node.kind in ("phone", "whatsapp"):
            data["phone"] = node.phone or ""
            if node.kind == "whatsapp":
                data["wa_text"] = node.whatsapp_message or ""
        elif node.kind == "claim":
            data["claim"] = {
                "type": node.claim_type_id.code,
                "subtype": node.subtype_id.code,
                "detail": node.detail_id.code or None,
            }

        children = node.child_ids.filtered("active").sorted("sequence")
        if children:
            data["options"] = [self._serialize(child) for child in children]
        return data

    @api.model
    def _root(self):
        return self.search([("parent_id", "=", False)], limit=1)

    @api.model
    def _compile(self, version=0):
        root = self._root()
        if not root:
            raise ValidationError(
                "No hay ningún nodo raíz: no se puede publicar el árbol."
            )
        return {
            "version": version,
            "root": self._serialize(root),
        }

    @api.model
    def _count_nodes(self, data):
        return 1 + sum(
            self._count_nodes(child) for child in data.get("options", [])
        )

    @api.model
    def _find_by_code(self, code):
        if not code:
            return self.browse()
        return self.search([("code", "=", code)], limit=1)

    def action_publish(self):
        self.ensure_one()
        return self.env["cda.chatbot.publish"]._open()

    # ------------------------------------------------- reclamo desde el chat
    @api.model
    def _create_claim_from_chat(self, payload):
        """Crea el cda.claim que dejó el usuario al rendirse.

        La taxonomía (tipo, subtipo, detalle) la define el nodo de tipo
        `claim` desde el que se pidieron los datos, no el widget: así el
        grafo manda y el sitio no puede inventar clasificaciones.
        """
        code = _text(payload.get("node"), 80)
        if not code:
            raise ClaimApiError("Falta el nodo de reclamo.")
        node = self._find_by_code(code)
        if not node:
            raise ClaimApiError("Nodo de reclamo inexistente: %s." % code, 422)
        if node.kind != "claim":
            raise ClaimApiError(
                "El nodo %s no pide un reclamo." % code, 422
            )

        description = _text(payload.get("description"), 8000)
        if not description:
            raise ClaimApiError("El reclamo necesita una descripción.")

        entry = self.env["cda.claim.entry.code"].search(
            [("code", "=", ENTRY_CODE)], limit=1
        )
        if not entry:
            raise ClaimApiError(
                "Falta el medio de entrada %s en el sistema." % ENTRY_CODE, 500
            )

        # Idempotencia: si el widget reintenta, devolvemos el mismo reclamo.
        external = _text(payload.get("external_ref"), 120)
        if external:
            existing = self.env["cda.claim"].search(
                [("external_ref", "=", external)], limit=1
            )
            if existing:
                return self._claim_response(existing, created=False)

        abandon = self._find_by_code(_text(payload.get("abandon_node"), 80)) or node

        claim = self.env["cda.claim"].create(
            {
                "name": _text(payload.get("subject"), 200)
                or _text(payload.get("name"), 200)
                or "Consulta desde el chat",
                "description": description,
                "entry_code_id": entry.id,
                "claim_type_id": node.claim_type_id.id,
                "subtype_id": node.subtype_id.id,
                "detail_id": node.detail_id.id or False,
                "email": _text(payload.get("email"), 200),
                "phone": _text(payload.get("phone"), 60),
                "external_ref": external or False,
                "chat_session": _text(payload.get("session"), 120),
                "chat_node_id": abandon.id,
                "chat_path": _text(payload.get("path"), 4000),
                "chat_transcript": _text(
                    payload.get("transcript"), MAX_TRANSCRIPT
                ),
                "chat_origin": _text(payload.get("origin"), 500),
            }
        )
        claim.message_post(body="Reclamo creado desde el chatbot.")
        return self._claim_response(claim, notificado=claim._send_claimant_email())

    def _claim_response(self, claim, created=True, notificado=False):
        return {
            "id": claim.id,
            "number": claim.number,
            "stage": claim.stage_id.name,
            "created": created,
            # True si Odoo mandó el aviso; si es False, lo manda el sitio.
            "notificado": bool(notificado),
        }
