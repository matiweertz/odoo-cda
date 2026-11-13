import re

from odoo.http import request
from werkzeug.exceptions import Unauthorized

REQUIRE_AUTH = "cda_api.require_auth"
SERVICE_USER = "cda_api.service_user_id"
TRUTHY = ("1", "true", "yes", "t")

_BEARER = re.compile(r"^bearer\s+(.+)$", re.IGNORECASE)


def _token():
    header = request.httprequest.headers.get("Authorization")
    if not header:
        return None
    encontrado = _BEARER.match(header)
    return encontrado.group(1).strip() if encontrado else None


def _exigir_api_key():
    """Valida el Bearer y devuelve el usuario dueño de la key.

    No se delega en ir.http._auth_method_bearer() porque estas rutas son
    auth="public": ahí request.env.uid ya es el usuario público y el control de
    "la sesión no es la dueña de la key" de Odoo saltaría siempre, incluso con
    una key válida.
    """
    token = _token()
    if not token:
        raise Unauthorized(
            "Falta el encabezado Authorization con la API key (esquema Bearer).",
            www_authenticate="Bearer",
        )
    uid = (
        request.env["res.users.apikeys"]
        .sudo()
        ._check_credentials(scope="rpc", key=token)
    )
    if not uid:
        raise Unauthorized(
            "La API key no es válida o venció.",
            www_authenticate="Bearer",
        )
    request.update_env(user=uid)
    return uid


def api_user():
    params = request.env["ir.config_parameter"].sudo()
    require = (params.get_param(REQUIRE_AUTH) or "").strip().lower() in TRUTHY
    if require:
        return _exigir_api_key()
    raw = (params.get_param(SERVICE_USER) or "").strip()
    user = request.env["res.users"]
    if raw.isdigit():
        user = user.sudo().browse(int(raw)).exists()
    if not user:
        user = request.env.ref("base.user_root")
    request.update_env(user=user.id)
    return user.id
