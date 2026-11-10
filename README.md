# GEBICHART

Aplicación Django 5.2 LTS para gestionar bienes culturales histórico-artísticos.
Python 3.12 o posterior, SQLite local para desarrollo e identidad GEBICHART 3.0.

## Funciones disponibles

- Acceso con usuarios y contraseñas locales, cierre de sesión protegido por CSRF.
- Inventario: listado paginado, búsqueda por código/título/autoría/ubicación y
  filtros por tipo y estado de conservación.
- Ficha de obra, alta y edición según los permisos de cada usuario.
- Código de inventario único, título y tipo obligatorios. Autoría, técnica,
  datación, dimensiones, ubicación, descripción y observaciones opcionales.
  La conservación parte de «Sin evaluar».
- Administración Django de obras, usuarios y grupos.

La ubicación actual es texto libre (edificio, planta y sala). El catálogo de
ubicaciones, fotografías, movimientos, cesiones e informes son próximos módulos.
No se incluyen datos municipales ni conexiones MariaDB/Active Directory.

## Primera instalación

Abre `main` con **Code → Codespaces** o **Dev Containers: Reopen in Container**
una vez integrada la PR. Para probar cambios pendientes, selecciona su rama.
El contenedor ejecuta `scripts/setup.sh` automáticamente.

En la terminal del proyecto:

```bash
bash scripts/setup.sh
source .venv/bin/activate
python manage.py migrate
python manage.py crear_roles
python manage.py createsuperuser
bash scripts/dev.sh
```

Crea el superusuario interactivamente: no hay credenciales predeterminadas.
Abre `http://127.0.0.1:8000` o el puerto **8000** en **Ports** de Codespaces.
Mantén su visibilidad **Private**.

## Actualizar una instalación existente

En una copia de trabajo limpia, desde `main` después de integrar los cambios:

```bash
git pull --ff-only
bash scripts/dev.sh
```

El script crea el entorno virtual si falta, aplica las migraciones, prepara los
grupos y arranca Django. Conserva los datos de SQLite existentes; no borres
`db.sqlite3`. Detén un servidor anterior con **Ctrl+C** antes de arrancarlo.

El script configura los hosts y orígenes de desarrollo exactos para Codespaces
y `https://localhost:8000` / `https://127.0.0.1:8000`, manteniendo CSRF activo.
Respeta los valores de entorno que ya hayas definido. Si conservas una configuración
antigua incorrecta, ejecuta antes:

```bash
unset DJANGO_ALLOWED_HOSTS DJANGO_CSRF_TRUSTED_ORIGINS
bash scripts/dev.sh
```

Después de cambiar orígenes, recarga la página de acceso antes de enviar el formulario.

## Usuarios y permisos

Con el superusuario, entra en `/admin/` y asigna grupos a cada usuario:

| Grupo | Permisos en el inventario |
| --- | --- |
| Consulta inventario | Consultar listado y fichas |
| Gestión inventario | Consultar, añadir y editar obras |

`python manage.py crear_roles` es idempotente: prepara los grupos y no asigna
usuarios. No concede permiso de borrado. Para usar el inventario no hace falta
marcar «Es parte del personal» (staff); este estado solo habilita la entrada a
administración, donde además se comprueban los permisos de cada modelo.
Un usuario sin permisos de inventario solo puede acceder al inicio.

## Configuración

- `DJANGO_DEBUG`: `1` para desarrollo (predeterminado), `0` para producción.
- `DJANGO_SECRET_KEY`: obligatoria con DEBUG desactivado; introducir mediante el
  gestor de secretos del alojamiento, nunca en Git.
- `DJANGO_ALLOWED_HOSTS`: hosts permitidos separados por comas.
- `DJANGO_CSRF_TRUSTED_ORIGINS`: orígenes HTTPS autorizados separados por comas.
- SQLite local: `db.sqlite3`, excluida de Git.

Esta configuración es de desarrollo. Producción requiere servidor WSGI/ASGI,
HTTPS, gestión de estáticos, copias de seguridad y configuración de base de datos.
Con DEBUG desactivado se exige clave secreta, se fuerza HTTPS y se activan cookies
seguras. No se ha desplegado un servicio público.

## Comprobaciones

```bash
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
python manage.py collectstatic --noinput
ruff check config gebichart manage.py
```

GitHub Actions ejecuta esas comprobaciones en cada push y PR. Las pruebas cubren
acceso, permisos de consulta/alta/edición, validación, códigos duplicados,
búsqueda y filtros, paginación, escape de contenido, CSRF y recursos originales.

## Identidad visual

Los recursos se sirven directamente desde
`GEBICHART_INTEGRACION_CODEX/marca_original/static/`, conservando sus bytes.
El CSS propio está en `gebichart/static/gebichart/css/app.css`. Se utilizan Georgia,
Segoe UI y Arial, sin fuentes propietarias. El manual se conserva intacto.

Las capturas de `docs/screenshots/inventario-*`, `ficha-*` y `formulario-*`
contienen únicamente datos ficticios de revisión, que no se cargan en la base
de datos de la aplicación. Las capturas `home-*` y `login-desktop.jpg` documentan
la primera versión.
