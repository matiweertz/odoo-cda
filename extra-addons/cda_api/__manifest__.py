{
    "name": "CDA API REST",
    "version": "19.0.1.0.0",
    "summary": "API REST de Caminos del Aconcagua sobre el ORM",
    "description": """
Expone /api/v1 con autenticación Bearer (API key de res.users) sobre los
modelos de cda_claims. Reemplaza al gateway FastAPI: no hay tablas
intermedias ni claves paralelas, las ACL, record rules y el multi-company
son los del usuario dueño de la API key.

Endpoints: búsqueda de reclamos, detalle con formulario de vialidad,
alta idempotente por external_ref y actualización parcial.
""",
    "author": "Watson",
    "license": "AGPL-3",
    "category": "Services/Helpdesk",
    "depends": ["cda_claims"],
    "data": [],
    "installable": True,
}
