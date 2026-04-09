#!/bin/sh
# Запуск из каталога, где лежат main.py и .venv (внутренняя папка moyka).
# На Linux купюроприёмник в kiosk_hardware включён по умолчанию (как bil.py). Отключить: MOYKA_HW=0 ./run.sh
cd "$(dirname "$0")" || exit 1
exec .venv/bin/python3 -u main.py "$@"
