#!/bin/sh
# Запуск из каталога, где лежат main.py и .venv (внутренняя папка moyka).
cd "$(dirname "$0")" || exit 1
exec .venv/bin/python3 -u main.py "$@"
