"""Migración 19.0.1.7.0 de cda_claims.

Los datos del módulo van con noupdate="1", así que sacar un <record> del XML no
lo borra de la base. Acá se limpian los cambios de datos:

- Se retiran los medios de entrada GRP (grupo de WhatsApp) y FRM (formulario del
  móvil). Si ningún reclamo los usa se borran; si alguno los usa se archivan,
  para no romper la referencia.
- Se convierten los valores viejos de "¿Hubo personas lesionadas?" (sí/no) a la
  nueva lista de tres opciones.
"""

import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

CODIGOS_A_RETIRAR = ("GRP", "FRM")

# valor viejo -> valor nuevo
MAPA_LESIONADOS = {
    "yes": "injured",
    "no": "no_injured",
}


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})

    # --- medios de entrada ---
    EntryCode = env["cda.claim.entry.code"]
    Claim = env["cda.claim"]
    for codigo in CODIGOS_A_RETIRAR:
        registro = EntryCode.search([("code", "=", codigo)])
        if not registro:
            continue
        en_uso = Claim.search_count([("entry_code_id", "in", registro.ids)])
        if en_uso:
            registro.write({"active": False})
            _logger.info(
                "cda_claims: %s archivado, lo usan %s reclamos",
                codigo,
                en_uso,
            )
        else:
            nombres = ", ".join(registro.mapped("name"))
            registro.unlink()
            _logger.info("cda_claims: %s eliminado (%s)", codigo, nombres)

    # --- valores de lesionados ---
    for viejo, nuevo in MAPA_LESIONADOS.items():
        cr.execute(
            "UPDATE cda_claim SET den_injured = %s WHERE den_injured = %s",
            (nuevo, viejo),
        )
        if cr.rowcount:
            _logger.info(
                "cda_claims: den_injured %s -> %s (%s registros)",
                viejo,
                nuevo,
                cr.rowcount,
            )
