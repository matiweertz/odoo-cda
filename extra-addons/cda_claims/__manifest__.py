{
    "name": "CDA Reclamos",
    "version": "19.0.1.5.0",
    "summary": "Reclamos de Caminos del Aconcagua",
    "description": """
Gestión de reclamos de Caminos del Aconcagua.

Modelo propio cda.claim con clasificación en tipo, subtipo y detalle, medio de
entrada con los 17 códigos, referencia externa idempotente y formulario de
reclamo. Numeración MEDIO-TIPO-SUBTIPO-NUMERO.

El controlador /api/claims usa un entorno elevado sobre el usuario de servicio
configurado en cda_claims.service_user_id, porque el llamador ya fue autenticado
por el Gateway FastAPI y la cabecera X-Api-Key vive en cda_claims.api_key.
""",
    "author": "Watson",
    "license": "AGPL-3",
    "category": "Services/Helpdesk",
    "depends": ["mail"],
    "data": [
        "security/groups.xml",
        "security/ir_rules.xml",
        "security/ir.model.access.csv",
        "data/claim_data.xml",
        "data/claim_type_data.xml",
        "data/claim_taxonomy_data.xml",
        "data/crane_type_data.xml",
        "views/claim_views.xml",
        "views/claim_frm_views.xml",
        "views/entry_code_views.xml",
        "views/claim_type_views.xml",
        "views/claim_taxonomy_views.xml",
        "views/crane_type_views.xml",
        "views/claim_merge_wizard_views.xml",
        "views/claim_menus.xml",
        "views/cda_api_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "cda_claims/static/src/scss/claim_form.scss",
        ],
    },
    "installable": True,
}
