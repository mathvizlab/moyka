"""
Аппаратный ввод для киоска: купюроприёмник (импульсы) и опционально PCF8574 по I2C.

На Raspberry Pi можно использовать RPi.GPIO (BOARD, как в вашем скрипте).
На Radxa Zero RPi.GPIO не работает — варианты:
  • MOYKA_GPIO_BACKEND=gpiod — libgpiod 1.x (как ваш рабочий скрипт, см. MOYKA_PRESET=radxa_zero_gpiod)
  • periphery — /dev/gpiochip* + опрос линии (MOYKA_PRESET=radxa_zero)

Включение: MOYKA_HW=1

Переменные окружения (основные):
  MOYKA_HW=1
  MOYKA_GPIO_BACKEND=auto|rpigpio|gpiod|periphery|mock
      auto: RPi.GPIO → иначе gpiod → иначе periphery
  MOYKA_BILL_UZS_PER_PULSE=1000
  MOYKA_BILL_DEBOUNCE_S=0.03   # как в RPi: импульсы чаще 30 мс не считаем
  MOYKA_BILL_IDLE_S=0.8       # тишина после последнего импульса — конец купюры
  MOYKA_HW_LOOP_S=0.05         # период главного цикла как time.sleep(0.05) на Pi
  MOYKA_I2C_BUS=1
  MOYKA_I2C_ADDR=32          # 0x20
  MOYKA_I2C_ENABLE=0         # 1 — слушать линию INT и читать PCF8574

  # Raspberry Pi (BOARD), если backend=rpigpio:
  MOYKA_RPI_INT_PIN=7
  MOYKA_RPI_BILL_PIN=40

  # Radxa Zero (S905Y2), тот же 40-pin расклад что у Pi — купюра на pin 40, INT PCF на pin 7:
  MOYKA_PRESET=radxa_zero
      → periphery + MOYKA_BILL_MODE=poll (S905Y2: имена GPIOAO_*; см. gpiofind)
  MOYKA_PRESET=radxa_zero2
      → как radxa_zero, но купюры по имени PIN_40 (док. Radxa Zero 2 / GPIOD); линию INT задайте
        через MOYKA_GPIO_INT_NAME или MOYKA_LINE_I2C_INT после gpioinfo
  MOYKA_BILL_MODE=poll|edge   # poll = опрос уровня (по умолчанию для radxa_zero); edge = старый вариант
  MOYKA_GPIO_POLL_MS=0.002    # период опроса линии купюр, сек

  Если установлен gpiofind (пакет gpiod), линии ищутся по имени; иначе задайте вручную.
  В доке Radxa (GPIOD) для Zero 2 у физ. pin 40 имя часто PIN_40 → gpiochip0 offset 7;
  на других Zero встречается GPIOAO_11 и другой gpiochip — сверяйте: gpioinfo | grep PIN_40

  MOYKA_GPIOCHIP=/dev/gpiochip0
  MOYKA_LINE_BILL=11         # пример: GPIOAO_11 на одной из сборок; число смотрите gpiofind/gpioinfo
  MOYKA_LINE_I2C_INT=3       # GPIOAO_3 → физ. pin 7 (FALLING, pull-up, чтение PCF8574)

  Либо явные имена для gpiofind:
  MOYKA_GPIO_BILL_NAME=GPIOAO_11
  MOYKA_GPIO_INT_NAME=GPIOAO_3

  Права: пользователь должен читать /dev/gpiochip* (группа gpio или root).

  # --- Radxa Zero (libgpiod): gpiochip1, offset 11 = купюры, 4 = INT PCF (пример, проверьте gpiofind) ---
  MOYKA_PRESET=radxa_zero_gpiod
      → MOYKA_GPIO_BACKEND=gpiod, chip gpiochip1, линии 11 / 4, I2C шина 1
  MOYKA_GPIOD_CHIP=gpiochip1      # или /dev/gpiochip1
  MOYKA_GPIOD_LINE_BILL=11      # физ. pin 40 → offset 11 (ваша разводка)
  MOYKA_GPIOD_LINE_INT=4          # GPIOAO_4 — INT; пусто / none — только купюры
  (на Radxa проверьте шину: ls /dev/i2c* → MOYKA_I2C_BUS=1 или 7)

  # Кнопки PCF8574: список id кнопок через запятую, бит 0 = младший бит статуса
  MOYKA_PCF_BUTTONS=btn1,btn2,btn3,btn4,btn5,btn6,btn7,btn8

Очереди событий забирает main.timer_loop через drain_hw_events().

Алгоритм счёта купюр/кнопок совпадает с типовым RPi.GPIO (BOARD):
  • купюры: pin 40, PUD_DOWN, событие RISING, софт-дебаунс 30 мс (аналог bouncetime 20 мс на Pi);
  • INT PCF8574: pin 7, PUD_UP, FALLING, чтение I2C (bouncetime на Pi 200 мс — здесь только софт);
  • после последнего импульса пауза MOYKA_BILL_IDLE_S (0.8 с) → сумма = импульсы * MOYKA_BILL_UZS_PER_PULSE.
"""

from __future__ import annotations

import os
import queue
import shutil
import subprocess
import threading
import time
from datetime import timedelta
from typing import Any, Callable

_HW_EVENTS: queue.Queue[tuple[str, Any]] = queue.Queue()
_threads_started = False

BILL_UZS_PER_PULSE = int(os.environ.get("MOYKA_BILL_UZS_PER_PULSE", "1000"))
BILL_DEBOUNCE_S = float(os.environ.get("MOYKA_BILL_DEBOUNCE_S", "0.03"))
BILL_IDLE_S = float(os.environ.get("MOYKA_BILL_IDLE_S", "0.8"))
# Как в скрипте RPi.GPIO: в главном цикле time.sleep(0.05) перед проверкой «тишина после пачки импульсов».
HW_LOOP_SLEEP_S = float(os.environ.get("MOYKA_HW_LOOP_S", "0.05"))

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
        os.environ.setdefault("MOYKA_BILL_MODE", "poll")
        os.environ.setdefault("MOYKA_GPIO_BILL_NAME", "GPIOAO_11")
        os.environ.setdefault("MOYKA_GPIO_INT_NAME", "GPIOAO_3")
        os.environ.setdefault("MOYKA_I2C_ENABLE", "1")
        os.environ.setdefault("MOYKA_I2C_ADDR", "0x20")
        os.environ.setdefault("MOYKA_I2C_BUS", "1")
        if not os.environ.get("MOYKA_LINE_BILL") and not shutil.which("gpiofind"):
            # Как bil.py без gpiofind: /dev/gpiochip1 offset 11 (pin 40 на типичном Radxa Zero).
            os.environ.setdefault("MOYKA_GPIOCHIP", "/dev/gpiochip1")
            os.environ.setdefault("MOYKA_LINE_BILL", "11")
            os.environ.setdefault("MOYKA_LINE_I2C_INT", "3")

    if p in ("radxa_zero2", "radxa-zero-2", "radxa_zero_2"):
        # Док. Radxa GPIOD: gpiofind PIN_40 → часто gpiochip0, offset 7 (не путать с S905Y2 / GPIOAO_11).
        os.environ.setdefault("MOYKA_GPIO_BACKEND", "periphery")
        os.environ.setdefault("MOYKA_BILL_MODE", "poll")
        os.environ.setdefault("MOYKA_GPIO_BILL_NAME", "PIN_40")
        os.environ.setdefault("MOYKA_I2C_ENABLE", "1")
        os.environ.setdefault("MOYKA_I2C_ADDR", "0x20")
        os.environ.setdefault("MOYKA_I2C_BUS", "1")

    if p in ("radxa_zero_gpiod", "radxa_gpiod"):
        os.environ.setdefault("MOYKA_GPIO_BACKEND", "gpiod")
        os.environ.setdefault("MOYKA_GPIOD_CHIP", "gpiochip1")
        os.environ.setdefault("MOYKA_GPIOD_LINE_BILL", "11")
        os.environ.setdefault("MOYKA_GPIOD_LINE_INT", "4")
        os.environ.setdefault("MOYKA_I2C_ENABLE", "1")
        os.environ.setdefault("MOYKA_I2C_ADDR", "0x20")
        os.environ.setdefault("MOYKA_I2C_BUS", "1")


def _gpiod_event_wait(line: Any, timeout_sec: float) -> bool:
    """libgpiod 1.x Python: разные сборки принимают timedelta, sec или nsec."""
    if timeout_sec <= 0:
        td = timedelta(seconds=0)
    else:
        td = timedelta(seconds=timeout_sec)
    try:
        return bool(line.event_wait(td))
    except TypeError:
        pass
    try:
        return bool(line.event_wait(sec=timeout_sec))
    except TypeError:
        pass
    try:
        nsec = max(0, int(timeout_sec * 1e9))
        return bool(line.event_wait(nsec=nsec))
    except TypeError:
        return bool(line.event_wait(timeout_sec))


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
    last_pcf = None
    lock = threading.Lock()

    def on_bill(_ch: Any) -> None:
        nonlocal pulse_count, last_pulse_t
        now = time.time()
        with lock:
            if now - last_pulse_t > BILL_DEBOUNCE_S:
                pulse_count += 1
                last_pulse_t = now

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
            time.sleep(HW_LOOP_SLEEP_S)
            with lock:
                if pulse_count > 0 and (time.time() - last_pulse_t > BILL_IDLE_S):
                    amount = pulse_count * BILL_UZS_PER_PULSE
                    print(f"[moyka-hw] принято {amount} UZS ({pulse_count} имп.)", flush=True)
                    _enqueue_cash_uzs(amount)
                    pulse_count = 0
    finally:
        GPIO.cleanup()


# --- libgpiod 1.x (Radxa — как рабочий скрипт с gpiod.Chip / get_line / event_wait) ---


def _gpiod_request_ev_line(
    gpiod: Any,
    line: Any,
    consumer: str,
    ev_type: Any,
    bias: str | None,
) -> None:
    """Событие на линии + подтяжка как у RPi.GPIO (PUD_DOWN / PUD_UP), если версия gpiod поддерживает флаги."""
    flags = 0
    if bias == "pull_down":
        for attr in ("LINE_REQ_FLAG_BIAS_PULL_DOWN", "LINE_REQUEST_FLAG_BIAS_PULL_DOWN"):
            if hasattr(gpiod, attr):
                flags |= int(getattr(gpiod, attr))
                break
    elif bias == "pull_up":
        for attr in ("LINE_REQ_FLAG_BIAS_PULL_UP", "LINE_REQUEST_FLAG_BIAS_PULL_UP"):
            if hasattr(gpiod, attr):
                flags |= int(getattr(gpiod, attr))
                break
    try:
        if flags:
            line.request(consumer=consumer, type=ev_type, flags=flags)
        else:
            line.request(consumer=consumer, type=ev_type)
    except TypeError:
        line.request(consumer=consumer, type=ev_type)


def _run_gpiod() -> None:
    import gpiod  # type: ignore

    chip_arg = os.environ.get("MOYKA_GPIOD_CHIP", "gpiochip1").strip()
    chip_path = chip_arg if chip_arg.startswith("/dev/") else f"/dev/{chip_arg}"

    try:
        bill_off = int(os.environ.get("MOYKA_GPIOD_LINE_BILL", "11"), 0)
    except ValueError:
        bill_off = 8

    raw_int = os.environ.get("MOYKA_GPIOD_LINE_INT", "4").strip().lower()
    int_off: int | None
    if raw_int in ("", "none", "-1"):
        int_off = None
    else:
        try:
            int_off = int(raw_int, 0)
        except ValueError:
            int_off = 4

    i2c_on = os.environ.get("MOYKA_I2C_ENABLE", "").strip().lower() in ("1", "true", "yes")
    bit_map = _parse_pcf_button_map()

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

    if int_off is not None and bus is None:
        int_off = None

    try:
        chip = gpiod.Chip(chip_path)
    except Exception as err:
        print(f"[moyka-hw] gpiod.Chip({chip_path}): {err}", flush=True)
        _run_mock()
        return

    bill_line = chip.get_line(bill_off)
    try:
        _gpiod_request_ev_line(
            gpiod,
            bill_line,
            "moyka_nv10",
            gpiod.LINE_REQ_EV_RISING_EDGE,
            "pull_down",
        )
    except Exception as err:
        print(f"[moyka-hw] gpiod bill line {bill_off}: {err}", flush=True)
        try:
            chip.close()
        except Exception:
            pass
        _run_mock()
        return

    int_line = None
    if int_off is not None and bus is not None:
        try:
            int_line = chip.get_line(int_off)
            _gpiod_request_ev_line(
                gpiod,
                int_line,
                "moyka_pcf",
                gpiod.LINE_REQ_EV_FALLING_EDGE,
                "pull_up",
            )
        except Exception as err:
            print(f"[moyka-hw] gpiod INT line {int_off}: {err} — только купюры", flush=True)
            int_line = None

    pulse_count = 0
    last_pulse_t = 0.0
    last_pcf = None
    lock = threading.Lock()

    def bill_hit() -> None:
        nonlocal pulse_count, last_pulse_t
        now = time.time()
        with lock:
            if now - last_pulse_t > BILL_DEBOUNCE_S:
                pulse_count += 1
                last_pulse_t = now

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
        f"[moyka-hw] gpiod (как RPi.GPIO): {chip_path} bill={bill_off} RISING+PULL_DOWN "
        f"int={int_off if int_line else '—'} FALLING+PULL_UP  debounce={BILL_DEBOUNCE_S}s  "
        f"idle={BILL_IDLE_S}s  loop={HW_LOOP_SLEEP_S}s",
        flush=True,
    )

    try:
        while True:
            if int_line is not None and _gpiod_event_wait(int_line, 0.01):
                try:
                    int_line.event_read()
                except Exception:
                    pass
                int_hit()

            if _gpiod_event_wait(bill_line, 0.001):
                try:
                    bill_line.event_read()
                except Exception:
                    pass
                bill_hit()

            with lock:
                if pulse_count > 0 and (time.time() - last_pulse_t > BILL_IDLE_S):
                    amount = pulse_count * BILL_UZS_PER_PULSE
                    print(f"[moyka-hw] принято {amount} UZS ({pulse_count} имп.)", flush=True)
                    _enqueue_cash_uzs(amount)
                    pulse_count = 0

            time.sleep(HW_LOOP_SLEEP_S)
    finally:
        try:
            bill_line.release()
        except Exception:
            pass
        if int_line is not None:
            try:
                int_line.release()
            except Exception:
                pass
        try:
            chip.close()
        except Exception:
            pass


# --- python-periphery (Radxa и др. Linux с /dev/gpiochip*) ---


def _periphery_bias(name: str, default: str) -> str:
    v = os.environ.get(name, default).strip().lower()
    if v in ("pull_down", "pull_up", "disable", "default"):
        return v
    return default


def _run_periphery() -> None:
    from periphery import GPIO  # type: ignore

    i2c_on = os.environ.get("MOYKA_I2C_ENABLE", "").strip().lower() in ("1", "true", "yes")
    bit_map = _parse_pcf_button_map()
    bill_mode = os.environ.get("MOYKA_BILL_MODE", "poll").strip().lower()
    if bill_mode not in ("poll", "edge"):
        bill_mode = "poll"
    try:
        poll_ms = float(os.environ.get("MOYKA_GPIO_POLL_MS", "0.002"))
    except ValueError:
        poll_ms = 0.002
    poll_ms = max(0.0005, min(poll_ms, 0.05))

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

    bill_bias = _periphery_bias("MOYKA_BILL_BIAS", "pull_down")
    int_bias = _periphery_bias("MOYKA_INT_BIAS", "pull_up")
    bill_edge = "none" if bill_mode == "poll" else "rising"
    int_edge = "none" if bill_mode == "poll" else "falling"

    try:
        bill_gpio = GPIO(bill_chip, bill_line_no, "in", bias=bill_bias, edge=bill_edge)
    except PermissionError as err:
        print(
            f"[moyka-hw] нет доступа к {bill_chip}: {err}\n"
            "  Запустите от root или добавьте пользователя в группу «gpio», "
            "проверьте права на /dev/gpiochip*",
            flush=True,
        )
        _run_mock()
        return
    except Exception as err:
        print(f"[moyka-hw] не удалось открыть линию купюр {bill_chip}:{bill_line_no}: {err}", flush=True)
        _run_mock()
        return

    int_gpio = None
    if bus is not None and int_line_no is not None:
        try:
            int_gpio = GPIO(int_chip, int_line_no, "in", bias=int_bias, edge=int_edge)
        except Exception as err:
            print(f"[moyka-hw] INT GPIO не открыт: {err} — только купюры", flush=True)

    pulse_count = 0
    last_pulse_t = 0.0
    last_pcf = None
    lock = threading.Lock()

    def bill_hit() -> None:
        nonlocal pulse_count, last_pulse_t
        now = time.time()
        with lock:
            if now - last_pulse_t > BILL_DEBOUNCE_S:
                pulse_count += 1
                last_pulse_t = now

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

    try:
        lvl = bill_gpio.read()
    except Exception as err:
        print(f"[moyka-hw] первое чтение линии купюр: {err}", flush=True)
        bill_gpio.close()
        _run_mock()
        return

    print(
        f"[moyka-hw] periphery (алгоритм как RPi.GPIO BOARD): купюры {bill_chip} line {bill_line_no} "
        f"mode={bill_mode} bias={bill_bias} (ожидаем RISING после LOW) "
        f"старт={'HIGH' if lvl else 'LOW'}; INT {int_chip if int_gpio else '—'} "
        f"{int_line_no if int_gpio else ''}  debounce={BILL_DEBOUNCE_S}s idle={BILL_IDLE_S}s",
        flush=True,
    )

    try:
        if bill_mode == "poll":
            prev_bill = bool(lvl)
            prev_int = True
            if int_gpio:
                try:
                    prev_int = bool(int_gpio.read())
                except Exception:
                    prev_int = True
            while True:
                try:
                    high = bool(bill_gpio.read())
                except Exception:
                    time.sleep(0.05)
                    continue
                if high and not prev_bill:
                    bill_hit()
                prev_bill = high

                if int_gpio:
                    try:
                        ih = bool(int_gpio.read())
                    except Exception:
                        ih = prev_int
                    if not ih and prev_int:
                        int_hit()
                    prev_int = ih

                with lock:
                    if pulse_count > 0 and (time.time() - last_pulse_t > BILL_IDLE_S):
                        amount = pulse_count * BILL_UZS_PER_PULSE
                        print(f"[moyka-hw] принято {amount} UZS ({pulse_count} имп.)", flush=True)
                        _enqueue_cash_uzs(amount)
                        pulse_count = 0

                time.sleep(poll_ms)
        else:
            while True:
                if bill_gpio.poll(0.05):
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
                    if pulse_count > 0 and (time.time() - last_pulse_t > BILL_IDLE_S):
                        amount = pulse_count * BILL_UZS_PER_PULSE
                        print(f"[moyka-hw] принято {amount} UZS ({pulse_count} имп.)", flush=True)
                        _enqueue_cash_uzs(amount)
                        pulse_count = 0
                time.sleep(HW_LOOP_SLEEP_S)
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
    elif backend == "gpiod":
        target = _run_gpiod
    elif backend == "periphery":
        target = _run_periphery
    else:
        try:
            import RPi.GPIO  # type: ignore  # noqa: F401

            target = _run_rpi_gpio
        except Exception:
            try:
                import gpiod  # type: ignore  # noqa: F401

                target = _run_gpiod
            except Exception:
                try:
                    import periphery  # type: ignore  # noqa: F401

                    target = _run_periphery
                except Exception:
                    print(
                        "[moyka-hw] нет RPi.GPIO, gpiod и periphery — режим mock",
                        flush=True,
                    )
                    target = _run_mock

    th = threading.Thread(target=target, name="moyka-hw", daemon=True)
    th.start()
