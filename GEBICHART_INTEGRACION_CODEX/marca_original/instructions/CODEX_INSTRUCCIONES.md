# Instrucciones para Codex — GEBICHART

## Objetivo
Incorporar el sistema visual del paquete a la aplicación existente **Python/Django/MariaDB**, sin alterar funcionalidad, permisos ni datos.

## Reglas obligatorias
1. Respetar exactamente el isotipo aprobado `static/gebichart/logo/gebichart-isotipo-aprobado.png`: no redibujar, reinterpretar, recolorear, recortar detalles ni añadir escudos.
2. La identidad visual usa principalmente negro #000000, granate #993333, verde #336633, amarillo #FABC4D, dorado auxiliar #D19544, gris #999999 y fondo #FAFAF7.
3. No incorporar fotos de capiteles, rosetones, catedral ni otros monumentos. Utilizar exclusivamente elementos abstractos o iconos del paquete.
4. Integrar `static/gebichart/css/tokens.css` y `components.css` mediante `{% load static %}` de Django.
5. Mantener accesibilidad WCAG: contraste en textos, foco visible, etiquetado de inputs, navegación teclado y reducción de movimiento.
6. No modificar el manual PDF; es la referencia visual aprobada en la conversación.
7. Los 26 iconos son SVG con `currentColor` para heredar color CSS. Usar botones y textos accesibles.
8. No incluir fuentes propietarias o de licencia incierta. Configurar la familia `Burgos` solo cuando el Ayuntamiento facilite archivos con autorización de uso; usar Georgia como respaldo. Para interfaz usar Myriad Pro solo si está autorizada; si no, Source Sans 3 o Segoe UI.
9. No aplicar este kit como sustituto de la marca institucional oficial del Ayuntamiento; mantener la identidad de GEBICHART separada.

## Integración sugerida
- Copiar contenido de `static/gebichart/` a la carpeta correspondiente de archivos estáticos de Django.
- En `base.html`:
  ```django
  {% load static %}
  <link rel="icon" href="{% static 'gebichart/favicon/favicon.ico' %}">
  <link rel="stylesheet" href="{% static 'gebichart/css/components.css' %}">
  <img src="{% static 'gebichart/logo/gebichart-isotipo-transparente.png' %}" alt="GEBICHART">
  ```
- Mantener la lógica Python/Django de autenticación AD y permisos existentes.
- Revisar todas las vistas para aplicar componentes coherentes: formulario de obra, ficha individual, tabla de inventario, ubicaciones, cesiones, informes, administración.
- Ejecutar comprobaciones visuales en escritorio y móvil y pruebas de accesibilidad antes de integrar.

## Entrega esperada de Codex
PR con cambios a plantillas y estilos, sin modificar esquemas de MariaDB ni lógica de autorización; capturas de vistas y pruebas.
