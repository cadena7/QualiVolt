# QualiVolt

**Lector y analizador de calidad de la energía para el HT Instruments PQA820.**

Abre grabaciones HED/PER sin iniciar TopView, explora las mediciones y genera reportes PDF con gráficas. También acepta exportaciones CSV compatibles de TopView.

**Autor:** Edgar Omar Cadena Zepeda  
**Versión:** 1.0.0 · 28 de octubre de 2026

## Antes de empezar

- Instala **Python 3.11 o posterior**.
- Necesitas una computadora con entorno gráfico e Internet para instalar las dependencias la primera vez.
- Descarga el proyecto completo desde GitHub: **Code → Download ZIP**, y descomprime el ZIP. También puedes clonar el repositorio con Git.
- Conserva la carpeta `assets/` junto al programa; contiene recursos necesarios para ejecutarlo.

QualiVolt está diseñado para **Windows, macOS y Ubuntu**. Se ha probado con las grabaciones incluidas en Windows; la validación completa en macOS y Ubuntu está pendiente. Por ahora se ejecuta desde Python, sin un instalador independiente.

## Instalación y ejecución

Elige las instrucciones de tu sistema. **Ejecuta los comandos dentro de la carpeta que contiene `app.py`, `install.sh` y `requirements.txt`.** No es necesario activar el entorno virtual.

### Windows — PowerShell, sin Git Bash

1. Instala Python desde [python.org para Windows](https://www.python.org/downloads/windows/). Si el instalador ofrece la opción, marca **Add Python to PATH**.
2. Abre la carpeta del proyecto en el Explorador. Escribe `powershell` en la barra de direcciones y pulsa Enter.
3. Comprueba que Python sea 3.11 o posterior:

```powershell
py -3 --version
```

4. Instala las dependencias, solo la primera vez:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

5. Abre QualiVolt:

```powershell
.\.venv\Scripts\python.exe app.py
```

**Las próximas veces**, abre PowerShell en esa carpeta y ejecuta únicamente el último comando.

Si `py` no está disponible pero `python --version` muestra una instalación válida, sustituye `py -3` por `python` en los comandos de preparación.

### Windows — alternativa con Git Bash

Instala [Git para Windows](https://git-scm.com/install/windows), que incluye Git Bash, y Python 3.11 o posterior. Abre Git Bash en la carpeta del proyecto.

Primera instalación:

```bash
bash install.sh
```

Para abrir la app, ahora y en las siguientes ocasiones:

```bash
bash runme.sh
```

### macOS

1. Instala Python desde [python.org para macOS](https://www.python.org/downloads/macos/).
2. Abre Terminal y entra en la carpeta del proyecto. Puedes escribir `cd `, arrastrar la carpeta desde Finder a Terminal y pulsar Enter.
3. Comprueba la versión:

```bash
python3 --version
```

Debe ser **3.11 o posterior**. Después instala y ejecuta:

```bash
bash install.sh
bash runme.sh
```

**Las próximas veces**, ejecuta únicamente `bash runme.sh` desde la carpeta del proyecto.

### Ubuntu Desktop

Abre una terminal e instala Python y el soporte para entornos virtuales:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
python3 --version
```

Comprueba que sea **3.11 o posterior**; si tu versión de Ubuntu proporciona un Python anterior, necesitarás un intérprete compatible antes de continuar.

Entra en la carpeta descargada. Por ejemplo, escribe `cd ` y arrástrala desde el administrador de archivos a la terminal. Instala y ejecuta:

```bash
bash install.sh
bash runme.sh
```

**Las próximas veces**, ejecuta únicamente `bash runme.sh` desde esa carpeta. La app necesita una sesión de escritorio; no es una aplicación para servidores sin pantalla.

### Alternativa manual en macOS y Ubuntu

Si prefieres no usar los scripts:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

### ¿Qué hacen los scripts?

| Archivo | Función |
| --- | --- |
| `install.sh` | Crea `.venv` e instala las dependencias de `requirements.txt`. |
| `runme.sh` | Ejecuta la app con el entorno preparado; no instala paquetes. |
| `unistall.sh` | Elimina únicamente `.venv` y sus dependencias. Conserva código, mediciones y reportes. |

El instalador prepara las dependencias necesarias. No necesitas instalar las fuentes por separado.

## Primera medición: guía rápida

### 1. Abrir los archivos

Pulsa **Abrir grabación** o usa **Archivo → Abrir grabación…**.

Selecciona el **`.HED`**. El `.PER` contiene las mediciones y debe estar en la misma carpeta, con exactamente el mismo nombre base:

```text
medicion.HED
medicion.PER
```

Para abrir un CSV de TopView, cambia el filtro del diálogo a **Exportación TopView CSV**.

En `files/` hay grabaciones de ejemplo para probar la aplicación.

### 2. Revisar la configuración

Al abrir una grabación aparece la configuración del proyecto:

- **Título de proyecto:** se propone el nombre del archivo; puedes cambiarlo. Se utiliza en el informe.
- **Frecuencia nominal del análisis:** 60 Hz por defecto, editable a 50 Hz. Es independiente del ajuste del medidor y de la frecuencia medida.
- **Sistema:** monofásico, trifásico de 3 hilos o trifásico de 4 hilos. El perfil HED reconocido propone trifásico de 4 hilos; siempre puedes corregirlo.
- **Tensión nominal:** 220 V por defecto, con opciones predefinidas y valor personalizado.
- **Referencia de medición:** fase-neutro o fase-fase, independiente del nominal del sistema. En trifásico, el nominal del sistema es fase-fase; en monofásico puedes elegir la referencia.
- **Relaciones TC/TP:** se guardan como información del estudio; no multiplican los valores leídos.

Puedes volver a editar estos campos desde **Configuración**.

### 3. Elegir canales y explorar

Los canales están agrupados por función: voltajes, corrientes, THD, frecuencia, potencias, factor de potencia, desequilibrio y armónicos. Al final está la lista completa.

- **Clic izquierdo:** selecciona un canal.
- **Ctrl + clic**, o Cmd según la plataforma: selección múltiple.
- **Clic derecho:** añade o quita un canal conservando los demás.
- **Buscador:** escribe, por ejemplo, `V1`, `THD` o `har05`.

La escala se ajusta al cambiar de selección. Cada unidad tiene su propio panel y los paneles comparten el tiempo. Usa la rueda para ampliar y arrastra para desplazarte; el cursor permite consultar valores sincronizados.

En los nombres, **Avg** significa promedio, **Max** máximo y **Min** mínimo.

### 4. Analizar un intervalo

Usa los campos **Desde / Hasta** y pulsa **Aplicar**. También puedes ampliar una zona y pulsar **Usar zoom**. **Todo** vuelve a la grabación completa.

Las estadísticas, el espectro y los nuevos informes usan el intervalo aplicado. Ampliar la gráfica por sí solo no cambia el período del análisis.

### 5. Consultar armónicos

En **Espectro armónico**, elige V1/V2/V3 o I1/I2/I3. Puedes ver los órdenes 2–49 como porcentaje de la fundamental o como amplitud RMS del período en V/A. Al mover el cursor sobre las barras aparecen su valor y cantidad de registros válidos.

### 6. Guardar gráficas o generar un informe

**Exportar PNG** guarda la gráfica o el espectro de la pestaña activa a 2400 píxeles de ancho. Su menú también permite generar una imagen por canal seleccionado. El tema claro/oscuro se conserva en las imágenes.

**Informe PDF** permite revisar título, responsable y punto de medición: salida de transformador, tablero principal, tablero secundario o carga individual. Después se abre la **vista previa dentro de QualiVolt**. Desde ahí puedes guardar, imprimir todo o un rango de páginas, o cerrar sin guardar.

El informe tiene nueve páginas con resumen, tendencias, corrientes de fases y neutro, potencias activa/reactiva/aparente, factor de potencia total inductivo/capacitivo, THD, espectros, estadísticas de voltajes fase-neutro y fase-fase y referencias técnicas. Puedes editar el nombre del responsable del análisis antes de generar el informe.

### 7. Guardar y reabrir un proyecto

En **Archivo → Guardar proyecto…**, guarda un `.qvp` con título, ajustes, canales, intervalo y notas. Para recuperarlo, usa **Archivo → Abrir proyecto…**.

**El proyecto no contiene las mediciones:** guarda referencias relativas a los originales. Si lo compartes, incluye también HED/PER y conserva la estructura de carpetas.

Para recuperar el estudio utiliza **Guardar proyecto…**. **Guardar configuración…** permite exportar una copia de los ajustes en JSON.

## Apariencia y menús

En **Apariencia** puedes elegir **Tema claro** o **Tema oscuro**. La app recuerda tu elección y adapta fondo, ejes, cuadrícula, leyendas y curvas. Los reportes PDF mantienen fondo blanco.

El menú **Archivo** incluye abrir, cerrar, proyectos, configuración, exportar, vista previa, imprimir la gráfica visible y salir. **Ayuda** contiene la guía y Acerca de.

## Actualizar, mover o retirar la app

**Actualizar dependencias:** vuelve a ejecutar `bash install.sh`. En PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**Mover la carpeta o cambiar de sistema operativo:** conserva el código, `assets/`, proyectos y mediciones, pero vuelve a crear `.venv` en el destino siguiendo la instalación. Los entornos virtuales no deben trasladarse entre rutas o computadoras. Si ya copiaste uno, elimina solamente la carpeta `.venv` antes de instalar de nuevo.

**Eliminar el entorno:** cierra QualiVolt y ejecuta `bash unistall.sh`, o elimina únicamente `.venv` desde el administrador de archivos. Python, el código y tus mediciones se conservan.

## Problemas frecuentes

| Problema | Solución |
| --- | --- |
| Windows dice que no encuentra Python o abre Microsoft Store | Instala Python, vuelve a abrir la terminal y prueba `py -3 --version`. Usa las instrucciones de PowerShell si `python3` apunta al alias de Microsoft Store. |
| `No module named PySide6` u otro módulo | Instala `requirements.txt` usando el Python de `.venv`, no otro intérprete. |
| Ubuntu no puede crear el entorno | Instala `python3-venv` y comprueba la versión de `python3`. |
| Error de plataforma Qt en Linux | Ejecuta desde una sesión de escritorio y revisa la biblioteca indicada en el error. Consulta la [documentación de Qt para Linux](https://doc.qt.io/qt-6/linux-requirements.html). |
| No se encuentra el PER | Coloca HED y PER juntos y comprueba que tengan el mismo nombre base. |
| Se rechaza una grabación | El lector admite el perfil PQA820 identificado; otros perfiles o archivos incompletos necesitan revisión. |
| El proyecto no encuentra sus mediciones | Recupera los archivos originales y su estructura de carpetas. |
| Faltan fuentes al abrir | Conserva `assets/fonts/Geist/` junto al código. |
| Las gráficas no muestran el período esperado | Pulsa **Todo** y vuelve a seleccionar los canales. |

## Compatibilidad

QualiVolt abre grabaciones compatibles del HT PQA820 y exportaciones CSV de TopView. Si una grabación no se puede abrir, conserva el mensaje de error para reportarlo.

Las energías acumuladas se calculan integrando las potencias promedio desde el inicio de la grabación. Los reportes son descriptivos y no realizan una evaluación automática de cumplimiento normativo. Las gráficas muestran los datos registrados; no reconstruyen formas de onda ni eventos breves ausentes en la medición.

Los datos se procesan localmente en tu computadora.

## Créditos y licencia

**Edgar Omar Cadena Zepeda** — autor de QualiVolt.

La fuente Geist Sans incluye su licencia en `assets/fonts/Geist/`. La licencia del código de QualiVolt está pendiente de definir.

HT Instruments, PQA820 y TopView se mencionan para identificar el equipo y el formato de origen. QualiVolt es un proyecto independiente del fabricante.

## Documentación de instalación

- [Descargas oficiales de Python](https://www.python.org/downloads/).
- [Entornos Python en Ubuntu](https://ubuntu.com/developers/docs/howto/python-setup/).
- [Instalación de Qt para Python / PySide6](https://doc.qt.io/qtforpython-6/gettingstarted.html).

Para colaborar con el código, consulta [Desarrollo y pruebas](DEVELOPMENT.md).

En los factores de potencia, `-1` indica un valor no definido para el cuadrante de operación. La app lo representa como un hueco y lo excluye de las estadísticas de ese canal, conservando el dato original.
