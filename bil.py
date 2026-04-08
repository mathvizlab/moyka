#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NV10 → PC817 → GPIO (физ. pin 40). Дефолты как RPi.GPIO: RISING + pull_down, debounce 0.03 с, idle 0.8 с.
См. MOYKA_* и gpiofind PIN_40.
"""

from __future__ import annotations

import os
import shutil
import subprocess
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
# Дефолт — типичная связка для одной из сборок Radxa Zero (не для всех ревизий).
_DEFAULT_CHIP = "/dev/gpiochip1"
_DEFAULT_LINE = 11


def _gpiofind_line(name: str) -> tuple[str, int] | None:
    """gpiofind из пакета gpiod → (/dev/gpiochipN, offset)."""
    gf = shutil.which("gpiofind")
    if not gf or not name.strip():
        return None
    try:
        out = subprocess.check_output(
            [gf, name.strip()],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return None
    parts = out.split()
    if len(parts) != 2 or not parts[0].startswith("gpiochip"):
        return None
    try:
        return "/dev/" + parts[0], int(parts[1], 0)
    except ValueError:
        return None


_line_name = (
    os.environ.get("MOYKA_GPIO_LINE_NAME", "").strip()
    or os.environ.get("MOYKA_GPIOFIND", "").strip()
)
if _line_name:
    _resolved = _gpiofind_line(_line_name)
    if not _resolved:
        print(
            f"MOYKA_GPIO_LINE_NAME={_line_name!r}: gpiofind не вернул линию.\n"
            "Установите gpiod (apt: gpiod) и проверьте имя: gpiofind "
            f"{_line_name}\n"
            "Либо задайте вручную MOYKA_GPIOCHIP и MOYKA_GPIO_LINE (число).",
            file=sys.stderr,
        )
        sys.exit(1)
    CHIP, LINE = _resolved
else:
    CHIP = os.environ.get("MOYKA_GPIOCHIP", _DEFAULT_CHIP).strip()
    try:
        LINE = int(
            os.environ.get("MOYKA_GPIO_LINE", os.environ.get("MOYKA_LINE_BILL", str(_DEFAULT_LINE))),
            0,
        )
    except ValueError:
        print("MOYKA_GPIO_LINE должен быть числом", file=sys.stderr)
        sys.exit(1)

# По умолчанию как RPi.GPIO: BOARD pin 40, PUD_DOWN, считаем RISING (см. kiosk_hardware / ваш скрипт на Pi).
EDGE = os.environ.get("MOYKA_EDGE", "rising").strip().lower()
if EDGE not in ("rising", "falling"):
    EDGE = "rising"

# falling + pull_up: покой HIGH, импульс тянет линию к GND (коллектор к GPIO, эмиттер GND, подтяжка к 3.3V).
# rising + pull_down: покой LOW, импульс подаёт на GPIO «единицу» (RPi: GPIO.setup(40, IN, PUD_DOWN) + RISING).
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
# Печатать текущий уровень каждые N секунд (например 0.25) — видно, меняется ли GPIO при внесении купюры
WATCH_S = float(os.environ.get("MOYKA_WATCH_S", "0"))
if WATCH_S < 0:
    WATCH_S = 0.0

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
    src = f"  линия из gpiofind: {_line_name!r}\n" if _line_name else ""
    print(
        f"Купюры NV10→PC817→GPIO\n"
        f"  chip={CHIP}  line(offset)={LINE}  edge={EDGE}  bias={BIAS}\n"
        f"{src}"
        f"  стартовый уровень: {'HIGH' if prev else 'LOW'}\n"
        f"  UZS за импульс={UZS_PULSE}  debounce={DEBOUNCE_S}s  конец купюры после тишины {IDLE_S}s\n"
        f"  опрос каждые {POLL_S * 1000:.1f} ms{dbg}\n"
        f"Ctrl+C — выход\n"
        f"Подсказка: по умолчанию rising+pull_down как на Pi; если схема наоборот — MOYKA_EDGE=falling. "
        f"Короткие импульсы — MOYKA_POLL_S=0.0005. Нет ни [уровень], ни смены в [watch] — неверная линия: "
        f"gpiofind PIN_40 → MOYKA_GPIO_LINE_NAME=PIN_40. Общий GND: плата и NV10.\n",
        flush=True,
    )
    if WATCH_S > 0:
        print(f"  MOYKA_WATCH_S={WATCH_S}: каждые {WATCH_S}s строка [watch] с уровнем GPIO\n", flush=True)

    pulse_count = 0
    last_pulse_t = 0.0
    last_watch_t = 0.0

    try:
        while True:
            x = bool(gpio.read())
            if WATCH_S > 0:
                tnow = time.time()
                if tnow - last_watch_t >= WATCH_S:
                    last_watch_t = tnow
                    print(f"  [watch] {'HIGH' if x else 'LOW'}", flush=True)
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
