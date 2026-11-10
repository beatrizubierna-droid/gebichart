# GEBICHART — Kit de integración en repositorio Django existente

Este paquete no es una versión modificada de GEBICHART: el código fuente del proyecto no estaba disponible al preparar el kit.

## Contenido
- `marca_original/`: copia sin cambios del ZIP de diseño facilitado, incluidos PDF, instrucciones, CSS, iconos SVG y PNG.
- `integracion/CODEX_TAREA_INTEGRACION.md`: tarea completa para ejecutar en Codex sobre el repositorio real.
- `integracion/EJEMPLO_BASE_DJANGO.html`: fragmento orientativo para plantilla base; adaptar a rutas y bloques existentes, NO reemplazar base.html ciegamente.
- `integracion/validar_recursos.py`: validación hash SHA-256 de la copia de los recursos originales.

## Uso
1. Añadir estos archivos al repositorio privado `gebichart` o facilitar su contenido a Codex. No subir datos municipales sensibles.
2. En Codex abrir repositorio y pedir: «Lee `integracion/CODEX_TAREA_INTEGRACION.md` y aplícalo a la rama actual. Revisa primero el manual y las instrucciones de marca». 
3. Revisar PR, lista de archivos, pruebas y capturas. No dar por verificada la integridad de MariaDB, AD o permisos si no se ha probado en un entorno real autorizado.
