# gebichart

Entorno de desarrollo con Python 3.12, pytest y Ruff.
El repositorio aún no incluye una aplicación ni dependencias de ejecución.

## GitHub Codespaces o VS Code

Abre el repositorio con **Code → Codespaces → Create codespace on main**,
o utiliza **Dev Containers: Reopen in Container** en VS Code.
La configuración instala las dependencias automáticamente.

## Desarrollo local o Codex

Requiere Python 3.12 o posterior:

```bash
bash scripts/setup.sh
source .venv/bin/activate
python --version
ruff check .
```

Añade las dependencias de la aplicación a `project.dependencies` en
`pyproject.toml`. Para ejecutar las pruebas cuando existan: `pytest`.

El archivo `.devcontainer/devcontainer.json` define el entorno reproducible.
La creación de un Codespace requiere una cuenta con acceso y cuota disponibles.
