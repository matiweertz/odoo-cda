"""Migración 19.0.1.8.0 de cda_claims.

Los detalles van con noupdate="1", así que cambiar el nombre en el XML no
actualiza los registros que ya existen. Acá se renombran los dos detalles de
Siniestros/Accidente para que el combo quede con las tres opciones pedidas.
"""

import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

RENOMBRES = {
    "CL": "Personas lesionadas",
    "SL": "Personas no lesionadas",
}

NUEVOS = [
    {"code": "AM", "name": "Ambos", "sequence": 30},
]


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    Detail = env["cda.claim.detail"]
    subtype = env.ref("cda_claims.subtype_accidente", raise_if_not_found=False)
    if not subtype:
        return

    for code, nombre in RENOMBRES.items():
        detalle = Detail.search(
            [("code", "=", code), ("subtype_id", "=", subtype.id)]
        )
        if detalle and detalle.name != nombre:
            anterior = detalle.name
            detalle.write({"name": nombre})
            _logger.info(
                "cda_claims: detalle %s renombrado de '%s' a '%s'",
                code,
                anterior,
                nombre,
            )

    for datos in NUEVOS:
        existe = Detail.search(
            [("code", "=", datos["code"]), ("subtype_id", "=", subtype.id)]
        )
        if not existe:
            Detail.create(
                {
                    "code": datos["code"],
                    "name": datos["name"],
                    "sequence": datos["sequence"],
                    "subtype_id": subtype.id,
                }
            )
            _logger.info(
                "cda_claims: detalle %s (%s) creado",
                datos["code"],
                datos["name"],
            )
