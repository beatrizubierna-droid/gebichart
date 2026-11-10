# Tarea para Codex — integración de identidad GEBICHART 3.0

Trabaja SOBRE EL REPOSITORIO EXISTENTE. Proyecto GEBICHART, paquete de configuración `config`, aplicación principal Django `gebichart`, base de datos MariaDB `gebichart_db`. No renombres apps ni alteres rutas, modelos, migraciones, conexiones o funciones existentes.

## Primero, inspeccionar
1. Leer íntegramente `marca_original/documentation/Manual_Imagen_Corporativa_GEBICHART_3.0.pdf` y `marca_original/instructions/CODEX_INSTRUCCIONES.md`.
2. Inventariar todas las plantillas, rutas, vistas, formularios, administración Django y archivos estáticos actuales. Determinar si existen plantillas base compartidas; preservar los bloques y nombres de URL reales.
3. Comprobar estado de Git y crear una rama de trabajo `feature/gebichart-brand-v3`. No sobrescribir modificaciones sin revisar.

## Identidad visual
4. Copiar `marca_original/static/gebichart/` a la carpeta estática apropiada manteniendo EXACTAMENTE los bytes de cada archivo. Usar `gebichart-isotipo-aprobado.png` o la variante transparente incluida, sin redibujar, retocar, recortar, aplicar filtros ni cambiar proporciones. Comprobar SHA-256 antes/después.
5. Con `{% load static %}` cargar `gebichart/css/components.css` (que importa tokens.css) en la plantilla base; favicons y `site.webmanifest` mediante rutas `{% static %}`. Incluir viewport, lang=es, skip link y navegación semántica.
6. Aplicar iconos originales SVG del paquete mediante rutas `{% static 'gebichart/icons/...' %}`. Tener presente que un SVG en `<img>` no adquiere el `currentColor` del padre; para iconos que necesiten color variable usar inclusión SVG revisada con seguridad o utilizar color/color de fondo apropiado, sin cambiar los originales.
7. Reutilizar clases `gch-*` y añadir CSS mínimo y localizado solo donde haga falta. Evitar CSS que rompa componentes de administración. Mantener responsive, contraste, estados de foco, etiquetas, tabulación, `prefers-reduced-motion` y texto alternativo adecuado.
8. Asegurar identidad uniforme en: inicio/dashboard, inventario, listado y detalle/ficha de obra, altas y edición, edificios, plantas, ubicaciones, cesiones, devoluciones, movimientos, informes, usuarios y administración si esas páginas existen. No inventar módulos funcionales inexistentes.
9. No incluir fotografías decorativas de monumentos ni modificar el manual; utilizar exclusivamente recursos del kit. Las fotografías documentales de las obras almacenadas por la propia aplicación se conservan donde correspondan.
10. No incorporar archivos de fuentes propietarias sin licencia: Georgia/Segoe UI/Arial como fuentes de respaldo y las fuentes corporativas solo si están legalmente disponibles.

## Invariantes y pruebas
11. No modificar modelos/migraciones MariaDB, autenticación LDAP/Active Directory, roles, permisos, middleware, rutas ni lógica de negocio salvo una adaptación estrictamente necesaria y explicada. No publicar ni transferir datos reales.
12. Ejecutar `python manage.py check`, pruebas automatizadas existentes, `python manage.py collectstatic --noinput` en entorno seguro de pruebas (si aplica); verificar enlaces de recursos CSS, favicon y SVG y que no hay errores 404. Si no hay entorno o dependencias, declararlo y no inventar resultados.
13. Revisar visualmente escritorio (1440 px) y móvil (375 px) y navegación por teclado en todas las pantallas existentes. Si hay infraestructura Playwright, capturas y pruebas visuales. Verificar que imágenes del isotipo conservan aspect-ratio.
14. Generar PR con lista exacta de archivos añadidos/modificados, capturas antes/después, resultados de pruebas, incidencias y confirmación de que las comprobaciones de permisos/AD/MariaDB requieren entorno municipal si no está disponible.

## Criterio de aceptación
No declarar integración terminada sin acceso y cambios al repositorio real. Nunca afirmar que MariaDB o AD funcionan sin pruebas en el entorno apropiado.
