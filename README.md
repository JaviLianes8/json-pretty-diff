# json-pretty-diff

## Objetivo
Generar un informe HTML claro que resuma las diferencias de nivel superior entre dos archivos JSON. El reporte organiza las claves en tres grupos (Added, Removed, Changed) y ofrece un vistazo rápido al impacto de los cambios.

## Instalación local
1. Clonar este repositorio.
2. Instalar el paquete en modo editable:
   ```bash
   pip install -e .
   ```

## Uso
Ejecutar el comando principal indicando los archivos a comparar:
```bash
jpd A.json B.json -o diff.html
```
- Si se omite `-o`, el HTML se envía a `stdout` y puede redirigirse con `>`.
- Código de salida `0`: no se detectaron diferencias (se genera HTML con "No differences").
- Código de salida `1`: se detectaron diferencias y el HTML refleja los cambios.
- Código de salida `2`: ocurrió un error (archivo inexistente, JSON inválido o raíz que no es objeto) y no se genera HTML.

## Ejemplo
```bash
jpd fixtures/base.json fixtures/update.json -o reports/diff.html
```
El archivo `diff.html` contendrá una sección por cada tipo de cambio, con estilos sencillos para resaltar claves agregadas, eliminadas o modificadas.

## Límites
- Solo se comparan las claves del primer nivel (sin recursión).
- No existen exclusiones, tolerancias ni configuraciones avanzadas.
- No se generan salidas con colores ANSI en consola.
- No hay integración con CI/CD ni suite de tests incluida.
