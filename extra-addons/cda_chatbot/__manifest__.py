{
    "name": "CDA Chatbot",
    "version": "19.0.1.4.0",
    "summary": "Grafo de preguntas y respuestas del chatbot",
    "description": """
Configuración del árbol de preguntas y respuestas del chatbot.

El árbol vive en cda.chatbot.node: cada nodo es una opción dentro de su padre
y el grafo se arma arrastrando. Se publica compilado a JSON (cda.chatbot.publication)
para que el sitio consuma una versión inmutable, y los reclamos que deja el
usuario caen en cda.claim con el medio de entrada BOT.
""",
    "author": "Watson",
    "license": "AGPL-3",
    "category": "Services/Helpdesk",
    "depends": ["cda_claims", "cda_api"],
    "data": [
        "security/ir.model.access.csv",
        "data/chatbot_arbol.xml",
        "views/chatbot_node_views.xml",
        "views/chatbot_publication_views.xml",
        "views/chatbot_publish_views.xml",
        "views/claim_views.xml",
        "views/chatbot_menus.xml",
    ],
    "installable": True,
    "application": True,
}
