import json

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged

from odoo.addons.cda_api.models.claim_api import ClaimApiError


@tagged("post_install", "-at_install")
class TestChatbotNode(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Node = cls.env["cda.chatbot.node"]
        cls.Publication = cls.env["cda.chatbot.publication"]

        cls.claim_type = cls.env.ref("cda_claims.claim_type_reclamos")
        cls.subtype = cls.env.ref("cda_claims.subtype_telepase")

        cls.root = cls.Node.create(
            {
                "code": "raiz",
                "name": "Inicio",
                "kind": "menu",
                "message": "Hola. Soy tu asistente.",
                "allow_back": False,
            }
        )
        cls.emergency = cls.Node.create(
            {
                "code": "emergencias",
                "name": "Emergencias",
                "kind": "phone",
                "phone": "140",
                "parent_id": cls.root.id,
                "sequence": 10,
            }
        )
        cls.rates = cls.Node.create(
            {
                "code": "tarifas",
                "name": "Tarifas",
                "kind": "menu",
                "message": "Elegí una opción:",
                "parent_id": cls.root.id,
                "sequence": 20,
            }
        )
        cls.telepase = cls.Node.create(
            {
                "code": "tarifas.telepase",
                "name": "TelePASE",
                "kind": "link",
                "url": "https://www.telepase.com.ar/",
                "parent_id": cls.rates.id,
            }
        )
        cls.claim_node = cls.Node.create(
            {
                "code": "reclamo",
                "name": "Dejar un reclamo",
                "kind": "claim",
                "message": "Dejanos tu mail.",
                "parent_id": cls.root.id,
                "sequence": 30,
                "claim_type_id": cls.claim_type.id,
                "subtype_id": cls.subtype.id,
            }
        )

    # --------------------------------------------------------------- árbol
    def test_01_compile(self):
        data = self.Node._compile(version=7)

        self.assertEqual(data["version"], 7)
        root = data["root"]
        self.assertEqual(root["code"], "raiz")
        self.assertFalse(root["back"])
        self.assertEqual(len(root["options"]), 3)

        codes = [option["code"] for option in root["options"]]
        self.assertEqual(codes, ["emergencias", "tarifas", "reclamo"])

        emergency = root["options"][0]
        self.assertEqual(emergency["kind"], "phone")
        self.assertEqual(emergency["phone"], "140")
        self.assertTrue(emergency["back"])

        claim = root["options"][2]
        self.assertEqual(claim["claim"]["type"], self.claim_type.code)
        self.assertEqual(claim["claim"]["subtype"], self.subtype.code)

    def test_02_publish_is_immutable(self):
        first = self.Publication._publish(note="v1")
        self.assertTrue(first.is_current)
        self.assertEqual(first.node_count, 5)

        # Edito el árbol: lo publicado no cambia.
        self.emergency.name = "Emergencias 140"
        self.assertNotIn("Emergencias 140", first.payload)

        second = self.Publication._publish(note="v2")
        self.assertEqual(second.version, first.version + 1)
        self.assertTrue(second.is_current)
        self.assertFalse(first.is_current)
        self.assertIn("Emergencias 140", second.payload)

        # Volver atrás.
        first.action_activate()
        self.assertTrue(first.is_current)
        self.assertFalse(second.is_current)

        # El payload sigue siendo JSON válido y completo.
        payload = json.loads(second.payload)
        self.assertIn("root", payload)

    def test_03_single_root(self):
        with self.assertRaises(ValidationError):
            self.Node.create(
                {"code": "otra.raiz", "name": "Otra", "kind": "message"}
            )

    def test_04_menu_without_children_blocks_publish(self):
        # Se puede guardar un menú vacío mientras se arma el árbol...
        empty = self.Node.create(
            {
                "code": "vacio",
                "name": "Vacío",
                "kind": "menu",
                "parent_id": self.root.id,
            }
        )
        # ...pero no se puede publicar.
        with self.assertRaises(ValidationError):
            self.Node._check_tree()
        empty.unlink()
        self.assertTrue(self.Node._check_tree())

    def test_05_action_with_children(self):
        link = self.Node.create(
            {
                "code": "link.solo",
                "name": "Link solo",
                "kind": "link",
                "url": "https://ejemplo.com",
                "parent_id": self.root.id,
            }
        )
        with self.assertRaises(ValidationError):
            self.Node.create(
                {
                    "code": "hijo.del.link",
                    "name": "Hijo",
                    "kind": "message",
                    "parent_id": link.id,
                }
            )

    def test_06_cycle(self):
        # Odoo detecta la recursion por _parent_store (UserError) antes que
        # nuestra constraint (ValidationError): cualquiera de los dos está bien.
        with self.assertRaises(Exception):
            self.rates.parent_id = self.telepase

    def test_07_link_without_url_and_claim_without_type(self):
        with self.assertRaises(ValidationError):
            self.Node.create(
                {
                    "code": "link.sin.url",
                    "name": "Sin URL",
                    "kind": "link",
                    "parent_id": self.root.id,
                }
            )
        with self.assertRaises(ValidationError):
            self.Node.create(
                {
                    "code": "reclamo.sin.tipo",
                    "name": "Sin tipo",
                    "kind": "claim",
                    "parent_id": self.root.id,
                }
            )

    # ------------------------------------------------------------ reclamo
    def test_10_claim_from_chat(self):
        result = self.Node._create_claim_from_chat(
            {
                "node": "reclamo",
                "subject": "Consulta por tarifas",
                "description": "No encuentro la tarifa de la categoría 2",
                "name": "Juan Pérez",
                "email": "juan@ejemplo.com",
                "phone": "2615555555",
                "session": "s-abc-123",
                "path": "Inicio > Tarifas",
                "abandon_node": "tarifas",
                "transcript": "Bot: Hola\nUsuario: tarifas",
                "origin": "https://caminosdelaconcagua.com.ar/tarifas",
            }
        )

        claim = self.env["cda.claim"].browse(result["id"])
        self.assertTrue(claim.exists())
        self.assertEqual(claim.entry_code_id.code, "BOT")
        self.assertEqual(claim.claim_type_id, self.claim_type)
        self.assertEqual(claim.subtype_id, self.subtype)
        self.assertEqual(claim.chat_session, "s-abc-123")
        self.assertEqual(claim.chat_node_id, self.rates)
        self.assertIn("Inicio > Tarifas", claim.chat_path)
        self.assertTrue(result["number"])
        self.assertTrue(result["created"])

    def test_11_claim_idempotent(self):
        base = {
            "node": "reclamo",
            "description": "Cobro duplicado",
            "email": "a@b.com",
            "external_ref": "s-xyz-1",
        }
        first = self.Node._create_claim_from_chat(dict(base))
        second = self.Node._create_claim_from_chat(dict(base))
        self.assertEqual(first["id"], second["id"])
        self.assertFalse(second["created"])

    def test_12_claim_requires_node(self):
        with self.assertRaises(ClaimApiError):
            self.Node._create_claim_from_chat({"description": "sin nodo"})

    def test_13_claim_rejects_non_claim_node(self):
        with self.assertRaises(ClaimApiError):
            self.Node._create_claim_from_chat(
                {"node": "tarifas", "description": "no es nodo de reclamo"}
            )

    def test_14_claim_requires_description(self):
        with self.assertRaises(ClaimApiError):
            self.Node._create_claim_from_chat(
                {"node": "reclamo", "description": "  "}
            )
