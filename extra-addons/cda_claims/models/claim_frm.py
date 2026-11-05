from odoo import fields, models


class CdaClaimForm(models.Model):
    _inherit = "cda.claim"

    currency_id = fields.Many2one(related="company_id.currency_id")

    den_nombre = fields.Char(string="Nombre y apellido")
    den_caracter = fields.Selection(
        [
            ("driver_owner", "Conductor y titular"),
            ("driver", "Conductor (no titular)"),
            ("owner", "Titular (no conducía)"),
            ("agent", "Apoderado / representante"),
        ],
        string="Carácter",
    )
    den_doc_tipo = fields.Selection(
        [
            ("dni", "DNI"),
            ("passport", "Pasaporte"),
            ("rut", "RUT (Chile)"),
            ("foreign_id", "Cédula extranjera"),
            ("other", "Otro"),
        ],
        string="Tipo de documento",
    )
    den_doc_num = fields.Char(string="N° de documento")
    den_nacionalidad = fields.Char(string="Nacionalidad")
    den_localidad = fields.Char(string="Localidad / provincia")

    den_vehicle_type = fields.Selection(
        [
            ("car", "Automóvil"),
            ("suv", "Camioneta / SUV"),
            ("van", "Utilitario / furgón"),
            ("truck", "Camión"),
            ("bus", "Colectivo / minibús"),
            ("moto", "Motocicleta"),
            ("trailer", "Casa rodante / acoplado"),
            ("other", "Otro"),
        ],
        string="Tipo de vehículo",
    )
    den_make = fields.Char(string="Marca")
    den_model = fields.Char(string="Modelo")
    den_plate = fields.Char(string="Dominio (patente)")
    den_year = fields.Integer(string="Año")
    den_tires = fields.Char(
        string="Medida de neumáticos",
        help="Ej.: 205/55 R16 91V",
    )
    den_owner = fields.Char(string="Titular registral")
    den_insurer = fields.Char(string="Compañía de seguros")
    den_policy = fields.Char(string="N° de póliza")

    den_driver_name = fields.Char(string="Nombre y apellido del conductor")
    den_driver_doc = fields.Char(string="Documento del conductor")
    den_driver_license = fields.Char(string="Licencia de conducir")

    den_time = fields.Char(string="Hora aproximada")
    den_km = fields.Char(string="Kilómetro aproximado")
    den_direction = fields.Selection(
        [
            ("ew", "Este → Oeste (hacia Uspallata / Chile)"),
            ("we", "Oeste → Este (hacia Mendoza / San Luis)"),
        ],
        string="Sentido de circulación",
    )
    den_lane = fields.Selection(
        [
            ("right", "Derecho"),
            ("left", "Izquierdo / sobrepaso"),
            ("shoulder", "Banquina"),
            ("single", "Único por sentido"),
        ],
        string="Carril",
    )
    den_reference = fields.Char(
        string="Ubicación de referencia",
        help="Localidad, paraje, calle o punto cercano.",
    )
    den_coords = fields.Char(
        string="Coordenadas o enlace de Google Maps",
        help="Ej.: -33.0906, -68.9703 o un enlace de Maps.",
    )

    den_light = fields.Selection(
        [
            ("day", "Día"),
            ("night", "Noche"),
            ("twilight", "Amanecer / atardecer"),
        ],
        string="Luz",
    )
    den_weather = fields.Selection(
        [
            ("clear", "Despejado"),
            ("cloudy", "Nublado"),
            ("rain", "Lluvia"),
            ("snow", "Nieve / hielo"),
            ("fog", "Niebla"),
            ("wind", "Viento fuerte"),
        ],
        string="Clima",
    )
    den_speed = fields.Char(string="Velocidad aproximada (km/h)")
    den_signage = fields.Selection(
        [
            ("no", "No"),
            ("yes", "Sí"),
            ("unsure", "No recuerda"),
        ],
        string="¿Había señalización del peligro?",
    )
    den_occupants = fields.Integer(
        string="Ocupantes del vehículo",
        help="Cantidad, incluido el conductor.",
    )
    den_injured = fields.Selection(
        [("no", "No"), ("yes", "Sí")],
        string="¿Hubo personas lesionadas?",
    )
    den_injury_detail = fields.Char(string="Detalle de lesiones y atención")

    den_damage_tire = fields.Boolean(string="Neumático / cubierta")
    den_damage_rim = fields.Boolean(string="Llanta")
    den_damage_alignment = fields.Boolean(string="Tren delantero / alineación")
    den_damage_suspension = fields.Boolean(
        string="Amortiguadores / suspensión"
    )
    den_damage_axle = fields.Boolean(string="Palier / transmisión")
    den_damage_body = fields.Boolean(string="Carrocería / paragolpes")
    den_damage_underbody = fields.Boolean(string="Bajos / cárter")
    den_damage_other = fields.Boolean(string="Otro daño")

    den_position_fl = fields.Boolean(string="Delantera izq.")
    den_position_fr = fields.Boolean(string="Delantera der.")
    den_position_rl = fields.Boolean(string="Trasera izq.")
    den_position_rr = fields.Boolean(string="Trasera der.")

    den_damage_detail = fields.Text(string="Detalle de los daños")
    den_amount = fields.Monetary(
        string="Monto reclamado o estimado",
        currency_field="currency_id",
    )
    den_repaired = fields.Selection(
        [
            ("no", "No"),
            ("yes", "Sí"),
            ("partial", "Parcialmente"),
        ],
        string="¿Ya reparó o reemplazó?",
    )
    den_inspection_available = fields.Selection(
        [("yes", "Sí"), ("no", "No")],
        string="¿Vehículo y piezas disponibles para inspección?",
    )
    den_inspection_where = fields.Char(
        string="Dónde y cuándo puede inspeccionarse",
        help="Domicilio, gomería o taller y horario.",
    )

    den_toll_ticket = fields.Selection(
        [
            ("yes", "Sí"),
            ("no", "No"),
            ("telepase", "Paga con TelePASE"),
        ],
        string="¿Conserva el comprobante de peaje?",
    )
    den_toll_detail = fields.Char(string="Estación, fecha y hora del pago")
    den_police_report = fields.Selection(
        [("yes", "Sí"), ("no", "No")],
        string="¿Hizo denuncia policial o en fiscalía?",
    )
    den_police_detail = fields.Char(string="Dependencia, fecha y número")

    den_help_staff = fields.Boolean(string="Personal de la concesionaria")
    den_help_crane = fields.Boolean(string="Grúa / remolque")
    den_help_insurer = fields.Boolean(string="Auxilio de su aseguradora")
    den_help_police = fields.Boolean(string="Policía / Gendarmería")
    den_help_none = fields.Boolean(string="Ninguna")

    den_witnesses = fields.Char(
        string="Testigos",
        help="Nombre y contacto.",
    )
    den_third_parties = fields.Char(
        string="Otros vehículos involucrados",
        help="Dominio, conductor, aseguradora.",
    )

    den_sworn = fields.Boolean(
        string="Declaro bajo juramento que los datos son verdaderos",
    )
    den_data_consent = fields.Boolean(
        string="Presto consentimiento para el tratamiento de mis datos (Ley 25.326)",
    )
