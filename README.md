# Duraplay QR Cajas

Aplicación  para generar los códigos QR para identificar las cajas de los camiones que ingresan a la planta.

## Qué hace

- Genera un código QR (imagen PNG) por cada código de caja proporcionado.
- Los códigos se pueden ingresar de dos formas:
  - **Manual**: escribiendo los códigos directamente, uno por línea o separados por coma. Pensado para casos puntuales que no ameritan una exportación completa de la base de datos.
  - **Importar CSV**: leyendo un archivo CSV exportado de la base de datos (MSSQL), seleccionando la columna que contiene el código de caja.
- Elimina automáticamente los códigos duplicados antes de generar.
- Guarda todos los QR generados en la carpeta de destino elegida por el usuario.
- Al terminar, muestra un reporte (recibidos, generados, duplicados eliminados, errores) y ofrece abrir directamente la carpeta con los resultados.
- Disponible como aplicación empaquetada para uso en planta sin depender de un entorno de Python instalado.