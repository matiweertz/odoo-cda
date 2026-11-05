import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

OBSOLETOS = (
    "cda_claims.action_cda_api_config",
    "cda_claims.cda_api_settings_view_form",
    "cda_claims.menu_cda_api_config",
)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for xmlid in OBSOLETOS:
        registro = env.ref(xmlid, raise_if_not_found=False)
        if registro:
            _logger.info("cda_claims: borrando registro obsoleto %s", xmlid)
            registro.unlink()