from odoo import api, fields, models


class CdaClaimSiniestro(models.Model):
    """Planilla de campo del ASV para siniestros.

    Se carga desde la pestaña "Siniestro (ASV)" del reclamo, que solo aparece
    cuando el tipo es Siniestros. Refleja la planilla en papel: el hecho,
    personas y vehículos, el bien dañado, quién intervino y el cierre.
    """

    _inherit = "cda.claim"

    es_siniestro = fields.Boolean(
        compute="_compute_es_siniestro",
        store=True,
        string="Es siniestro",
    )

    # ---------------------------------------------------------- 1. EL HECHO
    sin_fecha = fields.Date(string="Fecha del hecho")
    sin_hora = fields.Char(string="Hora")
    sin_ruta = fields.Char(string="Ruta")
    sin_sentido = fields.Selection(
        [("asc", "Ascendente"), ("desc", "Descendente")],
        string="Sentido",
    )
    sin_km = fields.Char(string="Kilómetro")
    sin_gps = fields.Char(string="GPS")
    sin_donde = fields.Selection(
        [
            ("calzada", "Calzada"),
            ("banquina", "Banquina"),
            ("talud", "Talud"),
            ("peaje", "Peaje"),
            ("acceso", "Acceso, retorno o cruce"),
            ("otro", "Otro"),
        ],
        string="Dónde",
    )
    sin_donde_otro = fields.Char(string="Dónde (otro)")

    sin_llegada = fields.Selection(
        [
            ("posicion_final", "Vehículos y restos en su posición final"),
            ("movidos", "Ya habían sido movidos"),
            ("fotos", "Fotos de posición final tomadas"),
        ],
        string="Al llegar",
    )
    sin_movidos_por = fields.Char(string="Movidos por")

    sin_que_se_ve = fields.Text(string="Qué se ve")

    sin_calzada = fields.Selection(
        [
            ("nada", "Nada"),
            ("animal", "Animal suelto"),
            ("marca", "Marca o señal visible"),
            ("objeto", "Objeto"),
            ("carga", "Carga caída"),
            ("otro", "Otro"),
        ],
        string="En la calzada",
    )
    sin_calzada_detalle = fields.Char(string="Detalle en la calzada")
    sin_animal_cantidad = fields.Integer(string="Cantidad de animales")
    sin_animal_estado = fields.Selection(
        [("vivo", "Vivo"), ("muerto", "Muerto")],
        string="Estado del animal",
    )
    sin_relato_tercero = fields.Text(string="Qué dijo o pidió un tercero")

    sin_calzada_estado = fields.Selection(
        [
            ("seca", "Seca"),
            ("mojada", "Mojada"),
            ("nieve", "Nieve o hielo"),
            ("barro", "Barro"),
        ],
        string="Calzada",
    )
    sin_luz = fields.Selection(
        [("dia", "Día"), ("noche", "Noche")],
        string="Luz",
    )
    sin_clima = fields.Selection(
        [
            ("lluvia", "Lluvia"),
            ("niebla", "Niebla"),
            ("viento", "Viento o zonda"),
            ("humo", "Humo"),
            ("ninguno", "Ninguno"),
        ],
        string="En el momento",
    )
    sin_senalizacion = fields.Selection(
        [("si", "Sí"), ("no", "No")],
        string="Señalización en el sector",
    )
    sin_obra = fields.Selection(
        [("si", "Sí"), ("no", "No")],
        string="Obra en el sector",
    )
    sin_evento_hora = fields.Char(string="Evento natural: empezó a las")
    sin_evento_alertas = fields.Selection(
        [("si", "Sí"), ("no", "No"), ("ns", "NS")],
        string="¿Había alertas?",
    )

    # ------------------------------------------- 2. PERSONAS Y VEHÍCULOS
    sin_conductor_nombre = fields.Char(string="Conductor: nombre")
    sin_conductor_domicilio = fields.Char(string="Conductor: domicilio")
    sin_conductor_telefono = fields.Char(string="Conductor: teléfono")
    sin_foto_ci = fields.Boolean(string="Foto del DNI")
    sin_foto_licencia = fields.Boolean(string="Foto de la licencia")

    sin_dominio = fields.Char(string="Dominio")
    sin_marca_modelo = fields.Char(string="Marca y modelo")
    sin_color = fields.Char(string="Color")
    sin_vehiculo_tipo = fields.Selection(
        [
            ("auto", "Auto"),
            ("camioneta", "Camioneta"),
            ("camion", "Camión"),
            ("moto", "Moto"),
            ("otro", "Otro"),
        ],
        string="Tipo de vehículo",
    )

    sin_titular = fields.Char(string="Titular")
    sin_aseguradora = fields.Char(string="Aseguradora")
    sin_poliza = fields.Char(string="Póliza")
    sin_foto_poliza = fields.Boolean(string="Foto de la póliza")

    sin_transportista = fields.Char(string="Transportista")
    sin_carga = fields.Char(string="Carga")
    sin_carga_peligrosa = fields.Boolean(string="Carga peligrosa")

    sin_ocupantes = fields.Integer(string="Cantidad de ocupantes")
    sin_cant_vehiculos = fields.Integer(string="Cantidad de vehículos")
    sin_uso_anexo = fields.Boolean(string="Se usó el anexo")

    sin_personal_propio_herido = fields.Boolean(string="Hay personal propio herido")
    sin_personal_propio_nombre = fields.Char(string="Personal propio herido: nombre")

    sin_vehiculo_ids = fields.One2many(
        "cda.claim.siniestro.vehiculo",
        "claim_id",
        string="Vehículos de terceros",
        help="Vehículos 2 y 3 de la planilla; si hay más, agregar filas.",
    )
    sin_herido_ids = fields.One2many(
        "cda.claim.siniestro.herido",
        "claim_id",
        string="Heridos",
    )

    # ------------------------------------------------------ 3. BIEN DAÑADO
    sin_bien = fields.Selection(
        [
            ("defensa", "Defensa o baranda"),
            ("poste", "Poste"),
            ("cartel", "Cartel"),
            ("portico", "Pórtico"),
            ("semaforo", "Semáforo"),
            ("calzada", "Calzada o banquina"),
            ("cabina", "Cabina o barrera"),
            ("peaje", "Equipo de peaje"),
            ("movil", "Móvil o vehículo propio"),
            ("otro", "Otro"),
        ],
        string="Qué bien",
    )
    sin_bien_otro = fields.Char(string="Bien (otro)")
    sin_bien_movil = fields.Char(string="N° de móvil")
    sin_bien_km = fields.Char(string="Km del bien")
    sin_bien_cantidad = fields.Char(string="Largo o cantidad aprox.")
    sin_bien_marcas = fields.Boolean(string="Marcas o restos en el bien")
    sin_bien_riesgo = fields.Selection(
        [("si", "Sí"), ("no", "No")],
        string="¿Riesgo para el tránsito?",
    )
    sin_bien_medida = fields.Text(string="Medida tomada")

    # -------------------------------------------- 4. QUIÉN INTERVINO Y CUÁNDO
    sin_policia = fields.Boolean(string="Policía")
    sin_gendarmeria = fields.Boolean(string="Gendarmería")
    sin_dependencia = fields.Char(string="Dependencia")
    sin_acta = fields.Char(string="Acta o exposición N°")
    sin_alcoholemia = fields.Selection(
        [("si", "Sí"), ("no", "No"), ("ns", "NS")],
        string="¿Control de alcoholemia?",
    )
    sin_alcoholemia_resultado = fields.Char(string="Resultado")
    sin_ambulancia = fields.Boolean(string="Ambulancia")
    sin_bomberos = fields.Boolean(string="Bomberos")
    sin_prensa = fields.Boolean(string="Prensa presente")
    sin_abogado = fields.Boolean(string="Abogado presente")
    sin_hora_novedad = fields.Char(string="Se recibe la novedad")
    sin_hora_grua = fields.Char(string="Llegó la grúa")
    sin_hora_fin = fields.Char(string="Finaliza")
    sin_cronologia = fields.Text(
        string="Cronología",
        help="Una línea por jornada: qué pasó y a qué hora.",
    )

    # ------------------------------------------------- 5. EVIDENCIA Y CIERRE
    sin_fotos_cantidad = fields.Integer(string="Cantidad de fotos")
    sin_originales = fields.Boolean(string="Originales enviados al centro")
    sin_originales_hora = fields.Char(string="Hora de envío")
    sin_parte_diario = fields.Boolean(string="Asentado en parte diario")
    sin_camaras = fields.Char(
        string="Cámaras cerca",
        help="Cuáles y qué se pidió al centro.",
    )
    sin_testigos = fields.Text(string="Testigos")
    sin_firma_asv = fields.Char(string="Firma ASV")
    sin_hora_cierre = fields.Char(string="Hora de cierre")

    # ------------------------------------------------------------------ ORM
    @api.depends("claim_type_id.code")
    def _compute_es_siniestro(self):
        for claim in self:
            claim.es_siniestro = (claim.claim_type_id.code or "") == "SIN"


class CdaClaimSiniestroVehiculo(models.Model):
    """Un vehículo de terceros de la planilla."""

    _name = "cda.claim.siniestro.vehiculo"
    _description = "Vehículo de tercero (planilla de siniestro)"
    _order = "sequence, id"

    claim_id = fields.Many2one(
        "cda.claim",
        string="Reclamo",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10)

    nombre_conductor = fields.Char(string="Conductor")
    telefono = fields.Char(string="Teléfono")
    domicilio = fields.Char(string="Domicilio")
    foto_ci = fields.Boolean(string="Foto DNI")
    foto_licencia = fields.Boolean(string="Foto licencia")

    dominio = fields.Char(string="Dominio")
    marca_modelo = fields.Char(string="Marca y modelo")
    color = fields.Char(string="Color")
    tipo = fields.Selection(
        [
            ("auto", "Auto"),
            ("camioneta", "Camioneta"),
            ("camion", "Camión"),
            ("moto", "Moto"),
            ("otro", "Otro"),
        ],
        string="Tipo",
    )

    titular = fields.Char(string="Titular")
    aseguradora = fields.Char(string="Aseguradora")
    poliza = fields.Char(string="Póliza")
    foto_poliza = fields.Boolean(string="Foto")

    transportista = fields.Char(string="Transportista")
    carga = fields.Char(string="Carga")
    carga_peligrosa = fields.Boolean(string="Carga peligrosa")


class CdaClaimSiniestroHerido(models.Model):
    """Una persona lesionada de la planilla."""

    _name = "cda.claim.siniestro.herido"
    _description = "Persona lesionada (planilla de siniestro)"
    _order = "sequence, id"

    claim_id = fields.Many2one(
        "cda.claim",
        string="Reclamo",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10)

    nombre = fields.Char(string="Nombre")
    gravedad = fields.Selection(
        [
            ("leve", "Leve"),
            ("grave", "Grave"),
            ("fallecido", "Fallecido"),
        ],
        string="Gravedad",
    )
    trasladado_a = fields.Char(string="Trasladado a")
    rechazo_asistencia = fields.Boolean(string="Rechazó asistencia")
    es_personal_propio = fields.Boolean(string="Es personal propio")
