# Contraste de configuraciones exportadas

Se revisaron los dos PDF `settings_*.pdf` exportados desde TopView el 28 de octubre de 2026. Son referencias externas de configuración; la app no importa estos PDF automáticamente.

## Datos que muestran ambos reportes

| Campo del reporte | Valor |
| --- | --- |
| Equipo | PQA820, serie 25073960 |
| Sistema | 3phase-4W (trifásico de 4 hilos) |
| Frequency | 50 |
| VT ratio | 1 |
| FS Clamps | 1000 |
| Clamps Type | FlexInt |
| Int.Per. | 01:00 |
| Nominal de anomalías de tensión | 220 V |
| Límites alto / bajo | 10 % / 10 % |
| Armónicos / anomalías / cogeneración | On / On / On |
| Inicio efectivo | SaintEX: 08/10/26 12:28; 2m: 09/10/26 17:09 |
| Fin efectivo | SaintEX: 09/10/26 16:16:00; 2m: 12/10/26 17:05:00 |
| N. Par. | 347 |

## Discrepancias y alcance

El reporte corregido de SaintEX, emitido a las 10:45:32, muestra inicio 08/10/26 12:28 y fin 09/10/26 16:16:00. Ahora cada PDF corresponde a su grabación. El reporte de 2m muestra inicio 09/10/26 17:09 y fin 12/10/26 17:05:00. Los dos intervalos de integración son de un minuto y sus últimas muestras quedan un intervalo antes del fin efectivo.

El usuario confirmó que trabaja con sistemas de 60 Hz y que el instrumento mantiene por defecto el ajuste de 50 Hz que aparece en ambos reportes. Se conserva esa distinción: la app inicia el nominal del análisis en 60 Hz, editable; no interpreta 50 Hz como la frecuencia real ni modifica las mediciones. La referencia aproximada obtenida de las mediciones se muestra por separado. El offset candidato de frecuencia en HED sigue pendiente de validación con configuraciones distintas.

El fin efectivo 17:05 de 2m es coherente con su última muestra a las 17:04 y un intervalo de un minuto. El intervalo coincide con el obtenido de HED y CSV. El nombre `2m` no representa el intervalo real de esta grabación.

El nominal aparece dentro de la sección de anomalías de tensión del reporte. Su referencia fase-fase/fase-neutro no está explícita en ese texto; se conserva la convención configurada por el usuario en la app.

FS Clamps 1000 es el fondo de escala de las pinzas, no una relación TC de 1000:1. No debe aplicarse como multiplicador adicional a las corrientes ya decodificadas y validadas.

El reporte muestra Memory 8KB y Max Recording Time 0 días 3 horas; estos campos no deben usarse para validar la capacidad física ni la duración real de estas grabaciones. Los 347 parámetros del reporte tampoco equivalen necesariamente a las 534 columnas decodificadas: estas incluyen estadísticas Avg/Max/Min.

## Indicios en HED pendientes de validación con ajustes distintos

En ambas cabeceras aparecen 50 en el offset 51, 1000 en los offsets 54–55 y 220 en los offsets 134–135 (estos dos últimos como enteros big-endian). Coinciden con frecuencia, fondo de escala y nominal del reporte. Son candidatos, no una asignación demostrada: faltan muestras donde cambien estos ajustes para comprobar offsets, unidades y semántica.

No se han añadido esos offsets como metadatos confirmados ni se han convertido las mediciones. Para validarlos se necesitan grabaciones con cambios conocidos de configuración, acompañadas de sus reportes correctos. No es necesario alterar los archivos originales.
