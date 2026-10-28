# QualiVolt

Aplicación de escritorio en Python para leer y explorar mediciones de calidad de la energía del **HT Instruments PQA820**, directamente desde grabaciones **HED/PER** compatibles o desde archivos CSV exportados por TopView.

**QualiVolt** combina calidad de la energía y voltaje en una interfaz para explorar tus mediciones. El nombre aparece en la app y en el pie de cada página de los informes; el resumen destaca en negritas los valores relevantes.

Permite consultar los canales por función, comparar mediciones en gráficas interactivas y revisar estadísticas sin modificar los archivos originales.

**Autor y créditos: Edgar Omar Cadena Zepeda.**

## Estado del proyecto

Prototipo funcional en desarrollo. La importación y la interfaz se han comprobado con una grabación real de 1,668 registros y 566 canales en Windows. El proyecto está diseñado para Windows, macOS y Ubuntu; la validación en macOS y Ubuntu y los instaladores independientes están pendientes.

La lectura directa **HED/PER es experimental** y no requiere TopView ni CSV. Conserva ambos archivos con el mismo nombre en la misma carpeta y selecciona el HED desde la app. Se admite el perfil de 539 campos identificado en las muestras disponibles; las estructuras desconocidas se rechazan. Entrega 534 canales, sin energías acumuladas ni cinco campos sin identificar. Se compararon 3,195,456 valores compartidos y todos los tiempos contra los CSV de SaintEX y 2m, con tolerancia absoluta de 1e-8 y sin discrepancias fuera de tolerancia. Consulta [el formato y su validación](BINARY_FORMAT.md).

## Funciones disponibles

- Apertura de CSV de TopView con separador `|` y declaración `sep=|`.
- Apertura directa HED/PER compatible, con fecha inicial, intervalo y cantidad de registros leídos de HED.
- Lectura de fechas españolas en formato de 12 horas y encabezados con unidades.
- Configuración del sistema al abrir una grabación.
- Frecuencia nominal del análisis de 50 o 60 Hz, con 60 Hz como valor inicial por preferencia del usuario; se muestra además una referencia aproximada basada en las mediciones.
- Selección de sistema monofásico, trifásico de 3 hilos o trifásico de 4 hilos.
- Tensiones nominales predefinidas y entrada de valores personalizados.
- Canales agrupados por función y búsqueda por nombre o grupo.
- Selección múltiple con paneles sincronizados por unidad.
- Gráficas con zoom y desplazamiento.
- Exportación PNG de la vista actual o de cada canal seleccionado, a 2400 píxeles de ancho.
- Mínimo, media y máximo de los canales seleccionados para el intervalo aplicado.
- Guardado de la configuración en un archivo JSON separado.
- Guía de uso y sección Acerca de integradas en la aplicación.
- Informe PDF de ocho páginas con créditos, resumen automático local, tendencias, THD, espectros armónicos, cobertura de datos y referencias normativas.

### Organización de canales

Los grupos aparecen en este orden, cuando existen en el archivo:

1. Voltajes promedio fase-neutro.
2. Voltajes promedio fase-fase.
3. Corrientes promedio de fases y neutro.
4. Distorsión armónica total de corriente: THD (%).
5. Distorsión armónica total de voltaje: THD (%).
6. Frecuencia promedio.
7. Potencia activa promedio.
8. Factor de potencia promedio.
9. Desequilibrio promedio.
10. Armónicos individuales de corriente (A).
11. Armónicos individuales de voltaje (V).
12. Lista completa de canales.

## Requisitos

- Python 3.11 o posterior.
- Un entorno de escritorio con soporte para Qt.
- Conexión a Internet para instalar las dependencias.
- Git Bash en Windows si se utilizan los scripts `.sh`. Con PowerShell no es necesario.

Dependencias de Python: **PySide6**, **PyQtGraph** y **NumPy**. Los rangos de versiones están en `requirements.txt`.

## Instalación y ejecución

Descarga o clona el repositorio y abre una terminal en su carpeta.

### Windows con PowerShell

Preparar el entorno e instalar dependencias:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Ejecutar la aplicación:

```powershell
.\.venv\Scripts\python.exe app.py
```

No es necesario activar el entorno virtual. El intérprete utilizado para crear `.venv` debe ser Python 3.11 o posterior.

### macOS, Ubuntu o Windows con Git Bash

Instalar:

```bash
bash install.sh
```

Ejecutar:

```bash
bash runme.sh
```

`install.sh` crea `.venv` si hace falta e instala las dependencias. Puede ejecutarse otra vez para volver a resolverlas según `requirements.txt`. `runme.sh` únicamente ejecuta la aplicación usando ese entorno.

### Eliminar el entorno local

Cierra la app y ejecuta desde Bash:

```bash
bash unistall.sh
```

El script elimina únicamente `.venv` y las dependencias instaladas dentro de ese entorno. Conserva el código fuente, las mediciones, los ajustes y los reportes. No desinstala Python ni modifica paquetes globales. Para volver a preparar la app, ejecuta `bash install.sh`.

El archivo `.gitignore` excluye el entorno virtual, las cachés de Python, `tmp/`, `output/` y los ajustes `*.analysis.json` de nuevas incorporaciones a Git. Las grabaciones originales y los PDF de configuración no están excluidos; elige cuáles deseas compartir al preparar el repositorio. Los archivos que ya estén versionados no dejan de estarlo por añadirlos a `.gitignore`.

### Instalación manual en macOS o Ubuntu

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

## Uso

### Proyectos, intervalos y espectro

- **Archivo → Guardar proyecto…** guarda un `.qvp` con título, configuración, punto de medición si se ha elegido, canales seleccionados, intervalo y notas del estudio. **Archivo → Abrir proyecto…** recupera esos datos. El proyecto referencia la medición mediante una ruta relativa; conserva el proyecto y los originales HED/PER con su estructura de carpetas al compartirlos. No copia ni modifica las mediciones.
- En **Desde / Hasta**, elige los límites y pulsa **Aplicar**. **Usar zoom** toma el intervalo horizontal visible de la gráfica principal; **Todo** vuelve a la grabación completa. Las estadísticas, el espectro y los nuevos informes PDF usan exclusivamente los registros del intervalo aplicado, incluyendo los extremos.
- En **Tendencias sincronizadas**, selecciona canales de distintas unidades con Ctrl/Cmd. Se crea un panel por unidad, con escalas verticales independientes y eje temporal compartido. Desplaza o amplía horizontalmente cualquier panel; el cursor muestra la muestra más cercana y valores de hasta cinco canales. Puedes desplazarte verticalmente para consultar los demás paneles.
- En **Espectro armónico**, elige V1/V2/V3 o I1/I2/I3 y alterna porcentaje de la fundamental o amplitud RMS temporal en V/A. Muestra órdenes 2–49; la fundamental es la referencia del porcentaje. El cursor muestra el valor y la cantidad de registros válidos de cada orden. Exportar PNG e imprimir usan el espectro cuando esa pestaña está activa.

El porcentaje armónico es una razón de RMS temporales sobre pares válidos, no una reconstrucción de forma de onda. El zoom por sí solo no cambia el intervalo de análisis: pulsa **Usar zoom** para aplicarlo.

1. Copia los archivos HED y PER de la grabación en la misma carpeta, conservando sus nombres iguales. También puedes usar un CSV de TopView.
2. Pulsa **Abrir grabación** y selecciona el **HED**. El lector encuentra automáticamente su **PER** en la misma carpeta. Para abrir una exportación, cambia el filtro del diálogo a **CSV**.
3. Escribe el **Título de proyecto** y revisa la configuración del sistema antes de analizarlo. El título se propone con el nombre del archivo y puedes cambiarlo después en **Configuración**.
4. Expande los grupos y selecciona un canal. Usa Ctrl, o Cmd según la plataforma, para seleccionar varios; las distintas unidades se muestran en paneles sincronizados.
5. Usa el buscador para localizar canales: por ejemplo, `V1`, `THD` o `har05`.
6. Acerca o aleja con la rueda del ratón y arrastra para desplazarte por la gráfica.
7. Consulta las estadísticas debajo de la gráfica. Corresponden al intervalo aplicado. Usa Aplicar o Usar zoom para cambiarlo.
8. Si lo deseas, guarda los ajustes con **Guardar configuración…**.

La guía también está disponible en el botón **Guía de uso** y en el menú **Ayuda**.

El menú **Archivo** reúne abrir (`Ctrl+O`), cerrar grabación (`Ctrl+W`), configuración, guardar ajustes (`Ctrl+S`), exportar PDF/PNG, vista previa, imprimir la gráfica visible (`Ctrl+P`) y salir. Los atajos usan la tecla equivalente de la plataforma cuando corresponde. La impresión conserva el zoom y añade el título del proyecto y los créditos. Cerrar una grabación limpia la vista sin eliminar archivos; guarda previamente los ajustes que quieras conservar.

En **Apariencia**, elige **Tema claro** o **Tema oscuro**. La selección se recuerda entre sesiones y cambia la interfaz y las gráficas: fondo, texto, ejes, cuadrícula y curvas. Los PNG y la impresión de la gráfica visible conservan el tema elegido; los informes PDF mantienen su diseño de fondo blanco para lectura e impresión.

### Exportar gráficas PNG

En la parte superior del panel de gráficas, pulsa **Exportar PNG** para guardar la gráfica visible con los canales seleccionados y el zoom actual. La flecha del botón ofrece **Un PNG por canal seleccionado…**: selecciona una carpeta y se guardará una imagen independiente por canal, conservando el intervalo horizontal visible y ajustando la escala vertical de cada imagen. Si un nombre ya existe en la exportación por canal, se añade un número para conservarlo. Las imágenes tienen 2400 píxeles de ancho.

### Informe automático PDF

Pulsa **Informe PDF**, revisa el título de proyecto, responsable y punto de medición. Primero se abre una **vista previa dentro de la app**, con todas las páginas y opciones de zoom. Desde ahí puedes **Guardar PDF…**, **Imprimir…** (incluido un rango de páginas) o cerrar sin guardar. El título del proyecto se utiliza en la portada y en los metadatos del PDF, y se incluye al guardar la configuración JSON. Los créditos de **Edgar Omar Cadena Zepeda** aparecen siempre, aunque cambie el responsable del estudio. No requiere paquetes adicionales a las dependencias de la interfaz.

La interfaz y los informes utilizan **Geist Sans**: Regular para textos y gráficas, SemiBold para títulos del PDF y Bold para los resultados destacados. La fuente se incluye en `assets/fonts/Geist/` con su licencia SIL OFL 1.1 y se carga localmente. No necesitas instalarla; conserva esa carpeta al descargar o distribuir el proyecto.

Incluye tendencias de voltaje fase-neutro y fase-fase, corrientes de fases, potencias totales activa/reactiva/aparente, factor de potencia total, THD de voltaje/corriente, frecuencia, espectros por fase, estadísticas de corriente de neutro y referencias técnicas. El resumen se calcula localmente mediante reglas y estadísticas; no envía datos a una IA o servicio externo. Analiza el intervalo aplicado, o toda la grabación si no hay selección temporal.

Los espectros muestran la razón de RMS temporales `100 × sqrt(sum(Hh²)/sum(H1²))` para cada orden 2-49 usando pares de valores válidos y fundamental mayor que cero. No son una forma de onda instantánea, TDD ni percentiles normativos. Los valores negativos y no finitos se excluyen de las magnitudes no negativas del reporte, sin alterar los originales. Los ceros se conservan y una fundamental pequeña puede aumentar los porcentajes de corriente.

Referencias incluidas: IEEE 519-2022 (armónicos en el PCC), IEEE 1159-2019 (monitoreo), ANSI/NEMA C84.1-2020 (R2025) (tensiones de sistemas de 60 Hz) y Código de Red mexicano RES/550/2021. El reporte presenta explicaciones breves de estas referencias y una única nota de alcance al final. **No implementa tablas normativas ni declara cumplimiento.** La evaluación formal requiere confirmar punto de conexión, nivel de suministro, demanda, IL/Isc cuando corresponda, ventanas de agregación, duración y edición aplicable. THD de corriente no debe confundirse con TDD.

### Configuración del sistema

| Campo | Comportamiento |
| --- | --- |
| Frecuencia nominal | 60 Hz por defecto, editable a 50 Hz. Es independiente del ajuste del instrumento (50 Hz en los reportes disponibles) y de la frecuencia medida. |
| Sistema | Monofásico, trifásico de 3 hilos, trifásico de 4 hilos o sin confirmar. Para el perfil HED contrastado con los reportes oficiales se precarga trifásico de 4 hilos como sugerencia editable; otras firmas y CSV quedan sin confirmar. |
| Referencia de las mediciones | Fase-neutro por defecto; editable e independiente del nominal del sistema. |
| Tensión nominal del sistema | 220 V por defecto; admite valores predefinidos y personalizados. El valor 0 indica pendiente. |
| Referencia del nominal | Fase-fase en trifásico; fase-neutro o fase-fase en monofásico. Queda sin confirmar mientras no se elija el sistema. |
| Relaciones TC/TP | Se guardan como metadatos; no reescalan las mediciones del CSV. |

Por ejemplo, un sistema trifásico puede configurarse con **220 V nominales fase-fase** y conservar **fase-neutro como referencia de las mediciones**. Estos ajustes no convierten los valores exportados.

Los valores iniciales no se han obtenido de la cabecera `.HED`; deben revisarse para cada instalación.

## Formato de entrada y criterios de lectura

- Separador `|`, con soporte para una primera línea `sep=|`.
- Primera columna de fecha y hora, como `08/10/2026 12:28:00 p. m.`.
- Canales numéricos con sus nombres y unidades originales.
- Codificación UTF-8, con o sin BOM, o CP1252.
- Se comprueba la cantidad de columnas y que los tiempos estén en orden creciente, sin duplicados.
- Las horas se conservan como las registró el equipo, sin conversión de zona horaria.
- THD se muestra en porcentaje; los armónicos individuales conservan su amplitud en A o V.
- Los valores `-1` se conservan y participan en las estadísticas: su significado en la exportación está pendiente de validar.

La compatibilidad con otras variantes de exportación de TopView todavía debe comprobarse.

## Instrumento de referencia

El **HT Instruments PQA820** es un analizador de calidad de la energía para sistemas monofásicos y trifásicos. Entre sus funciones se encuentran el registro de hasta 383 parámetros simultáneos, armónicos de tensión y corriente hasta el orden 49, THD, potencias, energías y corriente de neutro.

Estas características corresponden al instrumento. La información que puede mostrar esta aplicación depende del contenido del CSV exportado.

Consulta las especificaciones y documentación en el [sitio oficial del HT PQA820](https://www.ht-instruments.com/en/products/power-quality-analyzers/wifi/pqa820/).

## Estructura del proyecto

```text
.
├── app.py             # Interfaz gráfica, configuración y visualización
├── appearance.py      # Temas claro/oscuro
├── typography.py      # Carga de Geist Sans
├── branding.py        # Nombre, autor y versión
├── study_view.py      # Intervalos y espectro interactivo
├── project.py         # Guardado y recuperación de proyectos
├── analysis_report.py # Generación del informe PDF
├── report_preview.py  # Vista previa e impresión del informe
├── assets/fonts/Geist/ # Fuentes y licencias necesarias
├── files/             # Grabaciones de prueba y referencias
├── reader.py          # Importación y validación del CSV
├── binary_reader.py   # Lectura directa experimental HED/PER
├── test_binary_reader.py # Pruebas y comparación con CSV local
├── BINARY_FORMAT.md   # Estructura observada y alcance de validación
├── requirements.txt   # Dependencias de Python
├── install.sh         # Preparación del entorno e instalación
├── runme.sh           # Ejecución con el entorno preparado
├── unistall.sh        # Elimina solamente el entorno .venv
├── .gitignore         # Excluye entorno, cachés y resultados locales
└── README.md
```

## Limitaciones y próximos pasos

- Ampliar y validar la lectura HED/PER con más perfiles, firmware y configuraciones; resolver campos pendientes y energías.
- Añadir importación de los antiguos JSON de configuración; los proyectos `.qvp` ya permiten guardar y recuperar el estudio.
- Validar el significado de los valores especiales y el tratamiento de datos ausentes.
- Incorporar exportación Excel y reglas normativas verificadas con parámetros de conexión y agregaciones adecuados.
- Ampliar el análisis de eventos según los datos disponibles.
- Validar la aplicación en macOS y Ubuntu y preparar paquetes por plataforma.

Las series agregadas del CSV no permiten reconstruir formas de onda ni eventos breves que no se hayan exportado. Esta versión tampoco realiza una evaluación automática de cumplimiento normativo.

## Solución de problemas

**Windows indica que no encuentra Python o abre Microsoft Store:** instala Python 3.11 o posterior, cierra y vuelve a abrir la terminal. Si `python3` apunta al alias de Microsoft Store, utiliza los comandos de PowerShell con `py -3` para preparar el entorno.

**No se puede crear `.venv` en Ubuntu:** comprueba que esté instalado el paquete `python3-venv` correspondiente a tu versión de Python.

**Faltan módulos:** ejecuta de nuevo `bash install.sh` o instala `requirements.txt` con el intérprete del entorno virtual.

**La gráfica no muestra la selección:** pulsa Todo para recuperar el intervalo completo y selecciona un canal. Los canales con unidades diferentes aparecen en paneles separados.

## Contribuciones

Las propuestas de mejora y los reportes de errores son bienvenidos. Al reportar un problema, incluye el sistema operativo, la versión de Python, los pasos para reproducirlo y el mensaje de error. Si aportas una muestra de datos, utiliza una grabación que tengas permiso de compartir.

## Créditos y licencia

**Edgar Omar Cadena Zepeda** — autor del proyecto.

HT Instruments, PQA820 y TopView se mencionan para identificar el equipo y el formato de origen. Este proyecto es independiente del fabricante.

La licencia de distribución y reutilización está pendiente de definir; el repositorio todavía no incluye un archivo `LICENSE`.

## Pruebas

```bash
python -m unittest discover -v
```

Las grabaciones de ejemplo están en `files/`. Las pruebas binarias comparan con CSV solo si están presentes junto a los HED/PER; consulta `files/README.md`. Para ejecutar todas las pruebas, instala primero las dependencias de `requirements.txt`.
