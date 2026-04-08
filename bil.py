#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест NV10 → PC817 → GPIO (Radxa Zero: pin 40 → gpiochip1 offset 11).
Запуск: sudo -E ./venv/bin/python3 bil.py  (см. MOYKA_* в коде).
"""

from __future__ import annotations

import os
import sys
import time

try:
    from periphery import GPIO
except ImportError:
    print(
        "Установите в ТОМ ЖЕ Python, которым запускаете скрипт:\n"
        "  pip install python-periphery\n\n"
        "Если запускали «sudo python3 bil.py», sudo берёт системный python без venv.\n"
        "Тогда либо:\n"
        "  sudo -E ./venv/bin/python3 bil.py\n"
        "либо добавьте пользователя в группу gpio и запускайте без sudo:\n"
        "  ./venv/bin/python3 bil.py",
        file=sys.stderr,
    )
    sys.exit(1)

# --- настройки из окружения ---
# Физ. 40-й контакт → на вашей плате offset 11 (libgpiod / periphery)
CHIP = os.environ.get("MOYKA_GPIOCHIP", "/dev/gpiochip1").strip()
try:
    LINE = int(os.environ.get("MOYKA_GPIO_LINE", os.environ.get("MOYKA_LINE_BILL", "11")), 0)
except ValueError:
    print("MOYKA_GPIO_LINE должен быть числом", file=sys.stderr)
    sys.exit(1)

EDGE = os.environ.get("MOYKA_EDGE", "falling").strip().lower()
if EDGE not in ("rising", "falling"):
    EDGE = "falling"

# pull_up + falling (PC817 коллектор к GPIO, эмиттер GND, внешняя или внутр. подтяжка к 3.3V)
# pull_down + rising — если схема наоборот
BIAS = "pull_up" if EDGE == "falling" else "pull_down"

try:
    UZS_PULSE = int(os.environ.get("MOYKA_UZS_PULSE", "1000"), 0)
except ValueError:
    UZS_PULSE = 1000

DEBOUNCE_S = float(os.environ.get("MOYKA_DEBOUNCE_S", "0.03"))
IDLE_S = float(os.environ.get("MOYKA_IDLE_S", "0.8"))
POLL_S = float(os.environ.get("MOYKA_POLL_S", "0.002"))
# 1 — печатать каждый импульс сразу (проверка проводки); 2 — ещё и каждую смену уровня (шумно)
DEBUG = int(os.environ.get("MOYKA_DEBUG", "0"), 0)

if POLL_S < 0.0005:
    POLL_S = 0.0005
if POLL_S > 0.05:
    POLL_S = 0.05


def main() -> None:
    try:
        gpio = GPIO(CHIP, LINE, "in", bias=BIAS, edge="none")
    except Exception as e:
        eno = getattr(e, "errno", None)
        low = str(e).lower()
        py = sys.executable

        # EBUSY: линия уже открыта другим процессом (main.py, второй bil, libgpiod)
        if eno == 16 or "busy" in low or "resource busy" in low:
            print(
                f"Линия занята (EBUSY): {CHIP} offset {LINE}\n{e}\n\n"
                "Остановите всё, что может держать GPIO:\n"
                "  • systemd-сервис мойки (main.py), другой терминал с bil.py\n"
                "  • pgrep -af 'python|nicegui'\n"
                f"  • sudo fuser -v {CHIP}\n"
                "  • ls /sys/class/gpio  (если есть export — освободите линию)\n",
                file=sys.stderr,
            )
            sys.exit(1)

        # periphery часто кидает GPIOError вокруг Errno 13
        if isinstance(e, PermissionError) or eno == 13 or "ermission denied" in low:
            print(
                f"Нет доступа к {CHIP}: {e}\n\n"
                "Сделайте одно из:\n"
                "  1) sudo usermod -aG gpio $USER  →  перелогиньтесь, затем без sudo:\n"
                f"       {py} bil.py\n"
                "  2) newgrp gpio\n"
                f"  3) разовая проверка с root, но тем же Python (чтобы был periphery из venv):\n"
                f"       sudo -E {py} bil.py\n\n"
                "Не используйте просто «sudo python3» — это другой интерпретатор.\n"
                "Права на устройство: ls -l /dev/gpiochip*",
                file=sys.stderr,
            )
            sys.exit(1)

        raise
    prev = bool(gpio.read())
    dbg = f"  DEBUG={DEBUG}" if DEBUG else ""
    print(
        f"Купюры NV10→PC817→GPIO\n"
        f"  chip={CHIP}  line(offset)={LINE}  edge={EDGE}  bias={BIAS}\n"
        f"  стартовый уровень: {'HIGH' if prev else 'LOW'}\n"
        f"  UZS за импульс={UZS_PULSE}  debounce={DEBOUNCE_S}s  конец купюры после тишины {IDLE_S}s\n"
        f"  опрос каждые {POLL_S * 1000:.1f} ms{dbg}\n"
        f"Ctrl+C — выход\n"
        f"Подсказка: если при внесении купюры тишина — MOYKA_DEBUG=1 (см. импульсы), "
        f"MOYKA_DEBUG=2 (любая смена уровня), MOYKA_EDGE=rising, MOYKA_POLL_S=0.0005; "
        f"проверьте провод на pin40/line11 и что у NV10 включён импульсный выход.\n",
        flush=True,
    )

    pulse_count = 0
    last_pulse_t = 0.0

    try:
        while True:
            x = bool(gpio.read())
            if DEBUG >= 2 and x != prev:
                print(f"  [уровень] {'HIGH' if x else 'LOW'}", flush=True)
            if EDGE == "rising":
                hit = x and not prev
            else:
                hit = (not x) and prev
            prev = x

            if hit:
                now = time.time()
                if now - last_pulse_t >= DEBOUNCE_S:
                    pulse_count += 1
                    last_pulse_t = now
                    if DEBUG >= 1:
                        print(f"  [импульс #{pulse_count}] t={now:.3f}", flush=True)

            if pulse_count > 0 and (time.time() - last_pulse_t > IDLE_S):
                total = pulse_count * UZS_PULSE
                print(f"\n>>> ПРИНЯТО: {total} UZS  (импульсов: {pulse_count})\n", flush=True)
                pulse_count = 0

            time.sleep(POLL_S)
    except KeyboardInterrupt:
        print("\nВыход.", flush=True)
    finally:
        gpio.close()


if __name__ == "__main__":
    main()
