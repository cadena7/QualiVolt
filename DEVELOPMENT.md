# Desarrollo y pruebas de QualiVolt

Tecnologías: Python, PySide6, PyQtGraph y NumPy. Las dependencias están en `requirements.txt`.

Con el entorno preparado, ejecuta las pruebas:

```powershell
# Windows PowerShell
.\.venv\Scripts\python.exe -m unittest discover -v
```

```bash
# macOS y Ubuntu
.venv/bin/python -m unittest discover -v
```

Las pruebas binarias usan `files/`. Si hay un CSV con el mismo nombre junto al HED/PER, también comparan sus valores y tiempos. Los resultados históricos están en `files/binary_validation.json`.

La carpeta `assets/` contiene recursos necesarios. `.venv/`, cachés, `tmp/` y `output/` se excluyen mediante `.gitignore`. Los archivos de prueba de `files/` sí forman parte del contenido previsto para el repositorio.

