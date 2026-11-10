#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -x .venv/bin/python ]]; then
  bash scripts/setup.sh
else
  .venv/bin/python -m pip install -e '.[dev]'
fi
# Exact development origins; CSRF remains enabled.
gebichart_hosts="localhost,127.0.0.1,[::1]"
gebichart_origins="https://localhost:8000,https://127.0.0.1:8000"
if [[ -n "${CODESPACE_NAME:-}" && -n "${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-}" ]]; then
  gebichart_forward_host="${CODESPACE_NAME}-8000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
  gebichart_hosts+=",${gebichart_forward_host}"
  gebichart_origins+=",https://${gebichart_forward_host}"
fi
export DJANGO_ALLOWED_HOSTS="${DJANGO_ALLOWED_HOSTS:-$gebichart_hosts}"
export DJANGO_CSRF_TRUSTED_ORIGINS="${DJANGO_CSRF_TRUSTED_ORIGINS:-$gebichart_origins}"
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py crear_roles
exec .venv/bin/python manage.py runserver 0.0.0.0:8000
