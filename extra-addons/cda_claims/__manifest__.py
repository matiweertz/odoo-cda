{
    "name": "CDA Reclamos",
    "version": "19.0.1.6.0",
    "summary": "Reclamos de Caminos del Aconcagua",
    "description": """
Gestión de reclamos de Caminos del Aconcagua.

Modelo propio cda.claim con clasificación en tipo, subtipo y detalle, medio de
entrada con los 17 códigos y formulario de reclamo. Numeración
MEDIO-TIPO-SUBTIPO-NUMERO.

La API REST vive en el módulo cda_api, que autentica con API keys de res.users.
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
    ],
    "assets": {
        "web.assets_backend": [
            "cda_claims/static/src/scss/claim_form.scss",
        ],
    },
    "installable": True,
}