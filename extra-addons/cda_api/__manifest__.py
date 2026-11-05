{
    "name": "CDA API REST",
    "version": "19.0.1.1.0",
    "summary": "API REST de Caminos del Aconcagua sobre el ORM",
    "description": """
Expone /api/v1 con autenticación Bearer usando las API keys nativas de
res.users, sobre los modelos de cda_claims. No hay tablas intermedias ni
claves paralelas: las ACL, record rules y el multi-company son los del
usuario dueño de la API key.

Endpoints: búsqueda de reclamos, detalle con formulario de vialidad, alta
idempotente por external_ref y actualización parcial. Documentación en
/api/v1/docs y contrato en /api/v1/openapi.json.
""",
    "author": "Watson",
    "license": "AGPL-3",
    "category": "Services/Helpdesk",
    "depends": ["cda_claims"],
    "data": [
        "views/api_views.xml",
    ],
    "installable": True,
}