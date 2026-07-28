# bsky-bridge

Una librería de Python para la API de la red social BlueSky.

[![PyPI version](https://badge.fury.io/py/bsky-bridge.svg)](https://pypi.org/project/bsky-bridge/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Características

- Autenticación sencilla con persistencia automática de sesión
- Renovación automática de tokens y manejo de límites de tasa (rate limits)
- Publicación de texto con menciones, enlaces y hashtags (detección automática)
- Publicación de hasta 4 imágenes por post con soporte para texto alternativo (alt text)
- Optimización automática de imágenes (redimensionamiento, compresión, eliminación de EXIF)
- Especificación de idioma para publicaciones multilingües
- Controles de respuesta (threadgate) - restringe quién puede responder a tus publicaciones

## Instalación

```bash
pip install bsky-bridge
```

## Inicio Rápido

```python
from bsky_bridge import BskySession, post_text

session = BskySession("tu_usuario.bsky.social", "tu_contraseña_de_app")
post_text(session, "¡Hola BlueSky!")
```

## Uso

### Autenticación

Crea una sesión utilizando tu usuario de BlueSky y una [Contraseña de Aplicación](https://bsky.app/settings/app-passwords) (no uses tu contraseña principal):

```python
from bsky_bridge import BskySession

session = BskySession("tu_usuario.bsky.social", "tu_contraseña_de_app")
```

Las sesiones se guardan automáticamente en `.bsky_sessions/` y se reutilizan. Para usar un directorio personalizado:

```python
session = BskySession("tu_usuario.bsky.social", "tu_contraseña_de_app", session_dir="/ruta/a/sesiones")
```

### Publicar Texto

```python
from bsky_bridge import BskySession, post_text

session = BskySession("tu_usuario.bsky.social", "tu_contraseña_de_app")

# Publicación simple
post_text(session, "¡Hola BlueSky!")

# Las menciones, enlaces y hashtags se detectan automáticamente
post_text(session, "Hey @amigo.bsky.social mira esto https://ejemplo.com #programacion")
```

### Publicar una Sola Imagen

```python
from bsky_bridge import BskySession, post_image

session = BskySession("tu_usuario.bsky.social", "tu_contraseña_de_app")

post_image(
    session,
    "¡Mira esta foto!",
    "/ruta/a/imagen.jpg",
    alt_text="Un hermoso atardecer"
)
```

### Publicar Múltiples Imágenes

Publica hasta 4 imágenes en un solo post:

```python
from bsky_bridge import BskySession, post_images

session = BskySession("tu_usuario.bsky.social", "tu_contraseña_de_app")

post_images(session, "¡Mi galería de fotos!", [
    {"path": "/ruta/a/imagen1.jpg", "alt": "Primera imagen"},
    {"path": "/ruta/a/imagen2.jpg", "alt": "Segunda imagen"},
    {"path": "/ruta/a/imagen3.jpg", "alt": "Tercera imagen"},
    {"path": "/ruta/a/imagen4.jpg", "alt": "Cuarta imagen"},
])
```

### Especificar Idiomas

Ayuda a los algoritmos de feed de BlueSky especificando los idiomas del post:

```python
from bsky_bridge import post_text, post_image

# Publicación de texto multilingüe
post_text(session, "Bonjour! Hello!", langs=["fr", "en-US"])

# Publicación de imagen con idiomas
post_image(
    session,
    "Belle photo! Beautiful photo!",
    "/ruta/a/imagen.jpg",
    alt_text="Paisaje",
    langs=["fr", "en-US"]
)
```

### Controles de Respuesta (Threadgate)

Controla quién puede responder a tus publicaciones utilizando el parámetro `reply_to`:

```python
from bsky_bridge import post_text

# Nadie puede responder
post_text(session, "Esto es una declaración.", reply_to="nobody")

# Solo los usuarios mencionados pueden responder
post_text(session, "Hey @amigo.bsky.social ¿qué piensas?", reply_to="mentions")

# Solo las personas a las que sigues pueden responder
post_text(session, "Pregunta para mis amigos", reply_to="following")

# Solo tus seguidores pueden responder
post_text(session, "Discusión solo para seguidores", reply_to="followers")

# Combinar múltiples reglas
post_text(session, "Discusión limitada", reply_to=["mentions", "following"])
```

Opciones disponibles:

| Opción | Descripción |
|--------|-------------|
| `None` | Cualquiera puede responder (por defecto) |
| `"nobody"` | Nadie puede responder |
| `"mentions"` | Solo usuarios mencionados |
| `"following"` | Solo personas a las que sigues |
| `"followers"` | Solo tus seguidores |
| `["option1", "option2"]` | Combinar múltiples reglas |

Funciona con todas las funciones de publicación (`post_text`, `post_image`, `post_images`).

### Realizar Llamadas Personalizadas a la API

Usa la sesión para realizar llamadas autenticadas a cualquier endpoint del AT Protocol:

```python
# Solicitud GET
profile = session.api_call(
    "app.bsky.actor.getProfile",
    method="GET",
    params={"actor": "alguien.bsky.social"}
)

# Solicitud POST
session.api_call(
    "com.atproto.repo.createRecord",
    method="POST",
    json={
        "repo": session.did,
        "collection": "app.bsky.feed.like",
        "record": {
            "$type": "app.bsky.feed.like",
            "subject": {"uri": "at://...", "cid": "..."},
            "createdAt": "2024-01-01T00:00:00Z"
        }
    }
)
```

### Cerrar Sesión

```python
session.logout()  # Borra los tokens y elimina el archivo de sesión
```

## Manejo de Imágenes

Las imágenes se procesan automáticamente antes de la subida:

| Característica | Detalles |
|----------------|----------------------------------------------------------|
| Tamaño máximo | 1 MB (se comprime automáticamente si es mayor) |
| Dimensiones máx | 3840x2160 (se redimensiona automáticamente si es mayor) |
| Datos EXIF | Se eliminan automáticamente por privacidad |
| Relación de aspecto | Se preserva y se envía a la API |
| Formatos | JPEG, PNG (se preserva la transparencia) |

## Límites de Tasa (Rate Limiting)

La librería maneja automáticamente los límites de tasa de BlueSky:

- Detecta respuestas HTTP 429
- Lee los encabezados `Retry-After` y `RateLimit-Reset`
- Implementa un retroceso exponencial (exponential backoff) (1s, 2s, 4s...)
- Reintenta hasta 3 veces antes de lanzar un error

## Referencia de la API

### BskySession

```python
BskySession(handle: str, app_password: str, session_dir: str = None)
```

| Método | Descripción |
|--------|-------------|
| `api_call(endpoint, method, json, data, headers, params)` | Realiza una llamada a la API autenticada |
| `get_auth_header()` | Obtiene el diccionario del encabezado de Autorización |
| `logout()` | Cierra la sesión y borra los tokens almacenados |

### Funciones

| Función | Descripción |
|----------|-------------|
| `post_text(session, text, langs=None, reply_to=None)` | Publica contenido de texto |
| `post_image(session, text, image_path, alt_text="", langs=None, reply_to=None)` | Publica una sola imagen |
| `post_images(session, text, images, langs=None, reply_to=None)` | Publica hasta 4 imágenes |
| `set_threadgate(session, post_uri, reply_to)` | Establece controles de respuesta en un post existente |

## Contribuciones

¡Las contribuciones son bienvenidas! Por favor, envía issues para errores y pull requests para nuevas funcionalidades.

## Licencia

[MIT License](LICENSE)
