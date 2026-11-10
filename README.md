# GEBICHART

Base Django 5.2 LTS para la gestión de bienes culturales histórico-artísticos.
Python 3.12 o posterior. Incluye acceso con usuarios locales, inicio con identidad
visual GEBICHART 3.0 y administración de usuarios/grupos de Django.

El inventario, ubicaciones y movimientos están pendientes de desarrollo.
No se incluyen datos de ejemplo ni conexión con MariaDB o Active Directory.

## Empezar en Codespaces o Dev Containers

Abre la rama `feature/gebichart-brand-v3` con **Code → Codespaces** o
**Dev Containers: Reopen in Container**. Tras integrar la PR, usa `main`.
La creación del contenedor ejecuta `scripts/setup.sh`.

## Empezar en local

```bash
bash scripts/setup.sh
source .venv/bin/activate
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

Abre `http://127.0.0.1:8000`. En Codespaces abre el puerto 8000 desde la pestaña
**Ports**, manteniendo su visibilidad **Private**. Si el navegador usa otro host,
añádelo explícitamente antes de arrancar, por ejemplo:

```bash
export DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1,${CODESPACE_NAME}-8000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
export DJANGO_CSRF_TRUSTED_ORIGINS="https://${CODESPACE_NAME}-8000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
python manage.py runserver 0.0.0.0:8000
```

El superusuario se crea de forma interactiva; no hay credenciales predeterminadas.
La administración está en `/admin/`. Los usuarios normales acceden al inicio;
solo usuarios con estado staff y los permisos correspondientes usan administración.
Cerrar sesión requiere POST con CSRF.

## Configuración

- `DJANGO_DEBUG`: `1` para desarrollo (valor predeterminado), `0` para producción.
- `DJANGO_SECRET_KEY`: obligatoria con DEBUG desactivado; introducir mediante el
  gestor de secretos del alojamiento, nunca en Git.
- `DJANGO_ALLOWED_HOSTS`: hosts permitidos separados por comas.
- `DJANGO_CSRF_TRUSTED_ORIGINS`: orígenes HTTPS autorizados, separados por comas,
  cuando se accede a través de un proxy como Codespaces.
- SQLite local: `db.sqlite3`, excluida de Git.

Esta configuración está preparada para desarrollo. Un despliegue de producción
requiere servidor WSGI/ASGI, HTTPS, gestión de estáticos, copias de seguridad y
configuración de base de datos. Con DEBUG desactivado se exige clave secreta,
se fuerza HTTPS y se activan cookies seguras. No se ha desplegado un servicio público.

## Comprobaciones

```bash
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
python manage.py collectstatic --noinput
ruff check config gebichart manage.py
```

GitHub Actions ejecuta esas comprobaciones en cada push y PR.
Las pruebas verifican acceso, autenticación, cierre de sesión, permisos de
administración, redirecciones seguras e integridad de los recursos originales.

## Identidad visual

Los recursos se sirven directamente desde
`GEBICHART_INTEGRACION_CODEX/marca_original/static/`, conservando sus bytes.
El CSS propio está en `gebichart/static/gebichart/css/app.css`; no modifica los
originales. Se utilizan Georgia, Segoe UI y Arial, sin fuentes propietarias.
El manual original se conserva intacto. No se incluyen fotografías decorativas.
