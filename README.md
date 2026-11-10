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
- Galería por obra: selección múltiple al crear/editar y subida adicional desde
  la ficha, apertura de originales y eliminación con confirmación.
- Catálogo de edificios, plantas y ubicaciones, con alta/edición y consulta
  de las obras asignadas a cada espacio.
- Administración Django de obras, ubicaciones, usuarios y grupos.

La ubicación actual puede vincularse al catálogo. El texto libre anterior se
conserva como referencia. Movimientos, cesiones e informes son próximos módulos.
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

El script crea el entorno virtual si falta, instala las dependencias actualizadas,
aplica las migraciones y prepara los
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
| Consulta inventario | Consultar obras y catálogo de ubicaciones |
| Gestión inventario | Consultar, añadir y editar obras, edificios, plantas y ubicaciones |

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

## Galería de imágenes

En **Añadir obra** y **Editar ficha** puedes seleccionar varias fotografías.
También puedes abrir una ficha y usar **Galería de imágenes → Seleccionar imágenes
→ Subir imágenes**. La descripción opcional se aplica al conjunto seleccionado.
Al editar sin seleccionar nuevos archivos se conservan todas las imágenes existentes.
Para eliminar una imagen, utiliza su enlace **Eliminar imagen** y confirma la acción.
Selecciona la miniatura para abrir el original en otra pestaña.

- Formatos admitidos: JPG, PNG y WebP, comprobados por contenido con Pillow.
- Límites: 10 MB y 40 megapíxeles por imagen; 10 archivos y 50 MB por envío.
- Consulta: permiso `view_obra`. Subida/eliminación en una obra existente:
  `view_obra` + `change_obra`. Durante el alta, basta con `view_obra` + `add_obra`.
  Los grupos existentes ya incluyen los permisos correspondientes.
- Las imágenes se guardan en `media/`, fuera de Git, con nombres aleatorios.
  Se conservan los bytes originales y no se alteran las fotografías.
- Los archivos se sirven mediante rutas protegidas de la aplicación, también
  para lectores. No existe una ruta pública `/media/`.
- Las eliminaciones borran el archivo después de confirmar la transacción;
  una subida fallida revierte los registros y limpia los archivos escritos.
- En administración Django, guarda la obra y utiliza **Ver y gestionar fotografías**
  para abrir la galería de la ficha.

Al actualizar, `bash scripts/dev.sh` instala Pillow y aplica la nueva migración.
Recarga la ficha después de reiniciar el servidor. Las copias de seguridad deben
incluir `db.sqlite3` **y** `media/`. El almacenamiento de un Codespace es de desarrollo;
para producción se necesita almacenamiento persistente y acceso privado equivalente.

Las capturas `docs/screenshots/galeria-1440.jpg` y `galeria-375.jpg` muestran
la galería con imágenes sintéticas de prueba, sin obras ni datos reales.

## Edificios, plantas y ubicaciones

1. Entra en **Ubicaciones → Añadir edificio** y registra su código, nombre y,
   opcionalmente, dirección y descripción.
2. En el edificio pulsa **Añadir planta**. El orden permite situar sótanos
   antes de la planta baja y las plantas superiores.
3. En una planta pulsa **Añadir ubicación** para registrar una sala, depósito
   u otro espacio. Puedes abrir su ficha para consultar las obras asignadas.
4. En **Editar ficha** de una obra, selecciona **Ubicación del catálogo**.
   También puedes utilizar **Añadir obra aquí** desde la ficha de un espacio.

La ubicación en texto libre se mantiene exactamente como estaba. No se intentan
interpretar ni convertir automáticamente las ubicaciones anteriores. Si seleccionas
un espacio del catálogo, su ruta completa pasa a ser la ubicación actual y el
texto previo sigue apareciendo como referencia. Quitar la selección del catálogo
vuelve a mostrar el texto libre. Las fotografías y los otros datos se conservan.

El inventario permite buscar por edificio, planta o espacio y filtrar por edificio.
El catálogo se puede buscar por código/nombre del edificio, dirección, planta o espacio.
Las listas de edificios y de obras de un espacio tienen paginación.

Los códigos de edificio son únicos; los nombres de plantas no pueden repetirse
dentro del mismo edificio, ni los nombres de espacios dentro de una planta.
Al editar se pueden corregir etiquetas y descripciones, pero no cambiar el edificio
de una planta existente ni la planta de un espacio existente. Para ubicar una obra
en otro lugar, edita la ubicación del catálogo en su ficha. El historial de movimientos
se incorporará en su propio módulo.

La base de datos protege de borrado los edificios con plantas, las plantas con
espacios y los espacios con obras asignadas. Los grupos de consulta/gestión se
actualizan con `python manage.py crear_roles`, ejecutado automáticamente por
`bash scripts/dev.sh`; se conservan las pertenencias de los usuarios y no se conceden
permisos de borrado. La gestión del catálogo también está disponible en administración.

Las capturas `ubicaciones-1440.jpg`, `ubicaciones-375.jpg`, `espacio-1440.jpg` y
`espacio-375.jpg` de `docs/screenshots/` muestran datos ficticios de revisión.
