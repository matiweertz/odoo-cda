import hmac

from odoo import http
from odoo.exceptions import AccessError, ValidationError
from odoo.http import request


class ClaimApi(http.Controller):
    def _verify_api_key(self):
        expected = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("cda_claims.api_key")
            or ""
        )
        provided = request.httprequest.headers.get("X-Api-Key") or ""
        if not expected or not hmac.compare_digest(expected, provided):
            raise AccessError("X-Api-Key inválida.")

    def _service_env(self):
        raw = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("cda_claims.service_user_id")
        )
        user = (
            request.env["res.users"].sudo().browse(int(raw)).exists()
            if raw
            else request.env["res.users"]
        )
        if not user:
            raise ValidationError("cda_claims.service_user_id no configurado.")
        return request.env(user=user.id, su=True)

    def _company(self, env, company_id):
        if not company_id:
            raise ValidationError("company_id es obligatorio.")
        company = env["res.company"].browse(int(company_id)).exists()
        if not company:
            raise ValidationError("company_id inexistente.")
        return company

    def _entry_code(self, env, code):
        entry_code = env["cda.claim.entry.code"].search([("code", "=", code)], limit=1)
        if not entry_code:
            raise ValidationError("Medio de entrada inexistente: %s" % code)
        return entry_code

    def _claim_type(self, env, code):
        claim_type = env["cda.claim.type"].search([("code", "=", code)], limit=1)
        if not claim_type:
            raise ValidationError("Tipo de reclamo inexistente: %s" % code)
        return claim_type

    def _subtype(self, env, claim_type, code):
        subtype = env["cda.claim.subtype"].search(
            [("code", "=", code), ("type_id", "=", claim_type.id)], limit=1
        )
        if not subtype:
            raise ValidationError("Subtipo inexistente: %s" % code)
        return subtype

    def _detail(self, env, subtype, code):
        detail = env["cda.claim.detail"].search(
            [("code", "=", code), ("subtype_id", "=", subtype.id)], limit=1
        )
        if not detail:
            raise ValidationError("Detalle inexistente: %s" % code)
        return detail

    @http.route(
        "/api/claims/create",
        type="jsonrpc",
        auth="none",
        methods=["POST"],
        csrf=False,
    )
    def create_claim(self, **payload):
        self._verify_api_key()
        entry_code_value = (payload.get("entry_code") or "").strip()
        description = (payload.get("description") or "").strip()
        if not entry_code_value:
            raise ValidationError("entry_code es obligatorio.")
        if not description:
            raise ValidationError("description es obligatoria.")
        claim_type_value = (payload.get("claim_type") or "").strip()
        subtype_value = (payload.get("subtype") or "").strip()
        detail_value = (payload.get("detail") or "").strip()
        if not claim_type_value:
            raise ValidationError("claim_type es obligatorio.")
        if not subtype_value:
            raise ValidationError("subtype es obligatorio.")
        env = self._service_env()
        company = self._company(env, payload.get("company_id"))
        claims = env["cda.claim"].with_company(company)
        external_ref = (payload.get("external_ref") or "").strip() or False
        if external_ref:
            existing = claims.search([("external_ref", "=", external_ref)], limit=1)
            if existing:
                return {"id": existing.id, "number": existing.number}
        entry_code = self._entry_code(env, entry_code_value)
        claim_type = self._claim_type(env, claim_type_value)
        subtype = self._subtype(env, claim_type, subtype_value)
        detail = self._detail(env, subtype, detail_value) if detail_value else False
        vals = {
            "company_id": company.id,
            "entry_code_id": entry_code.id,
            "claim_type_id": claim_type.id,
            "subtype_id": subtype.id,
            "detail_id": detail.id if detail else False,
            "description": description,
            "name": (payload.get("title") or "").strip() or description[:120],
            "phone": payload.get("phone"),
            "email": payload.get("email"),
            "address": payload.get("address"),
            "claim_date": payload.get("claim_date"),
            "external_ref": external_ref,
        }
        for key, value in payload.items():
            if key.startswith("den_") and key in claims._fields:
                if not claims._fields[key].compute:
                    vals[key] = value
        claim = claims.create({k: v for k, v in vals.items() if v not in (None, "")})
        self._link_urls(env, claim, payload.get("attachment_urls"))
        return {"id": claim.id, "number": claim.number}

    def _link_urls(self, env, claim, urls):
        incoming = [url.strip() for url in (urls or []) if url and url.strip()]
        if not incoming:
            return 0
        existing = set(claim.attachment_ids.mapped("url"))
        nuevos = [url for url in dict.fromkeys(incoming) if url not in existing]
        if nuevos:
            env["cda.claim.attachment"].create(
                [
                    {
                        "claim_id": claim.id,
                        "url": url,
                        "name": url.rsplit("/", 1)[-1][:80] or url[:80],
                    }
                    for url in nuevos
                ]
            )
        return len(nuevos)

    @http.route(
        "/api/claims/<int:claim_id>/attachments",
        type="jsonrpc",
        auth="none",
        methods=["POST"],
        csrf=False,
    )
    def add_claim_attachments(self, claim_id, urls=None, **payload):
        self._verify_api_key()
        env = self._service_env()
        claim = env["cda.claim"].browse(claim_id).exists()
        if not claim:
            raise ValidationError("Reclamo inexistente.")
        company_id = payload.get("company_id")
        if company_id and claim.company_id.id != int(company_id):
            raise ValidationError("El reclamo no pertenece a la empresa indicada.")
        if not [url for url in (urls or []) if url and url.strip()]:
            raise ValidationError("urls es obligatorio.")
        agregados = self._link_urls(env, claim, urls)
        return {
            "id": claim.id,
            "added": agregados,
            "attachment_count": len(claim.attachment_ids),
        }
