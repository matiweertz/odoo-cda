import base64
import datetime
import logging
import mimetypes
from typing import Any

from markupsafe import Markup, escape
from odoo import fields, models
from psycopg2 import IntegrityError

_logger = logging.getLogger(__name__)

SCALAR_TYPES = frozenset(
    {"char", "text", "integer", "float", "boolean", "date", "datetime", "selection", "monetary"}
)
FRM_PREFIX = "frm_"
CLAIM_MODEL = "cda.claim"
CLAIM_TYPE_MODEL = "cda.claim.type"
ENTRY_CODE_MODEL = "cda.claim.entry.code"
STAGE_MODEL = "cda.claim.stage"
VEHICLE_FIELDS = (
    "id",
    "conductor_name",
    "conductor_phone",
    "photo_dni",
    "photo_license",
    "plate",
    "make_model",
    "color",
    "kind",
    "owner",
    "insurer",
    "policy",
    "photo_policy",
    "carrier",
    "cargo",
    "dangerous_cargo",
)
INJURED_FIELDS = ("id", "name", "severity", "transferred_to", "refused_help", "own_staff")
WITNESS_FIELDS = ("id", "name", "phone", "own_staff")
CREATE_FIELDS = frozenset(
    {
        "claim_type",
        "description",
        "entry_code",
        "subject",
        "phone",
        "email",
        "address",
        "claim_date",
        "company_id",
        "user_id",
        "external_ref",
        "frm",
    }
)
UPDATE_FIELDS = frozenset(
    {
        "subject",
        "description",
        "claim_date",
        "phone",
        "email",
        "address",
        "external_ref",
        "claim_type",
        "entry_code",
        "stage_id",
        "user_id",
        "company_id",
        "frm",
        "vehicles",
        "injured",
        "witnesses",
    }
)


class ClaimApiError(Exception):
    def __init__(self, detail: str, status: int = 422, code: str = "validation_error") -> None:
        super().__init__(detail)
        self.detail = detail
        self.status = status
        self.code = code


class CdaClaimApi(models.AbstractModel):
    _name = "cda.claim.api"
    _description = "API REST de reclamos"

    def search_claims(self, params: dict[str, Any]) -> dict[str, Any]:
        claim_type = self._text(params.get("claim_type"))
        subject = self._text(params.get("subject"))
        stage = self._text(params.get("stage"))
        company_id = self._int_value(params.get("company_id"), "company_id")
        limit = self._int_value(params.get("limit"), "limit", default=20, minimum=1, maximum=100)
        offset = self._int_value(params.get("offset"), "offset", default=0, minimum=0)
        domain: list[Any] = []
        if claim_type:
            domain.extend(
                [
                    "|",
                    ("claim_type_id.code", "=", claim_type),
                    ("claim_type_id.name", "ilike", claim_type),
                ]
            )
        if subject:
            domain.append(("name", "ilike", subject))
        if stage:
            domain.append(("stage_id.name", "=", stage))
        if company_id is not None:
            self._check_company(company_id)
            domain.append(("company_id", "=", company_id))
        Claim = self.env[CLAIM_MODEL]
        total = Claim.search_count(domain)
        records = Claim.search(domain, limit=limit, offset=offset, order="id desc")
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": [self._serialize_summary(claim) for claim in records],
        }

    def get_claim(self, claim_id: int) -> dict[str, Any]:
        return self._serialize_detail(self._claim(claim_id))

    def create_claim(self, payload: dict[str, Any], origin: str | None = None) -> dict[str, Any]:
        vals = self._create_vals(payload)
        external_ref = vals.get("external_ref")
        if external_ref:
            existing = self.env[CLAIM_MODEL].search(
                [("external_ref", "=", external_ref)], limit=1
            )
            if existing:
                return self._created(existing, created=False)
        try:
            with self.env.cr.savepoint():
                claim = self.env[CLAIM_MODEL].with_context(
                    mail_create_nolog=True, mail_notrack=True
                ).create(vals)
        except IntegrityError:
            _logger.info("Reclamo duplicado por external_ref=%s", external_ref)
            if external_ref:
                existing = self.env[CLAIM_MODEL].search(
                    [("external_ref", "=", external_ref)], limit=1
                )
                if existing:
                    return self._created(existing, created=False)
            raise ClaimApiError(
                "El reclamo viola una restricción de unicidad.", 409, "conflict"
            ) from None
        claim.message_post(body=self._created_note(origin), subtype_xmlid="mail.mt_note")
        return self._created(claim, created=True)

    def update_claim(
        self, claim_id: int, payload: dict[str, Any], origin: str | None = None
    ) -> dict[str, Any]:
        claim = self._claim(claim_id)
        vals = self._update_vals(payload)
        if not vals:
            raise ClaimApiError("No hay campos válidos para actualizar.")
        changes = self._changes(claim, vals)
        claim.with_context(mail_notrack=True).write(vals)
        if changes:
            claim.message_post(
                body=self._updated_note(changes, origin), subtype_xmlid="mail.mt_note"
            )
        return self._serialize_detail(claim)

    def claim_types(self) -> list[dict[str, Any]]:
        records = self.env[CLAIM_TYPE_MODEL].search([])
        return [{"id": record.id, "code": record.code, "name": record.name} for record in records]

    def _create_vals(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._reject_unknown(payload, CREATE_FIELDS)
        claim_type = self._text(payload.get("claim_type"))
        description = self._text(payload.get("description"))
        entry_code = self._text(payload.get("entry_code"))
        if not claim_type:
            raise ClaimApiError("claim_type es obligatorio.")
        if not description:
            raise ClaimApiError("description es obligatoria.")
        if not entry_code:
            raise ClaimApiError("entry_code es obligatorio.")
        vals: dict[str, Any] = {
            "claim_type_id": self._resolve_claim_type(claim_type),
            "entry_code_id": self._resolve_entry_code(entry_code),
            "description": description,
            "user_id": self._user_id(payload.get("user_id")),
        }
        subject = self._text(payload.get("subject"))
        if subject:
            vals["name"] = subject
        for name in ("phone", "email", "address", "external_ref"):
            value = self._text(payload.get(name))
            if value:
                vals[name] = value
        if payload.get("claim_date"):
            vals["claim_date"] = self._parse_date(payload["claim_date"])
        company_id = payload.get("company_id")
        if company_id is not None:
            vals["company_id"] = self._check_company(company_id)
        frm = payload.get("frm")
        if frm:
            vals.update(self._frm_vals(frm))
        return vals

    def _update_vals(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._reject_unknown(payload, UPDATE_FIELDS)
        vals: dict[str, Any] = {}
        for name in ("name", "description", "phone", "email", "address", "external_ref"):
            key = "subject" if name == "name" else name
            if key in payload and payload[key] is not None:
                vals[name] = self._text(payload[key]) or False
        if payload.get("claim_date") is not None:
            vals["claim_date"] = self._parse_date(payload["claim_date"])
        if payload.get("claim_type") is not None:
            vals["claim_type_id"] = self._resolve_claim_type(self._text(payload["claim_type"]))
        if payload.get("entry_code") is not None:
            vals["entry_code_id"] = self._resolve_entry_code(self._text(payload["entry_code"]))
        if payload.get("stage_id") is not None:
            stage = self.env[STAGE_MODEL].browse(self._int_value(payload["stage_id"], "stage_id"))
            if not stage.exists():
                raise ClaimApiError("Estado inexistente.")
            vals["stage_id"] = stage.id
        if payload.get("user_id") is not None:
            vals["user_id"] = self._user_id(payload["user_id"])
        if payload.get("company_id") is not None:
            vals["company_id"] = self._check_company(payload["company_id"])
        if payload.get("frm"):
            vals.update(self._frm_vals(payload["frm"]))
        for key, field_name, label, allowed in (
            ("vehicles", "frm_vehicle_ids", "vehicles", VEHICLE_FIELDS),
            ("injured", "frm_injured_ids", "injured", INJURED_FIELDS),
            ("witnesses", "frm_witness_ids", "witnesses", WITNESS_FIELDS),
        ):
            rows = payload.get(key)
            if rows is not None:
                vals[field_name] = self._replace_commands(rows, label, allowed)
        return vals

    def _serialize_summary(self, claim: Any) -> dict[str, Any]:
        return {
            "id": claim.id,
            "number": claim.number or None,
            "claim_type": claim.claim_type_id.name or None,
            "subject": claim.name or None,
            "description": claim.description or None,
            "stage": claim.stage_id.name or None,
        }

    def _serialize_detail(self, claim: Any) -> dict[str, Any]:
        frm = {name[len(FRM_PREFIX):]: self._scalar(claim, name) for name in self._frm_read_names()}
        return {
            "id": claim.id,
            "number": claim.number or None,
            "subject": claim.name or None,
            "description": claim.description or None,
            "claim_date": self._scalar(claim, "claim_date"),
            "phone": claim.phone or None,
            "email": claim.email or None,
            "address": claim.address or None,
            "external_ref": claim.external_ref or None,
            "active": bool(claim.active),
            "is_frm": bool(claim.is_frm),
            "closed": bool(claim.closed),
            "unattended": bool(claim.unattended),
            "claim_type": self._code_reference(claim.claim_type_id),
            "entry_code": self._code_reference(claim.entry_code_id),
            "stage": self._reference(claim.stage_id),
            "user": self._reference(claim.user_id),
            "company": self._reference(claim.company_id),
            "frm": frm,
            "vehicles": [
                self._row(record, VEHICLE_FIELDS)
                for record in claim.frm_vehicle_ids.sorted("id")
            ],
            "injured": [
                self._row(record, INJURED_FIELDS)
                for record in claim.frm_injured_ids.sorted("id")
            ],
            "witnesses": [
                self._row(record, WITNESS_FIELDS)
                for record in claim.frm_witness_ids.sorted("id")
            ],
            "attachments": [
                {
                    "id": attachment.id,
                    "name": attachment.name or None,
                    "kind": attachment.kind or None,
                    "note": attachment.note or None,
                    "url": attachment.url or None,
                    "file_name": attachment.file_name or None,
                    "file_size": attachment.file_size or 0,
                    "view_url": self._attachment_url(attachment),
                }
                for attachment in claim.attachment_ids.sorted("id")
            ],
        }

    def _attachment_url(self, attachment: Any) -> str | None:
        if attachment.url:
            return attachment.url
        if attachment.file_size:
            return f"/api/v1/claims/attachments/{attachment.id}"
        return None

    def attachment_content(self, attachment_id: int) -> tuple[bytes, str, str]:
        attachment = self.env["cda.claim.attachment"].browse(attachment_id)
        if not attachment.exists():
            raise ClaimApiError(
                f"No existe el adjunto {attachment_id}.", 404, "attachment_not_found"
            )
        attachment.claim_id.check_access("read")
        data = base64.b64decode(attachment.file or "")
        if not data:
            raise ClaimApiError(
                "El adjunto no tiene archivo ni URL.", 404, "attachment_not_found"
            )
        file_name = attachment.file_name or attachment.name or f"adjunto-{attachment.id}"
        mime = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
        return data, file_name, mime

    def _changes(self, claim: Any, vals: dict[str, Any]) -> list[tuple[str, Any, Any]]:
        changes = []
        for name, new_value in vals.items():
            field = claim._fields.get(name)
            if field is None:
                continue
            label = field.string or name
            if field.type == "one2many":
                rows = len(new_value) - 1 if new_value else 0
                changes.append((label, None, f"{rows} fila(s)"))
                continue
            if field.type == "many2one":
                old = claim[name].display_name if claim[name] else None
                record = (
                    self.env[field.comodel_name].browse(new_value).exists()
                    if new_value
                    else None
                )
                new = record.display_name if record else None
            elif field.type == "boolean":
                old, new = bool(claim[name]), bool(new_value)
            elif field.type == "selection":
                labels = dict(field.selection)
                old = labels.get(claim[name])
                new = labels.get(new_value)
            else:
                old = self._normalize(claim[name])
                new = self._normalize(new_value)
            if old == new:
                continue
            changes.append((label, old, new))
        return changes

    @staticmethod
    def _normalize(value: Any) -> Any:
        if value is False or value == "":
            return None
        return value

    def _created_note(self, origin: str | None) -> Markup:
        text = "Reclamo creado vía API"
        if origin:
            text = f"{text} · cliente: {origin}"
        return Markup("<p>%s</p>") % escape(text)

    def _updated_note(
        self, changes: list[tuple[str, Any, Any]], origin: str | None
    ) -> Markup:
        text = "Actualizado vía API"
        if origin:
            text = f"{text} · cliente: {origin}"
        items = Markup("").join(
            Markup("<li>%s: %s → %s</li>")
            % (escape(label), escape(self._format_value(old)), escape(self._format_value(new)))
            for label, old, new in changes
        )
        return Markup("<p>%s</p><ul>%s</ul>") % (escape(text), items)

    @staticmethod
    def _format_value(value: Any) -> str:
        if value is None:
            return "—"
        if isinstance(value, bool):
            return "Sí" if value else "No"
        if isinstance(value, (datetime.date, datetime.datetime)):
            return value.isoformat()
        text = str(value)
        return text if len(text) <= 60 else f"{text[:57]}..."

    def _row(self, record: Any, names: tuple[str, ...]) -> dict[str, Any]:
        return {name: self._scalar(record, name) for name in names}

    def _scalar(self, record: Any, name: str) -> Any:
        field = record._fields[name]
        value = record[name]
        if value is False and field.type != "boolean":
            return None
        if field.type == "date" and value:
            return value.isoformat()
        if field.type == "datetime" and value:
            return value.isoformat(sep=" ")
        return value

    def _reference(self, record: Any) -> dict[str, Any] | None:
        if not record:
            return None
        return {"id": record.id, "name": record.display_name}

    def _code_reference(self, record: Any) -> dict[str, Any] | None:
        if not record:
            return None
        return {"id": record.id, "code": record.code or None, "name": record.display_name}

    def _frm_read_names(self) -> list[str]:
        return [
            name
            for name, field in self.env[CLAIM_MODEL]._fields.items()
            if name.startswith(FRM_PREFIX) and field.type in SCALAR_TYPES
        ]

    def _frm_writable_names(self) -> frozenset[str]:
        return frozenset(
            name[len(FRM_PREFIX):]
            for name, field in self.env[CLAIM_MODEL]._fields.items()
            if name.startswith(FRM_PREFIX)
            and field.type in SCALAR_TYPES
            and not field.readonly
            and not field.compute
        )

    def _frm_vals(self, values: Any) -> dict[str, Any]:
        if not isinstance(values, dict):
            raise ClaimApiError("frm debe ser un objeto.")
        allowed = self._frm_writable_names()
        unknown = sorted(set(values) - allowed)
        if unknown:
            raise ClaimApiError(f"Campos FRM desconocidos: {', '.join(unknown)}.")
        return {f"{FRM_PREFIX}{name}": value for name, value in values.items()}

    def _replace_commands(
        self, rows: Any, label: str, allowed: tuple[str, ...]
    ) -> list[Any]:
        if not isinstance(rows, list):
            raise ClaimApiError(f"{label} debe ser una lista.")
        commands: list[Any] = [(5, 0, 0)]
        for row in rows:
            if not isinstance(row, dict):
                raise ClaimApiError(f"Cada elemento de {label} debe ser un objeto.")
            unknown = sorted(set(row) - (set(allowed) - {"id"}))
            if unknown:
                raise ClaimApiError(f"Campos desconocidos en {label}: {', '.join(unknown)}.")
            commands.append((0, 0, {k: v for k, v in row.items() if k != "id"}))
        return commands

    def _resolve_claim_type(self, value: str) -> int:
        record = self.env[CLAIM_TYPE_MODEL].search(
            ["|", ("code", "=", value), ("name", "ilike", value)], limit=1
        )
        if not record:
            raise ClaimApiError(f"Tipo de reclamo inexistente: {value}.")
        return record.id

    def _resolve_entry_code(self, value: str) -> int:
        record = self.env[ENTRY_CODE_MODEL].search([("code", "=", value)], limit=1)
        if not record:
            raise ClaimApiError(f"Medio de entrada inexistente: {value}.")
        return record.id

    def _claim(self, claim_id: int) -> Any:
        claim = self.env[CLAIM_MODEL].browse(claim_id)
        if not claim.exists():
            raise ClaimApiError(f"No existe el reclamo {claim_id}.", 404, "claim_not_found")
        return claim

    def _user_id(self, value: Any) -> int | bool:
        if value in (None, "", False):
            return False
        user_id = self._int_value(value, "user_id")
        if not self.env["res.users"].browse(user_id).exists():
            raise ClaimApiError("user_id inexistente.")
        return user_id

    def _check_company(self, value: Any) -> int:
        company_id = self._int_value(value, "company_id")
        company = self.env["res.company"].browse(company_id).exists()
        if not company:
            raise ClaimApiError("company_id inexistente.")
        if company not in self.env.user.company_ids:
            raise ClaimApiError(
                "company_id fuera de las empresas habilitadas.", 403, "forbidden_company"
            )
        return company.id

    def _parse_date(self, value: Any) -> str:
        try:
            parsed = fields.Date.to_date(value)
        except (TypeError, ValueError):
            parsed = None
        if not parsed:
            raise ClaimApiError("claim_date inválida, se espera YYYY-MM-DD.")
        return parsed.isoformat()

    def _int_value(
        self,
        value: Any,
        name: str,
        default: int | None = None,
        minimum: int | None = None,
        maximum: int | None = None,
    ) -> int | None:
        if value in (None, ""):
            return default
        try:
            number = int(value)
        except (TypeError, ValueError):
            raise ClaimApiError(f"{name} debe ser un entero.") from None
        if minimum is not None and number < minimum:
            raise ClaimApiError(f"{name} debe ser mayor o igual a {minimum}.")
        if maximum is not None and number > maximum:
            raise ClaimApiError(f"{name} debe ser menor o igual a {maximum}.")
        return number

    def _text(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    def _reject_unknown(self, payload: Any, allowed: frozenset[str]) -> None:
        if not isinstance(payload, dict):
            raise ClaimApiError("El cuerpo debe ser un objeto JSON.")
        unknown = sorted(set(payload) - allowed)
        if unknown:
            raise ClaimApiError(f"Campos desconocidos: {', '.join(unknown)}.")

    def _created(self, claim: Any, created: bool) -> dict[str, Any]:
        return {"id": claim.id, "number": claim.number or None, "created": created}
