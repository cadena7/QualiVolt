# Perfil binario experimental del HT PQA820

Descripción derivada de los dos pares HED/PER disponibles en el proyecto. No es una especificación publicada por el fabricante. La asignación de canales se validó contra los dos CSV de referencia en todos sus registros: SaintEX y 2m.

## HED

Offsets en bytes desde cero. Enteros multibyte en orden big-endian.

| Offset | Longitud | Interpretación observada |
| --- | --- | --- |
| 0 | 4 | Firma `2f 00 01 02` |
| 13 | 8 | Modelo ASCII `PQA820` con espacios |
| 56 | 5 | Año desde 2000, mes, día, hora de 24 h, minuto |
| 75 | 2 | Intervalo de integración en segundos |
| 79 | 4 | Número de registros |
| 103 | 28 | Máscaras/configuración: solo se admite la secuencia observada |

Se requiere una cabecera de 195 bytes. La semántica de las máscaras, escalas TC/TP, nominal y conexión no se ha resuelto; no se precargan desde esos campos. No se ha identificado ni validado un checksum de cabecera.

La app sugiere **Trifásico 4 hilos** cuando la firma de configuración coincide exactamente con el perfil contrastado con los dos PDF oficiales. Esta firma concatena los rangos `[51:56]`, `[61:72]`, `[77:79]` y `[103:138]`, excluyendo fechas, duración y serie. No representa la identificación de un campo universal de conexión. Una firma diferente queda sin confirmar, y el usuario puede corregir siempre la sugerencia. Las mediciones y la frecuencia nominal del análisis no se modifican por esa sugerencia.

## PER

Registros de 1617 bytes: 539 campos de tres bytes. Cada campo contiene una mantisa **con signo de 16 bits big-endian** y un exponente decimal **con signo de 8 bits**. Valor = mantisa × 10^exponente. `ff ff 00` se corresponde con `-1` en el CSV y se conserva como tal. El archivo se completa al siguiente múltiplo de 512 bytes con `ff`; el lector valida longitud y relleno.

El orden completo se construye en `binary_reader.channel_layout()`. Bloques observados:

- Índices 0–32: voltajes, frecuencia y corrientes (promedio, máximo, mínimo).
- 33–128: potencias y factores de potencia de dirección positiva.
- 129–224: potencias y factores de potencia de dirección negativa.
- 225–227: desequilibrio `u2`.
- 228–230: bloque sin identificación validada, omitido.
- 231–536: seis bloques de 51 campos, para V1, V2, V3, I1, I2 e I3: THD, componente DC y armónicos 1–49.
- 537–538: campos finales sin identificar, omitidos.

El lector entrega 534 canales y genera sus tiempos desde inicio + índice × intervalo. No depende del nombre del archivo ni necesita un CSV. No deriva las 32 columnas de energía de TopView ni inventa valores para los campos desconocidos.

## Verificación

```sh
python -m unittest test_binary_reader.py
```

Con las muestras locales, compara 3,195,456 valores contra los dos CSV con tolerancia absoluta de 1e-8 y verifica todos los tiempos: 890,712 valores de SaintEX (534 × 1668) y 2,304,744 de 2m (534 × 4316). No hay valores fuera de tolerancia; la diferencia absoluta máxima es 1.1368683772161603e-13, atribuible a representación de coma flotante. Comprueba además rechazo de truncamiento y lectura de tiempos tras renombrar los pares. El reporte `files/binary_validation.json` registra los resultados y hashes SHA-256 de los archivos comparados. Las pruebas con datos reales se omiten si no hay muestras locales.

Este soporte se limita al perfil observado; una máscara o estructura distinta se rechaza. Coincidir en estructura no sustituye validar nuevos equipos, firmware o ajustes contra una referencia fiable, especialmente canales que solo contienen ceros o `-1` en las muestras disponibles.

Las muestras locales se encuentran en `files/`. Las comparaciones numéricas se ejecutan solo si el CSV correspondiente está presente en esa carpeta. Actualmente se conservan los binarios y el historial de validación; los CSV no están presentes.
