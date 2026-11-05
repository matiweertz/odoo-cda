from odoo import http
from odoo.http import request

API = "/api/v1"

SCALAR_HTML = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>CDA API</title>
</head>
<body>
  <script id="api-reference" data-url="/api/v1/openapi.json"></script>
  <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
  <noscript>Usá <a href="/api/v1/docs/swagger">Swagger UI</a> o el contrato en /api/v1/openapi.json</noscript>
</body>
</html>
"""

SWAGGER_HTML = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>CDA API - Swagger UI</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css"/>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    window.ui = SwaggerUIBundle({
      url: "/api/v1/openapi.json",
      dom_id: "#swagger-ui",
      persistAuthorization: true,
      tryItOutEnabled: true
    });
  </script>
</body>
</html>
"""


def _reference() -> dict:
    return {
        "type": "object",
        "properties": {"id": {"type": "integer"}, "name": {"type": "string", "nullable": True}},
    }


def _code_reference() -> dict:
    return {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "code": {"type": "string", "nullable": True},
            "name": {"type": "string", "nullable": True},
        },
    }


def _error() -> dict:
    return {
        "type": "object",
        "properties": {"detail": {"type": "string"}, "code": {"type": "string"}},
        "required": ["detail", "code"],
    }


def _claim_update_properties() -> dict:
    return {
        "subject": {"type": "string", "nullable": True},
        "description": {"type": "string", "nullable": True},
        "claim_date": {"type": "string", "format": "date", "nullable": True},
        "phone": {"type": "string", "nullable": True},
        "email": {"type": "string", "nullable": True},
        "address": {"type": "string", "nullable": True},
        "external_ref": {"type": "string", "nullable": True},
        "claim_type": {"type": "string", "description": "Código o nombre del tipo."},
        "entry_code": {"type": "string", "description": "Código del medio de entrada."},
        "stage_id": {"type": "integer"},
        "user_id": {"type": "integer", "nullable": True},
        "company_id": {"type": "integer"},
        "frm": {"type": "object", "additionalProperties": True},
        "vehicles": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
        "injured": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
        "witnesses": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
    }


def _detail() -> dict:
    return {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "number": {"type": "string", "nullable": True},
            "subject": {"type": "string", "nullable": True},
            "description": {"type": "string", "nullable": True},
            "claim_date": {"type": "string", "format": "date", "nullable": True},
            "phone": {"type": "string", "nullable": True},
            "email": {"type": "string", "nullable": True},
            "address": {"type": "string", "nullable": True},
            "external_ref": {"type": "string", "nullable": True},
            "active": {"type": "boolean"},
            "is_frm": {"type": "boolean"},
            "closed": {"type": "boolean"},
            "unattended": {"type": "boolean"},
            "claim_type": _code_reference(),
            "entry_code": _code_reference(),
            "stage": _reference(),
            "user": _reference(),
            "company": _reference(),
            "frm": {
                "type": "object",
                "additionalProperties": True,
                "description": "Formulario de vialidad: claves sin el prefijo frm_.",
            },
            "vehicles": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
            "injured": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
            "witnesses": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
            "attachments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string", "nullable": True},
                        "url": {"type": "string", "nullable": True},
                        "kind": {"type": "string", "nullable": True},
                        "note": {"type": "string", "nullable": True},
                        "file_name": {"type": "string", "nullable": True},
                        "file_size": {"type": "integer"},
                        "view_url": {
                            "type": "string",
                            "nullable": True,
                            "description": (
                                "URL para abrir el adjunto: la externa si existe, "
                                "o /api/v1/claims/attachments/{id} para archivos en Odoo."
                            ),
                        },
                    },
                },
            },
        },
    }


def _spec() -> dict:
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "CDA API",
            "version": "1.0.0",
            "description": (
                "API REST de Caminos del Aconcagua sobre el ORM de Odoo. "
                "Autenticación: API key de un usuario de Odoo en "
                "`Authorization: Bearer <clave>`."
            ),
        },
        "servers": [{"url": "/"}],
        "tags": [{"name": "Claims"}, {"name": "Catalog"}],
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "description": "API key generada desde Preferencias → Seguridad en Odoo.",
                }
            },
            "schemas": {
                "Reference": _reference(),
                "CodeReference": _code_reference(),
                "Error": _error(),
                "ClaimSummary": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "number": {"type": "string", "nullable": True},
                        "claim_type": {"type": "string", "nullable": True},
                        "subject": {"type": "string", "nullable": True},
                        "description": {"type": "string", "nullable": True},
                        "stage": {"type": "string", "nullable": True},
                    },
                },
                "ClaimSearchResult": {
                    "type": "object",
                    "properties": {
                        "total": {"type": "integer"},
                        "limit": {"type": "integer"},
                        "offset": {"type": "integer"},
                        "items": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/ClaimSummary"},
                        },
                    },
                },
                "ClaimDetail": _detail(),
                "ClaimCreate": {
                    "type": "object",
                    "required": ["claim_type", "description", "entry_code"],
                    "properties": {
                        "claim_type": {"type": "string"},
                        "description": {"type": "string"},
                        "entry_code": {"type": "string"},
                        "subject": {"type": "string", "nullable": True},
                        "phone": {"type": "string", "nullable": True},
                        "email": {"type": "string", "nullable": True},
                        "address": {"type": "string", "nullable": True},
                        "claim_date": {"type": "string", "format": "date", "nullable": True},
                        "company_id": {"type": "integer", "nullable": True},
                        "user_id": {"type": "integer", "nullable": True},
                        "external_ref": {
                            "type": "string",
                            "nullable": True,
                            "description": "Clave de idempotencia.",
                        },
                        "frm": {"type": "object", "additionalProperties": True},
                    },
                },
                "ClaimUpdate": {
                    "type": "object",
                    "properties": _claim_update_properties(),
                },
                "ClaimCreated": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "number": {"type": "string", "nullable": True},
                        "created": {"type": "boolean"},
                    },
                },
            },
        },
        "security": [{"bearerAuth": []}],
        "paths": {
            "/api/v1/claims/search": {
                "get": {
                    "tags": ["Claims"],
                    "summary": "Busca reclamos por tipo, asunto y estado",
                    "parameters": [
                        {"name": "claim_type", "in": "query", "schema": {"type": "string"}},
                        {"name": "subject", "in": "query", "schema": {"type": "string"}},
                        {"name": "stage", "in": "query", "schema": {"type": "string"}},
                        {"name": "company_id", "in": "query", "schema": {"type": "integer"}},
                        {
                            "name": "limit",
                            "in": "query",
                            "schema": {"type": "integer", "default": 20, "maximum": 100},
                        },
                        {
                            "name": "offset",
                            "in": "query",
                            "schema": {"type": "integer", "default": 0},
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "Listado",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ClaimSearchResult"}
                                }
                            },
                        },
                        "401": {
                            "description": "Sin API key",
                            "content": {
                                "application/json": {"schema": {"$ref": "#/components/schemas/Error"}}
                            },
                        },
                    },
                }
            },
            "/api/v1/claims/{claim_id}": {
                "get": {
                    "tags": ["Claims"],
                    "summary": "Detalle completo con formulario de vialidad",
                    "parameters": [
                        {
                            "name": "claim_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Reclamo",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ClaimDetail"}
                                }
                            },
                        },
                        "404": {
                            "description": "No existe",
                            "content": {
                                "application/json": {"schema": {"$ref": "#/components/schemas/Error"}}
                            },
                        },
                    },
                },
                "patch": {
                    "tags": ["Claims"],
                    "summary": "Actualiza un reclamo",
                    "parameters": [
                        {
                            "name": "claim_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        },
                        {
                            "name": "X-Client",
                            "in": "header",
                            "required": False,
                            "schema": {"type": "string"},
                            "description": "Origen de la llamada (web, frm, chatbot).",
                        },
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ClaimUpdate"}
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Reclamo actualizado",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ClaimDetail"}
                                }
                            },
                        },
                        "422": {
                            "description": "Validación",
                            "content": {
                                "application/json": {"schema": {"$ref": "#/components/schemas/Error"}}
                            },
                        },
                    },
                },
            },
            "/api/v1/claims/attachments/{attachment_id}": {
                "get": {
                    "tags": ["Claims"],
                    "summary": "Abre el adjunto (archivo en Odoo o redirección al URL externo)",
                    "parameters": [
                        {
                            "name": "attachment_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Archivo",
                            "content": {
                                "application/octet-stream": {
                                    "schema": {"type": "string", "format": "binary"}
                                }
                            },
                        },
                        "302": {"description": "Redirección al URL externo del adjunto"},
                        "404": {
                            "description": "No existe",
                            "content": {
                                "application/json": {"schema": {"$ref": "#/components/schemas/Error"}}
                            },
                        },
                    },
                }
            },
            "/api/v1/claims": {
                "post": {
                    "tags": ["Claims"],
                    "summary": "Crea un reclamo base",
                    "parameters": [
                        {
                            "name": "X-Client",
                            "in": "header",
                            "required": False,
                            "schema": {"type": "string"},
                            "description": "Origen de la llamada (web, frm, chatbot). Queda en la nota del chatter.",
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ClaimCreate"}
                            }
                        },
                    },
                    "responses": {
                        "201": {
                            "description": "Creado o existente por external_ref",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ClaimCreated"}
                                }
                            },
                        },
                        "409": {
                            "description": "Conflicto de unicidad",
                            "content": {
                                "application/json": {"schema": {"$ref": "#/components/schemas/Error"}}
                            },
                        },
                        "422": {
                            "description": "Validación",
                            "content": {
                                "application/json": {"schema": {"$ref": "#/components/schemas/Error"}}
                            },
                        },
                    },
                }
            },
            "/api/v1/claim-types": {
                "get": {
                    "tags": ["Catalog"],
                    "summary": "Tipos de reclamo disponibles",
                    "responses": {
                        "200": {
                            "description": "Catálogo",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/CodeReference"
                                        },
                                    }
                                }
                            },
                        }
                    },
                }
            },
        },
    }


def _html(content: str):
    return request.make_response(
        content, headers=[("Content-Type", "text/html; charset=utf-8")]
    )


class CdaApiDocs(http.Controller):
    @http.route(f"{API}/openapi.json", type="http", auth="public", methods=["GET"], csrf=False)
    def openapi(self, **params):
        return request.make_json_response(_spec())

    @http.route(f"{API}/docs", type="http", auth="public", methods=["GET"], csrf=False)
    def scalar_docs(self, **params):
        return _html(SCALAR_HTML)

    @http.route(
        f"{API}/docs/swagger", type="http", auth="public", methods=["GET"], csrf=False
    )
    def swagger_docs(self, **params):
        return _html(SWAGGER_HTML)
