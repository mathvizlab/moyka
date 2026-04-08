"""
Аппаратный ввод для киоска: купюроприёмник (импульсы) и опционально PCF8574 по I2C.

На Raspberry Pi можно использовать RPi.GPIO (BOARD, как в вашем скрипте).
На Radxa Zero RPi.GPIO не работает — используйте python-periphery + sysfs/gpiochip
(см. переменные MOYKA_GPIOCHIP / MOYKA_LINE_*).

Включение: MOYKA_HW=1

Переменные окружения (основные):
  MOYKA_HW=1
  MOYKA_GPIO_BACKEND=auto|rpigpio|periphery|mock
      auto: RPi.GPIO если доступен, иначе periphery
  MOYKA_BILL_UZS_PER_PULSE=1000
  MOYKA_BILL_DEBOUNCE_S=0.03
  MOYKA_BILL_IDLE_S=0.8
  MOYKA_I2C_BUS=1
  MOYKA_I2C_ADDR=32          # 0x20
  MOYKA_I2C_ENABLE=0         # 1 — слушать линию INT и читать PCF8574

  # Raspberry Pi (BOARD), если backend=rpigpio:
  MOYKA_RPI_INT_PIN=7
  MOYKA_RPI_BILL_PIN=40

  # Radxa Zero (S905Y2), тот же 40-pin расклад что у Pi — купюра на pin 40, INT PCF на pin 7:
  MOYKA_PRESET=radxa_zero
      → MOYKA_GPIO_BACKEND=periphery, I2C включён, имена линий GPIOAO_11 / GPIOAO_3
      (см. https://docs.radxa.com/en/zero/zero/hardware-design/hardware-interface )
      Если установлен gpiofind (пакет gpiod), линии ищутся по имени; иначе задайте вручную:
  MOYKA_GPIOCHIP=/dev/gpiochip0
  MOYKA_LINE_BILL=11         # GPIOAO_11 → физ. pin 40 (импульсы купюр, RISING, pull-down)
  MOYKA_LINE_I2C_INT=3       # GPIOAO_3 → физ. pin 7 (FALLING, pull-up, чтение PCF8574)

  Либо явные имена для gpiofind:
  MOYKA_GPIO_BILL_NAME=GPIOAO_11
  MOYKA_GPIO_INT_NAME=GPIOAO_3

  # Кнопки PCF8574: список id кнопок через запятую, бит 0 = младший бит статуса
  MOYKA_PCF_BUTTONS=btn1,btn2,btn3,btn4,btn5,btn6,btn7,btn8

Очереди событий забирает main.timer_loop через drain_hw_events().
"""

from __future__ import annotations

import os
import queue
import shutil
import subprocess
import threading
import time
from typing import Any, Callable

_HW_EVENTS: queue.Queue[tuple[str, Any]] = queue.Queue()
_threads_started = False

BILL_UZS_PER_PULSE = int(os.environ.get("MOYKA_BILL_UZS_PER_PULSE", "1000"))
BILL_DEBOUNCE_S = float(os.environ.get("MOYKA_BILL_DEBOUNCE_S", "0.03"))
BILL_IDLE_S = float(os.environ.get("MOYKA_BILL_IDLE_S", "0.8"))

I2C_BUS = int(os.environ.get("MOYKA_I2C_BUS", "1"))
try:
    I2C_ADDR = int(os.environ.get("MOYKA_I2C_ADDR", "0x20"), 0)
except ValueError:
    I2C_ADDR = 0x20


def hw_enabled() -> bool:
    v = os.environ.get("MOYKA_HW", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def drain_hw_events() -> list[tuple[str, Any]]:
    """Непусто только из главного цикла NiceGUI (timer_loop)."""
    out: list[tuple[str, Any]] = []
    try:
        while True:
            out.append(_HW_EVENTS.get_nowait())
    except queue.Empty:
        pass
    return out


def _enqueue_cash_uzs(amount: int) -> None:
    if amount > 0:
        _HW_EVENTS.put(("cash", int(amount)))


def _enqueue_button(bid: str) -> None:
    if bid:
        _HW_EVENTS.put(("btn", str(bid)))


def _parse_pcf_button_map() -> list[str | None]:
    raw = os.environ.get("MOYKA_PCF_BUTTONS", "").strip()
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(",")]
    return [p if p else None for p in parts]


def _gpiofind_line(name: str) -> tuple[str, int] | None:
    """Сопоставить имя линии из Device Tree (например GPIOAO_11) с /dev/gpiochipN + offset."""
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


def _apply_hw_presets() -> None:
    """Подставить типичные настройки под конкретные платы (можно переопределить env)."""
    p = os.environ.get("MOYKA_PRESET", "").strip().lower()
    if p in ("radxa_zero", "radxa_zero_s905y2", "s905y2"):
        os.environ.setdefault("MOYKA_GPIO_BACKEND", "periphery")
        os.environ.setdefault("MOYKA_GPIO_BILL_NAME", "GPIOAO_11")
        os.environ.setdefault("MOYKA_GPIO_INT_NAME", "GPIOAO_3")
        os.environ.setdefault("MOYKA_I2C_ENABLE", "1")
        os.environ.setdefault("MOYKA_I2C_ADDR", "0x20")
        os.environ.setdefault("MOYKA_I2C_BUS", "1")
        if not os.environ.get("MOYKA_LINE_BILL") and not shutil.which("gpiofind"):
            os.environ.setdefault("MOYKA_GPIOCHIP", "/dev/gpiochip0")
            os.environ.setdefault("MOYKA_LINE_BILL", "11")
            os.environ.setdefault("MOYKA_LINE_I2C_INT", "3")


def _emit_pcf_delta(prev_byte: int, new_byte: int, bit_map: list[str | None]) -> None:
    """Активный низ: нажатие даёт переход бита 1 -> 0."""
    if not bit_map:
        return
    changed = prev_byte ^ new_byte
    if changed == 0:
        return
    for i, bid in enumerate(bit_map):
        if not bid or i > 7:
            continue
        mask = 1 << i
        if (changed & mask) and (prev_byte & mask) and not (new_byte & mask):
            _enqueue_button(bid)


# --- RPi.GPIO (только Raspberry Pi) ---


def _run_rpi_gpio() -> None:
    import RPi.GPIO as GPIO  # type: ignore

    int_pin = int(os.environ.get("MOYKA_RPI_INT_PIN", "7"))
    bill_pin = int(os.environ.get("MOYKA_RPI_BILL_PIN", "40"))
    i2c_on = os.environ.get("MOYKA_I2C_ENABLE", "").strip().lower() in ("1", "true", "yes")
    bit_map = _parse_pcf_button_map()

    try:
        import smbus2  # type: noqa: F401
    except ImportError:
        smbus2 = None  # type: ignore

    bus = None
    if i2c_on and smbus2:
        try:
            bus = smbus2.SMBus(I2C_BUS)
        except Exception as err:
            print(f"[moyka-hw] I2C SMBus({I2C_BUS}): {err}", flush=True)
            bus = None
    elif i2c_on:
        print("[moyka-hw] smbus2 не установлен — I2C отключён", flush=True)

    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(int_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(bill_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    pulse_count = 0
    last_pulse_t = 0.0
    processing = False
    last_pcf = None
    lock = threading.Lock()

    def on_bill(_ch: Any) -> None:
        nonlocal pulse_count, last_pulse_t, processing
        now = time.time()
        with lock:
            if now - last_pulse_t > BILL_DEBOUNCE_S:
                pulse_count += 1
                last_pulse_t = now
                processing = True

    def on_int(_ch: Any) -> None:
        nonlocal last_pcf
        if bus is None:
            return
        try:
            status = bus.read_byte(I2C_ADDR)
        except Exception as err:
            print(f"[moyka-hw] I2C read: {err}", flush=True)
            return
        print(f"[moyka-hw] PCF8574 {status:08b}", flush=True)
        with lock:
            if last_pcf is not None and bit_map:
                _emit_pcf_delta(last_pcf, status, bit_map)
            last_pcf = status

    GPIO.add_event_detect(bill_pin, GPIO.RISING, callback=on_bill, bouncetime=20)
    if i2c_on and bus is not None:
        GPIO.add_event_detect(int_pin, GPIO.FALLING, callback=on_int, bouncetime=200)

    print("[moyka-hw] RPi.GPIO: bill + I2C слушатель запущен", flush=True)
    try:
        while True:
            time.sleep(0.05)
            with lock:
                if processing and (time.time() - last_pulse_t > BILL_IDLE_S):
                    amount = pulse_count * BILL_UZS_PER_PULSE
                    print(f"[moyka-hw] принято {amount} UZS ({pulse_count} имп.)", flush=True)
                    _enqueue_cash_uzs(amount)
                    pulse_count = 0
                    processing = False
    finally:
        GPIO.cleanup()


# --- python-periphery (Radxa и др. Linux с /dev/gpiochip*) ---


def _run_periphery() -> None:
    from periphery import GPIO  # type: ignore

    i2c_on = os.environ.get("MOYKA_I2C_ENABLE", "").strip().lower() in ("1", "true", "yes")
    bit_map = _parse_pcf_button_map()

    bill_name = os.environ.get("MOYKA_GPIO_BILL_NAME", "").strip()
    int_name = os.environ.get("MOYKA_GPIO_INT_NAME", "").strip()
    default_chip = os.environ.get("MOYKA_GPIOCHIP", "/dev/gpiochip0")

    bill_chip = default_chip
    bill_line_no: int | None = None
    raw_bill = os.environ.get("MOYKA_LINE_BILL", "").strip()
    if raw_bill:
        try:
            bill_line_no = int(raw_bill, 0)
        except ValueError:
            bill_line_no = None
    if bill_line_no is None and bill_name:
        found = _gpiofind_line(bill_name)
        if found:
            bill_chip, bill_line_no = found
    if bill_line_no is None:
        print(
            "[moyka-hw] задайте MOYKA_LINE_BILL или MOYKA_GPIO_BILL_NAME "
            "(для Radxa Zero S905Y2: MOYKA_PRESET=radxa_zero или LINE_BILL=11 + INT=3)",
            flush=True,
        )
        _run_mock()
        return

    try:
        import smbus2
    except ImportError:
        smbus2 = None  # type: ignore

    bus = None
    if i2c_on and smbus2:
        try:
            bus = smbus2.SMBus(I2C_BUS)
        except Exception as err:
            print(f"[moyka-hw] I2C SMBus({I2C_BUS}): {err}", flush=True)

    int_chip = bill_chip
    int_line_no: int | None = None
    if i2c_on and bus is not None:
        raw_int = os.environ.get("MOYKA_LINE_I2C_INT", "").strip()
        if raw_int:
            try:
                int_line_no = int(raw_int, 0)
            except ValueError:
                int_line_no = None
            int_chip = os.environ.get("MOYKA_GPIOCHIP", bill_chip)
        elif int_name:
            found_i = _gpiofind_line(int_name)
            if found_i:
                int_chip, int_line_no = found_i
            else:
                print(
                    f"[moyka-hw] gpiofind «{int_name}» не удался — PCF8574 отключён",
                    flush=True,
                )
        if int_line_no is None and (raw_int or int_name):
            print("[moyka-hw] MOYKA_I2C_ENABLE: не удалось определить линию INT — только купюры", flush=True)

    bill_gpio = GPIO(bill_chip, bill_line_no, "in", bias="pull_down", edge="rising")
    int_gpio = None
    if bus is not None and int_line_no is not None:
        int_gpio = GPIO(int_chip, int_line_no, "in", bias="pull_up", edge="falling")

    pulse_count = 0
    last_pulse_t = 0.0
    processing = False
    last_pcf = None
    lock = threading.Lock()

    def bill_hit() -> None:
        nonlocal pulse_count, last_pulse_t, processing
        now = time.time()
        with lock:
            if now - last_pulse_t > BILL_DEBOUNCE_S:
                pulse_count += 1
                last_pulse_t = now
                processing = True

    def int_hit() -> None:
        nonlocal last_pcf
        if bus is None:
            return
        try:
            status = bus.read_byte(I2C_ADDR)
        except Exception as err:
            print(f"[moyka-hw] I2C read: {err}", flush=True)
            return
        print(f"[moyka-hw] PCF8574 {status:08b}", flush=True)
        with lock:
            if last_pcf is not None and bit_map:
                _emit_pcf_delta(last_pcf, status, bit_map)
            last_pcf = status

    print(
        f"[moyka-hw] periphery: купюры {bill_chip} line {bill_line_no} "
        f"(как RPi BOARD pin 40, RISING); INT {int_chip if int_gpio else '—'} "
        f"{int_line_no if int_gpio else ''}",
        flush=True,
    )

    try:
        while True:
            # Ждём событие на любом из пинов (короткий poll по очереди)
            if bill_gpio.poll(BILL_DEBOUNCE_S if not int_gpio else 0.05):
                try:
                    bill_gpio.read_event()
                except Exception:
                    pass
                bill_hit()
            if int_gpio and int_gpio.poll(0.01):
                try:
                    int_gpio.read_event()
                except Exception:
                    pass
                int_hit()

            with lock:
                if processing and (time.time() - last_pulse_t > BILL_IDLE_S):
                    amount = pulse_count * BILL_UZS_PER_PULSE
                    print(f"[moyka-hw] принято {amount} UZS ({pulse_count} имп.)", flush=True)
                    _enqueue_cash_uzs(amount)
                    pulse_count = 0
                    processing = False
    finally:
        bill_gpio.close()
        if int_gpio:
            int_gpio.close()


def _run_mock() -> None:
    print("[moyka-hw] mock: импульсов нет (тест MOYKA_HW=1 без GPIO)", flush=True)
    while True:
        time.sleep(3600)


def start() -> None:
    global _threads_started
    if _threads_started:
        return
    if not hw_enabled():
        print("[moyka-hw] выкл. Включите MOYKA_HW=1 на Radxa/Pi", flush=True)
        return
    _apply_hw_presets()
    _threads_started = True
    backend = os.environ.get("MOYKA_GPIO_BACKEND", "auto").strip().lower()

    target: Callable[[], None]
    if backend == "mock":
        target = _run_mock
    elif backend == "rpigpio":
        target = _run_rpi_gpio
    elif backend == "periphery":
        target = _run_periphery
    else:
        try:
            import RPi.GPIO  # type: ignore  # noqa: F401

            target = _run_rpi_gpio
        except Exception:
            try:
                import periphery  # type: ignore  # noqa: F401

                target = _run_periphery
            except Exception:
                print("[moyka-hw] нет RPi.GPIO и periphery — режим mock", flush=True)
                target = _run_mock

    th = threading.Thread(target=target, name="moyka-hw", daemon=True)
    th.start()
