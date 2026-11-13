# cda_chatbot — Grafo del chatbot

Módulo Odoo 19 que guarda el **árbol de preguntas y respuestas** del chatbot y lo
publica compilado a JSON para que el sitio lo consuma.

No reimplementa reclamos: los que deja el usuario son `cda.claim` con el medio de
entrada **BOT**, así que caen en la bandeja de siempre.

## Requisitos

- Odoo 19 con `cda_claims` y `cda_api` instalados.

## Instalación

```bash
odoo-bin -c odoo.conf -d <db> -i cda_chatbot --stop-after-init
```

Menú: **Reclamos → Configuración → Chatbot**.

## Cómo se arma el grafo

Un nodo **es** una opción dentro de su padre:

- `Etiqueta` → el texto del botón.
- `Mensaje` → lo que dice el bot al entrar.
- `Opciones` → los hijos, que son los botones que ofrece.

El primer nodo que se crea (sin padre) es la raíz: el mensaje inicial.

### Árbol inicial

El módulo trae cargado un árbol de arranque en `data/chatbot_arbol.xml`, armado
sobre el análisis del bot de Corresur y con los datos reales del sitio:

```
Inicio
├── 🚨 Emergencias            → 140
├── 🛣 Estado de la ruta      → Ruta 7 · Ruta 40
├── 💰 Tarifas y TelePASE    → Cuadro tarifario (10 categorías) · Adherir TelePASE
├── 🧭 Tu viaje               → Asistencia · Sectores de detención · Peajes
└── 🎧 Atención y reclamos    → 0800 · WhatsApp · Correo · Dejar un reclamo
```

27 nodos, 4 niveles. Está con `noupdate="1"`: se carga una vez y desde ahí se
edita desde la UI, sin que un `-u` pise los cambios.

### Tipos de nodo

| `kind` | Qué hace | Campos que usa |
|---|---|---|
| `menu` | Muestra sus opciones | `child_ids` (obligatorio tener al menos una activa) |
| `message` | Solo habla | `message` |
| `link` | Abre una URL | `url` |
| `phone` | Llama | `phone` |
| `whatsapp` | Abre WhatsApp | `phone`, `whatsapp_message` |
| `claim` | Pide los datos del reclamo | `claim_type_id`, `subtype_id`, `detail_id` |

`allow_back` decide si el widget ofrece «volver al menú» desde ese nodo.

### Validaciones

**Al guardar** (nodo por nodo):

- una sola raíz;
- un hijo no puede colgar de una acción (`link`, `phone`, `whatsapp`, `claim`);
- `link` sin URL, `phone`/`whatsapp` sin teléfono, `claim` sin tipo o subtipo;
- `code` único;
- sin ciclos (Odoo además lo bloquea por `_parent_store`).

**Al publicar** (`_check_tree`, sobre el árbol entero):

- que exista raíz y sea una sola;
- que ningún `menu` quede sin opciones activas.

La diferencia importa: un menú vacío **se puede guardar** mientras armás el árbol,
porque al crearlo todavía no tiene hijos. Lo que no se puede es **publicarlo**.

## Publicar

`Publicar` compila el árbol activo y guarda una **versión inmutable** en
`cda.chatbot.publication`. Editar nodos después **no** cambia lo que ve el sitio
hasta la próxima publicación.

Las versiones anteriores quedan guardadas y se pueden volver a poner en línea
desde la lista de publicaciones.

## API

Ambos endpoints viven bajo `/api/v1` y usan la autenticación de `cda_api`
(Bearer con API key, o el usuario de servicio si `require_auth` está apagado).

### `GET /api/v1/chatbot/tree`

Devuelve el JSON de la publicación en línea.

```
ETag: "v7"
Cache-Control: public, max-age=300
```

Si mandás `If-None-Match: "v7"` responde `304`. Sin publicación: `404 no_publication`.

### `POST /api/v1/chatbot/claim`

```json
{
  "node": "reclamo",
  "subject": "Consulta por tarifas",
  "description": "No encuentro la tarifa de la categoría 2",
  "name": "Juan Pérez",
  "email": "juan@ejemplo.com",
  "phone": "2615555555",
  "session": "s-8f2c1a",
  "path": "Inicio > Tarifas y TelePASE > Categoría 1",
  "abandon_node": "tarifas.cat1",
  "transcript": "Bot: Hola...\nUsuario: tarifas...",
  "origin": "https://caminosdelaconcagua.com.ar/tarifas",
  "external_ref": "s-8f2c1a-1730000000"
}
```

- `node` (obligatorio): código de un nodo `claim`. **De ahí sale la taxonomía**
  (tipo, subtipo, detalle), no del widget: el grafo manda.
- `external_ref` es idempotente: si se repite, devuelve el reclamo existente.

Respuesta `201`:

```json
{ "id": 42, "number": "BOT-TP-REC-00042", "stage": "Abierto", "created": true }
```

## Contrato del JSON publicado

```json
{
  "version": 1,
  "root": {
    "code": "raiz",
    "label": "Inicio",
    "kind": "menu",
    "message": "Hola. Soy tu asistente de viaje.",
    "back": false,
    "options": [
      {
        "code": "emergencias",
        "label": "🚨 Emergencias",
        "kind": "phone",
        "message": "Para asistencia inmediata llamá al Centro de Control.",
        "back": true,
        "phone": "140"
      },
      {
        "code": "tarifas",
        "kind": "menu",
        "message": "¿Qué necesitás?",
        "back": true,
        "options": [
          {
            "code": "tarifas.telepase",
            "label": "Adherir TelePASE",
            "kind": "link",
            "message": "",
            "back": true,
            "url": "https://www.telepase.com.ar/"
          }
        ]
      },
      {
        "code": "reclamo",
        "label": "✉️ Dejar un reclamo",
        "kind": "claim",
        "message": "Dejanos tu mail y te contactamos.",
        "back": true,
        "claim": { "type": "REC", "subtype": "TP", "detail": null }
      }
    ]
  }
}
```

Un árbol de 9 nodos ocupa ~1,3 KB; uno de 40 ronda los 6 KB, así que el widget
puede guardarlo en `localStorage` y no volver a pedirlo hasta que cambie la versión.

## Trazabilidad en el reclamo

`cda.claim` suma, solo para los reclamos del chat:

| Campo | Qué guarda |
|---|---|
| `chat_session` | identificador de la conversación |
| `chat_node_id` | nodo donde el usuario **se rindió** |
| `chat_path` | camino recorrido, legible |
| `chat_transcript` | la conversación |
| `chat_origin` | URL de origen |

En el formulario del reclamo aparece la pestaña **Chat** solo cuando el reclamo
vino del chatbot, y el buscador suma el filtro **Desde el chatbot**.

El dato más valioso es `chat_node_id`: agrupando por ese campo se ve en qué parte
del árbol se cae la gente, que es lo que dice qué le falta al grafo.
