from odoo.http import request

REQUIRE_AUTH = "cda_api.require_auth"
SERVICE_USER = "cda_api.service_user_id"
TRUTHY = ("1", "true", "yes", "t")


def api_user():
    params = request.env["ir.config_parameter"].sudo()
    require = (params.get_param(REQUIRE_AUTH) or "").strip().lower() in TRUTHY
    if require:
        request.env["ir.http"]._auth_method_bearer()
        return request.env.uid
    raw = (params.get_param(SERVICE_USER) or "").strip()
    user = request.env["res.users"]
    if raw.isdigit():
        user = user.sudo().browse(int(raw)).exists()
    if not user:
        user = request.env.ref("base.user_root")
    request.update_env(user=user.id)
    return user.id
