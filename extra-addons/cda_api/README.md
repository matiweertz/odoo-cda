# cda_api — API REST de Caminos del Aconcagua

Módulo Odoo 19 que expone `/api/v1` sobre el ORM. La autenticación es **Bearer con API key de `res.users`**: cada cliente usa una clave de un usuario Odoo, así que las ACL, las record rules y el multi-company son los del usuario dueño de la clave.

No hay gateway ni tabla intermedia: el módulo reemplaza al FastAPI (`fastapi/odoo-api`), que queda archivado como referencia.

## Requisitos

- Odoo 19 con `cda_claims` instalado.
- Un usuario Odoo con los permisos que se quieran dar a la API (ej. `cda_service`, grupo Operador: leer, crear y escribir).

## Instalación

```bash
odoo-bin -c odoo.conf -d <db> -i cda_api --stop-after-init
```

Agregar al `addons_path` la carpeta que contiene `cda_api`.

## Credenciales

API key del usuario en Odoo: avatar → Preferencias → pestaña **Seguridad** → **Add API Key**. Se muestra una sola vez.

```
Authorization: Bearer <api-key>
```

Sin header o con una clave inválida: `401 {"code": "unauthorized"}`.

## Endpoints

| Método | Ruta | Qué hace |
|---|---|---|
| `GET` | `/api/v1/claims/search` | Busca por tipo (código o nombre), asunto, estado y empresa. |
| `GET` | `/api/v1/claims/{id}` | Formulario completo + vialidad (`frm`, `vehicles`, `injured`, `witnesses`, `attachments`). |
| `GET` | `/api/v1/claims/attachments/{id}` | Abre el adjunto: sirve el archivo con Bearer o redirige al URL externo. |

`POST` y `PATCH` dejan una nota en el chatter del reclamo: `Reclamo creado vía API` / `Actualizado vía API` con la lista de campos que cambiaron. El header opcional `X-Client: web|frm|chatbot` se agrega a esa nota para saber por dónde entró. El tracking automático de Odoo se apaga en esas escrituras (`mail_notrack`) para no duplicar líneas.
| `POST` | `/api/v1/claims` | Crea un reclamo base. Idempotente por `external_ref`. |
| `PATCH` | `/api/v1/claims/{id}` | Actualiza campos y devuelve el detalle completo. |
| `GET` | `/api/v1/claim-types` | Catálogo de tipos para poblar formularios. |
| `GET` | `/api/v1/openapi.json` | Contrato OpenAPI 3.0. |
| `GET` | `/api/v1/docs` | Scalar UI (moderna). |
| `GET` | `/api/v1/docs/swagger` | Swagger UI (fallback). |

### Ejemplos

```bash
curl -H "Authorization: Bearer $CDA_KEY" \
  "http://localhost:8069/api/v1/claims/search?claim_type=reclamo&subject=peaje"

curl -H "Authorization: Bearer $CDA_KEY" \
  "http://localhost:8069/api/v1/claims/12"

curl -X POST -H "Authorization: Bearer $CDA_KEY" -H "Content-Type: application/json" \
  -d '{"claim_type":"reclamo","entry_code":"WEB","description":"Cobro duplicado","subject":"Cobro duplicado"}' \
  "http://localhost:8069/api/v1/claims"

curl -X PATCH -H "Authorization: Bearer $CDA_KEY" -H "Content-Type: application/json" \
  -d '{"stage_id":2,"frm":{"km":"12+300","direction":"asc"}}' \
  "http://localhost:8069/api/v1/claims/12"
```

### Detalle del contrato

| API | Odoo `cda.claim` |
|---|---|
| `id` / `number` | `id` / `number` (`CDA/AAAA/NNNNN`) |
| `claim_type` | `claim_type_id` por `code` o nombre |
| `entry_code` | `entry_code_id` por `code` |
| `subject` | `name` |
| `stage` | `stage_id` (`name`); se escribe con `stage_id` |
| `frm.*` | `frm_*` sin prefijo; los computados son solo lectura |
| `vehicles` / `injured` / `witnesses` | `frm_vehicle_ids` / `frm_injured_ids` / `frm_witness_ids`, reemplazo completo en cada PATCH |
| `attachments[].view_url` | `url` externa si existe; si el adjunto es un archivo en Odoo, `/api/v1/claims/attachments/{id}` (mismo Bearer) |

## Errores

Formato uniforme `{"detail": "...", "code": "..."}`, incluso en los fallos de autenticación (override de `ir.http._handle_error`).

| HTTP | `code` | Cuándo |
|---|---|---|
| 400 | `bad_request` | Body vacío o JSON inválido. |
| 401 | `unauthorized` | Sin Bearer o API key inválida. |
| 403 | `forbidden` / `forbidden_company` | ACL de Odoo o empresa fuera de las habilitadas. |
| 404 | `claim_not_found` | No existe o no visible para el usuario. |
| 409 | `conflict` | Unicidad (`external_ref`). |
| 422 | `validation_error` | Campo desconocido, tipo/medio inexistente, fecha inválida. |

## Notas técnicas

- Lecturas y catálogo: `type="http"` (query params). Escrituras: `type="json2"` (JSON plano + respuesta JSON, y es el dispatcher que parsea el body).
- `PATCH` y `POST` no usan CSRF: la autenticación es por Bearer, no por cookie.
- Idempotencia: `POST` busca por `external_ref`; si hay carrera, cae en un savepoint y devuelve el existente.
- El servidor no setea CORS: si el front es otro origen, usar el proxy de siempre o `--cors` de Odoo.
