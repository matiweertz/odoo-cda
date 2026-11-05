import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute(
        """
        SELECT 1
          FROM information_schema.columns
         WHERE table_name = 'cda_claim'
           AND column_name = 'claim_type'
        """
    )
    if not cr.fetchone():
        return
    cr.execute(
        """
        UPDATE cda_claim c
           SET claim_type_id = t.id
          FROM cda_claim_type t
         WHERE t.code = c.claim_type
           AND c.claim_type_id IS NULL
        """
    )
    _logger.info("cda_claims: %s reclamos migrados a tipo de reclamo", cr.rowcount)
    cr.execute(
        """
        UPDATE cda_claim
           SET claim_type_id = (
               SELECT id FROM cda_claim_type ORDER BY sequence, id LIMIT 1
           )
         WHERE claim_type_id IS NULL
        """
    )
