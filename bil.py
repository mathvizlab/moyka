

from __future__ import annotations

import os
import sys
import time

try:
    from periphery import GPIO
except ImportError:
    print(
        "Установите: pip install python-periphery\n"
        "или пакет из Debian для periphery, затем снова запустите этот файл.",
        file=sys.stderr,
    )
    sys.exit(1)

# --- настройки из окружения ---
CHIP = os.environ.get("MOYKA_GPIOCHIP", "/dev/gpiochip1").strip()
try:
    LINE = int(os.environ.get("MOYKA_GPIO_LINE", os.environ.get("MOYKA_LINE_BILL", "8")), 0)
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

if POLL_S < 0.0005:
    POLL_S = 0.0005
if POLL_S > 0.05:
    POLL_S = 0.05


def main() -> None:
    gpio = GPIO(CHIP, LINE, "in", bias=BIAS, edge="none")
    prev = bool(gpio.read())
    print(
        f"Купюры NV10→PC817→GPIO\n"
        f"  chip={CHIP}  line(offset)={LINE}  edge={EDGE}  bias={BIAS}\n"
        f"  стартовый уровень: {'HIGH' if prev else 'LOW'}\n"
        f"  UZS за импульс={UZS_PULSE}  debounce={DEBOUNCE_S}s  конец купюры после тишины {IDLE_S}s\n"
        f"Ctrl+C — выход\n",
        flush=True,
    )

    pulse_count = 0
    last_pulse_t = 0.0

    try:
        while True:
            x = bool(gpio.read())
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
