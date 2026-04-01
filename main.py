import gc
import asyncio
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from nicegui import app, events, ui

try:
    from icons import SVG_PATHS
except Exception:
    SVG_PATHS = {f"btn{i}": "M500 100l100 800h-200z" for i in range(1, 16)}

# Fallback-видео, если для услуги нет файла в static/tutorials/
VIDEO_SRC = "/static/promo.mp4"

gc.collect()

def get_svg_path(bid):
    return SVG_PATHS.get(bid) or "M500 200a300 300 0 1 0 0.001 0z"
# s
# --- БЛОК ФУНКЦИЙ ДЛЯ КАЖДОЙ КНОПК
# Здесь прописывай логику для каждой кнопк отдельно
def action_btn1(): print("FOAM (Пена) запущена")
def action_btn2(): print("WAX (Воск) запущен")
def action_btn3(): print("WATER (Вода) запущена")
def action_btn4(): print("AIR (Воздух) запущен")
def action_btn5(): print("OSMOS запущен")
def action_btn6(): print("TURBO запущен")
def action_btn7(): print("SHAMPOO запущен")
def action_btn8(): print("POLISH запущен")
def action_btn9(): print("STEAM запущен")
def action_btn10(): print("VACUUM запущен")
def action_btn11(): print("WHEELS запущен")
def action_btn12(): print("DRY запущен")
def action_btn13(): print("SMELL запущен")
def action_btn14(): print("WASH запущен")

# Карта соответствия: ID кнопки -> Функция
BUTTON_ACTIONS = {
    "btn1": action_btn1,
    "btn2": action_btn2,
    "btn3": action_btn3,
    "btn4": action_btn4,
    "btn5": action_btn5,
    "btn6": action_btn6,
    "btn7": action_btn7,
    "btn8": action_btn8,
    "btn9": action_btn9,
    "btn10": action_btn10,
    "btn11": action_btn11,
    "btn12": action_btn12,
    "btn13": action_btn13,
    "btn14": action_btn14,
}

# --- SERVICE MAPPING ---
# Здесь прописывай названия для каждой кнопки
SERVICE_NAMES = {
    "btn1": "FOAM", "btn2": "WAX", "btn3": "WATER", "btn4": "AIR", "btn5": "OSMOS",
    "btn6": "TURBO", "btn7": "SHAMPOO", "btn8": "POLISH", "btn9": "STEAM", "btn10": "VACUUM",
    "btn11": "WHEELS", "btn12": "DRY", "btn13": "SMELL", "btn14": "WASH"
}

# Порядок кнопок услуг на сетке (без паузы); названия на экране: service_display_names или перевод t(bid)
service_button_order = list(SERVICE_NAMES.keys())
service_display_names: dict[str, str] = {}
service_button_visible = {bid: True for bid in service_button_order}

# Готово под ролики: static/tutorials/btn2.mp4 … btn14.mp4 (имя = id кнопки). FOAM — assets/foam.mp4.
TUTORIAL_VIDEO_BY_SERVICE = {bid: f"/static/tutorials/{bid}.mp4" for bid in SERVICE_NAMES}
TUTORIAL_VIDEO_BY_SERVICE["btn1"] = "/assets/foam.mp4"

app.add_static_files("/assets", str(Path(__file__).resolve().parent / "assets"))

# --- TRANSLATIONS (ENG, RUS, UZB) ---
LANGS = ["eng", "rus", "uzb"]
current_lang = ["eng"]

TRANSLATIONS = {
    "eng": {
        "menu_lang": "Language", "menu_qr": "QR", "menu_cash": "Cash", "menu_info": "Info", "tab_lang_title": "Language",
        "tab_revenue": "REVENUE DASHBOARD", "tab_price": "PRICE CONFIGURATION",
        "price_per_min": "Price / minute (UZS):", "save": "SAVE", "total": "TOTAL",
        "choose_mode": "CHOOSE MODE", "start": "START", "stop": "STOP", "time_unit": "TIME",
        "selected": "Selected", "config_saved": "configuration saved", "price_positive": "Price must be positive", "invalid_input": "Invalid input",
        "btn1": "FOAM", "btn2": "WAX", "btn3": "WATER", "btn4": "AIR", "btn5": "OSMOS",
        "btn6": "TURBO", "btn7": "SHAMPOO", "btn8": "POLISH", "btn9": "STEAM", "btn10": "VACUUM",
        "btn11": "WHEELS", "btn12": "DRY", "btn13": "SMELL", "btn14": "WASH",
        "lang_eng": "English", "lang_rus": "Русский", "lang_uzb": "O'zbekcha",
        "menu_bonus": "Bonus", "menu_free_pause": "Free pause",
        "tab_bonus": "BONUS (%)", "tab_free_pause": "FREE PAUSE",
        "free_pause_label": "Free pause (seconds)",
        "free_pause_hint": "N seconds: pause is free (no time/money). Then the wash resumes automatically on the same service. 0 = pause until Start.",
        "auto_resumed": "Free pause ended — wash running",
        "bonus_label": "Bonus (%)", "bonus_hint": "Extra +(bonus)% on top-up only (пополнение). Not applied to per-second wash billing.",
        "bonus_saved": "Bonus saved", "pause_saved": "Free pause saved",
        "topup_done": "Top-up applied", "topup_need_service": "Select a wash mode first",
        "menu_display": "Display", "tab_display": "MAIN SCREEN",
        "disp_show_timer": "Show countdown (time) in header",
        "disp_show_balance": "Show balance (UZS) in header",
        "disp_services": "Service buttons on the grid",
        "disp_hint": "Uncheck to hide. Pause is always shown.",
        "disp_saved": "Display settings saved",
        "menu_services": "Services", "tab_services": "SERVICES (NAMES)",
        "services_hint": "Custom title on the main screen. Empty field = use language pack name. Add = full button like the others (price, timer, revenue).",
        "services_save_names": "Apply titles", "service_add": "Add service",
        "new_service_name": "New service", "services_min_one": "At least one service is required",
        "services_order_note": "Technical id (video: static/tutorials/<id>.mp4)",
    },
    "rus": {
        "menu_lang": "Язык", "menu_qr": "QR", "menu_cash": "Касса", "menu_info": "Инфо", "tab_lang_title": "Язык",
        "tab_revenue": "ВЫРУЧКА", "tab_price": "НАСТРОЙКА ЦЕН",
        "price_per_min": "Цена / мин (UZS):", "save": "СОХРАНИТЬ", "total": "ИТОГО",
        "choose_mode": "ВЫБЕРИТЕ РЕЖИМ", "start": "СТАРТ", "stop": "СТОП", "time_unit": "ВРЕМЯ",
        "selected": "Выбрано", "config_saved": "настройки сохранены", "price_positive": "Цена должна быть положительной", "invalid_input": "Неверный ввод",
        "btn1": "Пена", "btn2": "Воск", "btn3": "Вода", "btn4": "Воздух", "btn5": "Осмос",
        "btn6": "Турбо", "btn7": "Шампунь", "btn8": "Полироль", "btn9": "Пар", "btn10": "Пылесос",
        "btn11": "Колёса", "btn12": "Сушка", "btn13": "Аромат", "btn14": "Мойка",
        "lang_eng": "English", "lang_rus": "Русский", "lang_uzb": "O'zbekcha",
        "menu_bonus": "Бонус", "menu_free_pause": "Бесплатная пауза",
        "tab_bonus": "БОНУС (%)", "tab_free_pause": "БЕСПЛАТНАЯ ПАУЗА",
        "free_pause_label": "Бесплатная пауза (сек)",
        "free_pause_hint": "N сек — пауза бесплатно (время и деньги не идут). Потом мойка сама продолжается на том же режиме. 0 — до кнопки Старт.",
        "auto_resumed": "Пауза закончилась — мойка снова идёт",
        "bonus_label": "Бонус (%)", "bonus_hint": "Доп. +(бонус)% только при пополнении. К посекундной мойке не относится.",
        "bonus_saved": "Бонус сохранён", "pause_saved": "Пауза сохранена",
        "topup_done": "Пополнение выполнено", "topup_need_service": "Сначала выберите режим",
        "menu_display": "Экран", "tab_display": "ГЛАВНЫЙ ЭКРАН",
        "disp_show_timer": "Показывать таймер в шапке",
        "disp_show_balance": "Показывать баланс (UZS) в шапке",
        "disp_services": "Кнопки услуг в сетке",
        "disp_hint": "Снимите галочку, чтобы скрыть. Пауза всегда видна.",
        "disp_saved": "Настройки экрана сохранены",
        "menu_services": "Услуги", "tab_services": "УСЛУГИ (НАЗВАНИЯ)",
        "services_hint": "Свой заголовок на главном экране. Пустое поле — имя из языка. Добавить — полноценная кнопка (цена, таймер, выручка).",
        "services_save_names": "Применить названия", "service_add": "Добавить услугу",
        "new_service_name": "Новая услуга", "services_min_one": "Нужна хотя бы одна услуга",
        "services_order_note": "Технический id (ролик static/tutorials/<id>.mp4)",
    },
    "uzb": {
        "menu_lang": "Til", "menu_qr": "QR", "menu_cash": "Kassa", "menu_info": "Ma'lumot", "tab_lang_title": "Til",
        "tab_revenue": "DAROMAD", "tab_price": "NARXLAR",
        "price_per_min": "Narx / min (UZS):", "save": "SAQLASH", "total": "JAMI",
        "choose_mode": "REJIMNI TANLANG", "start": "BOSHLASH", "stop": "TO'XTATISH", "time_unit": "VAQT",
        "selected": "Tanlangan", "config_saved": "sozlamalar saqlandi", "price_positive": "Narx musbat bo'lishi kerak", "invalid_input": "Noto'g'ri kiritish",
        "btn1": "Ko'pik", "btn2": "Momiq", "btn3": "Suv", "btn4": "Havo", "btn5": "Osmos",
        "btn6": "Turbo", "btn7": "Shampun", "btn8": "Politur", "btn9": "Bug'", "btn10": "Changyutgich",
        "btn11": "G'ildiraklar", "btn12": "Quritish", "btn13": "Hidi", "btn14": "Yuvish",
        "lang_eng": "English", "lang_rus": "Русский", "lang_uzb": "O'zbekcha",
        "menu_bonus": "Bonus", "menu_free_pause": "Bepul pauza",
        "tab_bonus": "BONUS (%)", "tab_free_pause": "BEPUL PAUZA",
        "free_pause_label": "Bepul pauza (sekund)",
        "free_pause_hint": "N sek — pauza bepul. Keyin avtomatik davom etadi. 0 — Startgacha.",
        "auto_resumed": "Pauza tugadi — yuvish davom etadi",
        "bonus_label": "Bonus (%)", "bonus_hint": "Faqat to'ldirishda +(bonus)% qo'shimcha. Sekundlik yuvish tarifiga ta'sir qilmaydi.",
        "bonus_saved": "Bonus saqlandi", "pause_saved": "Pauza saqlandi",
        "topup_done": "To'ldirildi", "topup_need_service": "Avval rejimni tanlang",
        "menu_display": "Displey", "tab_display": "ASOSIY EKRAN",
        "disp_show_timer": "Sarlavhada taymerni ko'rsatish",
        "disp_show_balance": "Sarlavhada balans (UZS) ko'rsatish",
        "disp_services": "Xizmat tugmalari panjarada",
        "disp_hint": "Yashirish uchun belgini olib tashlang. Pauza har doim ko'rinadi.",
        "disp_saved": "Displey sozlamalari saqlandi",
        "menu_services": "Xizmatlar", "tab_services": "XIZMATLAR (NOMLAR)",
        "services_hint": "Asosiy ekrandagi sarlavha. Bo'sh = til paketidagi nom. Qo'shish — to'liq tugma (narx, taymer, daromad).",
        "services_save_names": "Nomlarni qo'llash", "service_add": "Xizmat qo'shish",
        "new_service_name": "Yangi xizmat", "services_min_one": "Kamida bitta xizmat kerak",
        "services_order_note": "Texnik id (video static/tutorials/<id>.mp4)",
    },
}

def t(key):
    return TRANSLATIONS.get(current_lang[0], TRANSLATIONS["eng"]).get(key, key)

def service_label(bid: str) -> str:
    custom = (service_display_names.get(bid) or "").strip()
    if custom:
        return custom
    return t(bid)

def iter_service_ids():
    return list(service_button_order)

def all_grid_button_ids():
    return list(service_button_order) + ["btn_pause"]

def next_service_button_id() -> str:
    mx = 0
    for bid in service_button_order:
        m = re.match(r"^btn(\d+)$", bid)
        if m:
            mx = max(mx, int(m.group(1)))
    return f"btn{mx + 1}"

def ensure_service_slot(bid: str) -> None:
    if not bid or bid == "btn_pause":
        return
    if bid not in service_config:
        base = SERVICE_NAMES.get(bid, bid)
        ppm = 500
        service_config[bid] = {
            "name": base,
            "price_per_min": ppm,
            "price_per_second": ppm / 60,
        }
    if bid not in service_revenue:
        service_revenue[bid] = 0.0
    if bid not in service_button_visible:
        service_button_visible[bid] = True
    if bid not in TUTORIAL_VIDEO_BY_SERVICE:
        TUTORIAL_VIDEO_BY_SERVICE[bid] = f"/static/tutorials/{bid}.mp4"

def set_lang(lang):
    current_lang[0] = lang
    refresh_all_ui_text()
    save_app_state()

def _set_el_text(el, text):
    if not el:
        return
    if hasattr(el, 'set_text'):
        el.set_text(text)
    elif hasattr(el, 'text'):
        el.text = text

def refresh_all_ui_text():
    for key, el in ui_refs.items():
        _set_el_text(el, t(key))
    for bid, el in revenue_name_refs.items():
        _set_el_text(el, service_label(bid))
    for bid, el in info_name_refs.items():
        _set_el_text(el, service_label(bid))
    for el in price_per_min_refs:
        _set_el_text(el, t('price_per_min'))
    for el in save_btn_refs:
        _set_el_text(el, t('save'))
    for bid, el in grid_label_refs.items():
        _set_el_text(el, service_label(bid))
    for bid, el in display_svc_checkbox_refs.items():
        _set_el_text(el, service_label(bid))
    update_pause_visuals()
    update_price_bar()
    update_ui()

# Refs for labels that need translation refresh
ui_refs = {}
revenue_name_refs = {}  # bid -> label for CASH tab service names
info_name_refs = {}    # bid -> label for INFO tab service names
price_per_min_refs = []  # labels "Price / minute"
save_btn_refs = []       # SAVE buttons in INFO tab
grid_label_refs = {}   # bid -> label for service names in button grid
display_svc_checkbox_refs = {}  # bid -> checkbox on Display settings tab
cash_rows_host_ref = [None]
info_cards_host_ref = [None]
display_checks_host_ref = [None]
services_editor_host_ref = [None]
total_revenue_label_ref = [None]
revenue_value_labels: dict[str, Any] = {}
services_name_inputs: dict[str, Any] = {}
service_editor_live_values: dict[str, str] = {}

# --- СИСТЕМНАЯ ЛОГИКА ---
DEFAULT_SESSION_SECONDS = 30 * 60
remaining_seconds = [0]  # source of truth for time; 0 = no session
active_btn_id = [None]
is_paused = [True]
display_mode = [0]  # 0 = TIME big, 1 = MONEY big
currency_code = ["UZS"]
menu_open = [False]
current_tab = [None]
btns, pause_refs = {}, {}
# Q → menu: admin-adjustable
# Free pause N>0: after user presses Pause, wash is frozen N seconds only, then auto-resumes (same service, timer + money flow).
# N=0: pause until user presses Start.
free_pause_seconds = [0]
bonus_percent = [0.0]
header_show_timer = [True]
header_show_balance = [True]
pause_started_at = [None]
timer_row_ref = [None]
custom_display_meta_ref = [None]
# Smooth countdown: bill every 1s via accumulator; display interpolates within current second
bill_accumulator = [0.0]
billing_phase_start = [None]  # monotonic() at start of current displayed second slice (when running)

def start_session_if_needed():
    if remaining_seconds[0] <= 0:
        remaining_seconds[0] = DEFAULT_SESSION_SECONDS

def switch_service(bid):
    active_btn_id[0] = bid
    refresh_button_visuals()
    notify(f"{t('selected')} {service_label(bid)}")
    update_price_bar()

def _sync_running_phase():
    """Reset fractional billing and display phase when session starts running."""
    billing_phase_start[0] = time.monotonic()
    bill_accumulator[0] = 0.0


def set_running(running: bool):
    is_paused[0] = not running
    if running:
        pause_started_at[0] = None
        _sync_running_phase()
    update_pause_visuals()

# Notifications: list of {"ts": float, "text": str}
notifications = []
notifications_container_ref = [None]

def notify(text):
    notifications.append({"ts": time.time(), "text": str(text)})
    _refresh_notifications_ui()

def _refresh_notifications_ui():
    if not notifications_container_ref[0]:
        return
    container = notifications_container_ref[0]
    container.clear()
    with container:
        for entry in reversed(notifications[-50:]):
            ts = entry["ts"]
            dt = datetime.fromtimestamp(ts)
            tstr = dt.strftime("%H:%M:%S")
            with ui.row().classes("w-full items-center gap-2 py-1 text-sm"):
                ui.label(tstr).classes("text-gray-400 shrink-0")
                ui.label(entry["text"]).classes("text-white truncate")

def clear_notifications():
    notifications.clear()
    _refresh_notifications_ui()

bell_btn_ref = [None]
bell_pressed_timer_ref = [None]
layout_compact_state = [False]
main_stage_ref = [None]
buttons_grid_ref = [None]
right_rail_ref = [None]
bell_fixed_host_ref = [None]
last_tutorial_video_key = [None]
header_idle_video_wrap_ref = [None]
custom_display_root_ref = [None]
_header_idle_video_last_shown = [None]

def set_bell_pressed_state(on: bool):
    btn = bell_btn_ref[0]
    if not btn:
        return
    if on:
        btn.classes(add='bell-pressed', remove='')
    else:
        btn.classes(remove='bell-pressed')

def send_bell_signal():
    print("BELL PRESSED: signal sent")
    set_bell_pressed_state(True)
    if bell_pressed_timer_ref[0]:
        bell_pressed_timer_ref[0].cancel()
    bell_pressed_timer_ref[0] = ui.timer(2.0, lambda: set_bell_pressed_state(False), once=True)

def video_play_pause():
    ui.run_javascript(
        "const v=document.getElementById('tutorialVideo');"
        "if(v){if(v.paused){v.play()}else{v.pause()}}"
    )

def video_restart():
    ui.run_javascript(
        "const v=document.getElementById('tutorialVideo');"
        "if(v){v.currentTime=0;v.play()}"
    )

price_bar_ref = [None]
price_bar_icon_ref = [None]
price_bar_label_ref = [None]

# --- SERVICE CONFIGURATION ---
def init_service_config():
    default_config = {}
    for bid in service_button_order:
        name = SERVICE_NAMES.get(bid, bid)
        price_per_min = 500
        default_config[bid] = {
            "name": name,
            "price_per_min": price_per_min,
            "price_per_second": price_per_min / 60,
        }
    return default_config

service_config = init_service_config()

# --- REVENUE TRACKING ---
service_revenue = {bid: 0.0 for bid in service_button_order}

PATH_PAUSE = "M200 200h200v600h-200zM600 200h200v600h-200z" 
PATH_PLAY = "M300 200l500 300-500 300z" 

def get_current_price_per_second():
    """UZS per second from configured UZS/min (Info); avoids stale price_per_second in dict."""
    bid = active_btn_id[0]
    if not bid or bid not in service_config:
        return 0.0
    ppm = float(service_config[bid]["price_per_min"])
    return (ppm / 60.0) if ppm > 0 else 0.0


def get_display_seconds_float() -> float:
    if (
        not is_paused[0]
        and active_btn_id[0]
        and remaining_seconds[0] > 0
        and billing_phase_start[0] is not None
    ):
        elapsed = time.monotonic() - billing_phase_start[0]
        return max(0.0, float(remaining_seconds[0]) - elapsed)
    return float(max(0, remaining_seconds[0]))


def get_tutorial_video_url(bid: str | None) -> str:
    if not bid or bid == 'btn_pause':
        return VIDEO_SRC
    return TUTORIAL_VIDEO_BY_SERVICE.get(bid, VIDEO_SRC)


def should_use_compact_layout() -> bool:
    """Узкий столбец кнопок справа + видео в центре: есть услуга, время и ненулевой баланс (или тариф 0)."""
    bid = active_btn_id[0]
    if not bid or bid == 'btn_pause':
        return False
    if remaining_seconds[0] <= 0:
        return False
    ppm = float(service_config.get(bid, {}).get('price_per_min', 0) or 0)
    rate = (ppm / 60.0) if ppm > 0 else 0.0
    display_sec_float = get_display_seconds_float()
    money = int(display_sec_float * rate + 1e-6) if rate > 0 else 0
    if rate > 0 and money <= 0:
        return False
    return True


def _sync_tutorial_video() -> None:
    if not layout_compact_state[0]:
        return
    bid = active_btn_id[0]
    url = get_tutorial_video_url(bid)
    key = (bid, url)
    if last_tutorial_video_key[0] == key:
        return
    last_tutorial_video_key[0] = key
    ui.run_javascript(f"""
        (function() {{
            const v = document.getElementById('tutorialVideo');
            if (!v) return;
            const url = {json.dumps(url)};
            v.src = url;
            v.muted = true;
            v.playsInline = true;
            v.load();
            v.play().catch(function() {{}});
        }})();
    """)


def update_compact_layout() -> None:
    want = should_use_compact_layout()
    ms = main_stage_ref[0]
    bg = buttons_grid_ref[0]
    rr = right_rail_ref[0]
    bell_btn_el = bell_btn_ref[0]
    bf = bell_fixed_host_ref[0]
    if not ms or not bg or not rr or not bell_btn_el or not bf:
        return
    state_changed = want != layout_compact_state[0]
    if state_changed:
        layout_compact_state[0] = want
        if want:
            last_tutorial_video_key[0] = None
            ms.classes(remove='layout-idle', add='layout-active')
            for bid in all_grid_button_ids():
                if bid in btns:
                    btns[bid].move(rr, -1)
            bell_btn_el.move(rr, -1)
            bell_btn_el.classes(remove='bell-btn--large', add='bell-btn--small')
        else:
            ms.classes(remove='layout-active', add='layout-idle')
            bell_btn_el.move(bf, -1)
            for bid in all_grid_button_ids():
                if bid in btns:
                    btns[bid].move(bg, -1)
            bell_btn_el.classes(remove='bell-btn--small', add='bell-btn--large')
            last_tutorial_video_key[0] = None
            ui.run_javascript(
                "const v=document.getElementById('tutorialVideo');if(v){v.pause();}"
            )
    if want:
        _sync_tutorial_video()
    sync_header_idle_video()


def sync_header_idle_video(force: bool = False):
    """Промо-ролик в шапке: только пока нет активной мойки (до compact layout)."""
    show = not layout_compact_state[0]
    if not force and _header_idle_video_last_shown[0] == show:
        return
    _header_idle_video_last_shown[0] = show
    w = header_idle_video_wrap_ref[0]
    root = custom_display_root_ref[0]
    if w:
        w.set_visibility(show)
    if root:
        if show:
            root.classes(remove='custom-display--timer-only', add='custom-display--with-idle-video')
        else:
            root.classes(remove='custom-display--with-idle-video', add='custom-display--timer-only')
    if show:
        ui.run_javascript(
            "const v=document.getElementById('headerIdleVideo');"
            "if(v){v.muted=true;v.playsInline=true;v.play().catch(function(){});}"
        )
    else:
        ui.run_javascript(
            "const v=document.getElementById('headerIdleVideo');if(v){v.pause();v.currentTime=0;}"
        )


def bonus_multiplier():
    return 1.0 + max(0.0, float(bonus_percent[0])) / 100.0


def apply_topup(money_uzs: float = 0.0, seconds: int = 0):
    """пополнение: add paid money and/or time; bonus % multiplies both credits (not used on running timer ticks)."""
    if not active_btn_id[0]:
        ui.notify(t('topup_need_service'), color='orange')
        return
    m = bonus_multiplier()
    mu = max(0.0, float(money_uzs))
    sec = max(0, int(seconds))
    if mu <= 0 and sec <= 0:
        return
    bid = active_btn_id[0]
    if mu > 0:
        service_revenue[bid] += mu * m
    if sec > 0:
        add = int(round(sec * m))
        if remaining_seconds[0] <= 0:
            remaining_seconds[0] = add
        else:
            remaining_seconds[0] += add
        if not is_paused[0]:
            _sync_running_phase()
    save_app_state()
    update_ui()
    ui.notify(t('topup_done'), color='green')

def apply_header_display_visibility():
    """Показ строк таймера и баланса в шапке по галочкам (учитывает display_mode swap)."""
    tr = timer_row_ref[0]
    meta = custom_display_meta_ref[0]
    if not tr or "sub_display" not in globals() or sub_display is None:
        return
    st = bool(header_show_timer[0])
    sb = bool(header_show_balance[0])
    if meta:
        meta.set_visibility(st or sb)
    if display_mode[0] == 0:
        tr.set_visibility(st)
        sub_display.set_visibility(sb)
    else:
        tr.set_visibility(sb)
        sub_display.set_visibility(st)


def apply_service_button_visibility():
    for bid, el in btns.items():
        if bid == "btn_pause":
            el.set_visibility(True)
            continue
        el.set_visibility(bool(service_button_visible.get(bid, True)))


def action_dynamic_service(bid: str):
    print(f"{service_label(bid)} ({bid})")


def repopulate_buttons_grid():
    bg = buttons_grid_ref[0]
    if not bg:
        return
    bg.clear()
    btns.clear()
    pause_refs.clear()
    grid_label_refs.clear()
    with bg:
        for bid in all_grid_button_ids():
            btn = ui.element('div').classes('action-btn icon-idle')
            btn.on('click', lambda e, b=bid: handle_click(b))
            with btn:
                if bid == 'btn_pause':
                    pause_refs['svg'] = ui.html('')
                    pause_refs['label'] = ui.label(t('start')).classes('font-bold mt-2 text-center').style('font-size: 1.4vmin')
                else:
                    path = get_svg_path(bid)
                    ui.html(f'<svg width="4.5vmin" height="4.5vmin" viewBox="0 0 1000 1000"><path d="{path}"/></svg>')
                    lbl = ui.label(service_label(bid)).classes('font-bold mt-2 text-center').style('font-size: 1.4vmin')
                    grid_label_refs[bid] = lbl
            btns[bid] = btn
    refresh_button_visuals()
    update_pause_visuals()
    apply_service_button_visibility()


def update_revenue_display():
    tr = total_revenue_label_ref[0]
    if not tr:
        return
    total = 0.0
    for bid in iter_service_ids():
        revenue = float(service_revenue.get(bid, 0.0))
        total += revenue
        lab = revenue_value_labels.get(bid)
        if lab:
            lab.set_text(f"{format_money(revenue)} UZS")
    tr.set_text(f"{format_money(total)} UZS")


def repopulate_cash_tab_rows():
    host = cash_rows_host_ref[0]
    if not host:
        return
    host.clear()
    revenue_name_refs.clear()
    revenue_value_labels.clear()
    with host:
        for bid in iter_service_ids():
            with ui.row().classes('w-full justify-between items-center mb-3 p-2').style('background: #1e293b; border-radius: 8px;'):
                nl = ui.label(service_label(bid)).classes('text-white font-bold')
                revenue_name_refs[bid] = nl
                revenue_value_labels[bid] = ui.label('0 UZS').classes('text-yellow-500 font-bold')


def repopulate_info_price_cards():
    host = info_cards_host_ref[0]
    if not host:
        return
    host.clear()
    info_name_refs.clear()
    price_per_min_refs.clear()
    save_btn_refs.clear()
    price_inputs: dict[str, Any] = {}
    with host:
        for bid in iter_service_ids():
            config = service_config[bid]
            with ui.card().classes('w-full mb-3').style('background: #1e293b;'):
                nl = ui.label(service_label(bid)).classes('text-yellow-500 font-bold mb-2')
                info_name_refs[bid] = nl
                pl = ui.label(t('price_per_min')).classes('text-white text-sm mb-1')
                price_per_min_refs.append(pl)
                price_input = ui.input(
                    label='',
                    value=str(int(config["price_per_min"])),
                    placeholder='UZS/min',
                ).props('outlined dense autocomplete=off').classes('w-full menu-admin-input')
                price_inputs[bid] = price_input

                def make_save_handler(b):
                    def save():
                        try:
                            raw = str(price_inputs[b].value or '').strip().replace(',', '.')
                            price_per_min = int(float(raw or 0))
                            if price_per_min <= 0:
                                ui.notify(t('price_positive'), color='red')
                                return
                            update_service_config(b, price_per_min)
                            save_app_state()
                            ui.notify(f"{service_label(b)} {t('config_saved')}", color='green')
                        except Exception:
                            ui.notify(t('invalid_input'), color='red')
                    return save

                save_el = ui.button(t('save'), on_click=make_save_handler(bid)).classes('w-full mt-2').props('color=primary')
                save_btn_refs.append(save_el)


def repopulate_display_visibility_checks():
    host = display_checks_host_ref[0]
    if not host:
        return
    host.clear()
    display_svc_checkbox_refs.clear()
    with host:
        for bid in iter_service_ids():
            def _make_svc_handler(b):
                def _on_svc(e):
                    service_button_visible[b] = bool(e.value)
                    save_app_state()
                    apply_service_button_visibility()
                return _on_svc

            cb = ui.checkbox(
                service_label(bid),
                value=service_button_visible.get(bid, True),
                on_change=_make_svc_handler(bid),
            ).props('dense').classes('text-white text-xs mb-1')
            display_svc_checkbox_refs[bid] = cb


def repopulate_services_editor():
    host = services_editor_host_ref[0]
    if not host:
        return
    host.clear()
    services_name_inputs.clear()
    service_editor_live_values.clear()
    with host:
        for bid in iter_service_ids():
            with ui.row().classes('w-full items-center gap-2 mb-2 flex-nowrap'):
                ui.label(bid).classes('text-gray-500 text-xs shrink-0').style('min-width: 52px; max-width: 72px')
                cur = (service_display_names.get(bid) or '').strip()

                def _track(b):
                    def _on(e):
                        service_editor_live_values[b] = str(e.value if e.value is not None else '')
                    return _on

                inp = ui.input(
                    label='',
                    value=cur,
                    placeholder=t(bid),
                    on_change=_track(bid),
                ).props('outlined dense').classes('flex-grow menu-admin-input')
                services_name_inputs[bid] = inp
                service_editor_live_values[bid] = cur
                ui.button(icon='delete').props('flat round dense color=red').on(
                    'click', lambda _, b=bid: remove_service(b)
                )


def save_service_names_from_editor():
    for bid, inp in list(services_name_inputs.items()):
        if bid in service_editor_live_values:
            v = str(service_editor_live_values[bid] or '').strip()
        elif inp is not None:
            v = str(inp.value or '').strip()
        else:
            v = ''
        if v:
            service_display_names[bid] = v
        else:
            service_display_names.pop(bid, None)
    save_app_state()
    repopulate_all_dynamic_ui()


def add_service_to_order():
    nid = next_service_button_id()
    service_button_order.append(nid)
    ensure_service_slot(nid)
    service_display_names[nid] = t('new_service_name')
    save_app_state()
    repopulate_all_dynamic_ui()
    ui.notify(t('config_saved'), color='green')


def remove_service(bid: str):
    if len(service_button_order) <= 1:
        ui.notify(t('services_min_one'), color='red')
        return
    if active_btn_id[0] == bid:
        stop_everything()
    service_button_order.remove(bid)
    service_display_names.pop(bid, None)
    service_button_visible.pop(bid, None)
    service_config.pop(bid, None)
    service_revenue.pop(bid, None)
    TUTORIAL_VIDEO_BY_SERVICE.pop(bid, None)
    save_app_state()
    repopulate_all_dynamic_ui()


def repopulate_all_dynamic_ui():
    repopulate_buttons_grid()
    repopulate_cash_tab_rows()
    repopulate_info_price_cards()
    repopulate_display_visibility_checks()
    repopulate_services_editor()
    refresh_all_ui_text()
    update_revenue_display()
    update_ui()


def update_price_bar():
    bar, icon_el, label_el = price_bar_ref[0], price_bar_icon_ref[0], price_bar_label_ref[0]
    if not bar or not label_el:
        return
    bid = active_btn_id[0]
    if not bid or bid not in service_config:
        bar.classes(remove="price-bar-visible", add="price-bar-hidden")
        return
    bar.classes(remove="price-bar-hidden", add="price-bar-visible")
    name = service_label(bid)
    price = service_config[bid]["price_per_min"]
    path = get_svg_path(bid)
    svg = f'<svg width="28" height="28" viewBox="0 0 1000 1000" style="fill:#020617; display:block;"><path d="{path}"/></svg>'
    if icon_el:
        icon_el.content = svg
    label_el.set_text(f"{name} — {price} UZS / MIN")

def update_ui():
    if 'main_display' not in globals(): return
    display_sec_float = get_display_seconds_float()
    sec = max(0, int(display_sec_float))
    minutes = sec // 60
    seconds = sec % 60
    time_str = f"{minutes:02d}:{seconds:02d}"
    # Сумма на экране = «сколько ещё висит» в UZS по текущему тарифу (UZS/min из меню)
    rate = get_current_price_per_second()
    money = int(display_sec_float * rate + 1e-6) if rate > 0 else 0
    formatted_money = f"{money:,}".replace(",", " ")

    if display_mode[0] == 0:
        main_display.set_text(time_str)
        main_unit.set_text(t('time_unit'))
        sub_display.set_text(f"{formatted_money} {currency_code[0]}")
    else:
        main_display.set_text(formatted_money)
        main_unit.set_text(currency_code[0])
        sub_display.set_text(time_str)
    apply_header_display_visibility()
    update_compact_layout()

async def timer_loop():
    dt = 0.05
    while True:
        now = time.monotonic()

        # Автовыход из бесплатной паузы: ровно N секунд «стоп», затем снова мойка (как нажали Старт)
        if is_paused[0] and active_btn_id[0] and pause_started_at[0] is not None:
            n = int(free_pause_seconds[0])
            if n > 0 and (now - pause_started_at[0]) >= float(n):
                is_paused[0] = False
                pause_started_at[0] = None
                _sync_running_phase()
                update_pause_visuals()
                notify(t('auto_resumed'))
                update_ui()

        ticked = False
        if not is_paused[0] and active_btn_id[0] and remaining_seconds[0] > 0:
            if billing_phase_start[0] is None:
                billing_phase_start[0] = now
            bill_accumulator[0] += dt
            while bill_accumulator[0] >= 1.0 and remaining_seconds[0] > 0:
                bill_accumulator[0] -= 1.0
                price_per_sec = get_current_price_per_second()
                remaining_seconds[0] -= 1
                if price_per_sec > 0:
                    service_revenue[active_btn_id[0]] += price_per_sec
                billing_phase_start[0] = time.monotonic()
                ticked = True
                if remaining_seconds[0] <= 0:
                    bill_accumulator[0] = 0.0
                    billing_phase_start[0] = None
                    stop_everything()
                    ticked = False
                    break
            if ticked:
                save_app_state()
        else:
            bill_accumulator[0] = 0.0

        if active_btn_id[0] and (remaining_seconds[0] > 0 or not is_paused[0]):
            update_ui()
        await asyncio.sleep(dt)

def stop_everything():
    is_paused[0] = True
    pause_started_at[0] = None
    billing_phase_start[0] = None
    bill_accumulator[0] = 0.0
    active_btn_id[0] = None
    remaining_seconds[0] = 0
    notify("Session ended — time reached 0")
    refresh_button_visuals()
    update_price_bar()
    update_ui()
    update_pause_visuals()

def handle_click(bid):
    if bid == 'btn_pause':
        toggle_pause()
        return

    action = BUTTON_ACTIONS.get(bid)
    if action:
        action()
    else:
        action_dynamic_service(bid)

    if bid not in service_config:
        return
    start_session_if_needed()
    switch_service(bid)
    if is_paused[0]:
        set_running(True)
    update_ui()

def refresh_button_visuals():
    for bid, el in btns.items():
        if bid == 'btn_pause': continue
        isActive = (bid == active_btn_id[0])
        el.classes(add='active-yellow scale-active' if isActive else '', 
                   remove='active-yellow scale-active' if not isActive else '')
        if isActive:
            el.classes(add='icon-active', remove='icon-idle')
        else:
            el.classes(add='icon-idle', remove='icon-active')

def toggle_pause():
    if not active_btn_id[0]:
        ui.notify(t('choose_mode'), color='orange')
        return
    is_paused[0] = not is_paused[0]
    if is_paused[0]:
        pause_started_at[0] = time.monotonic()
        bill_accumulator[0] = 0.0
    else:
        pause_started_at[0] = None
        _sync_running_phase()
    notify("Started" if not is_paused[0] else "Stopped")
    update_pause_visuals()
    update_ui()

def update_pause_visuals():
    p_btn = btns.get('btn_pause')
    if not p_btn or 'svg' not in pause_refs: return
    
    if is_paused[0]:
        p_btn.classes(remove='pause-active scale-active', add='pause-stopped')
        pause_refs['label'].set_text(t('start'))
        pause_refs['svg'].content = f'<svg width="5.5vmin" height="5.5vmin" viewBox="0 0 1000 1000" style="fill:#2ecc71;"><path d="{PATH_PLAY}"/></svg>'
    else:
        p_btn.classes(remove='pause-stopped', add='pause-active scale-active')
        pause_refs['label'].set_text(t('stop'))
        pause_refs['svg'].content = f'<svg width="5.5vmin" height="5.5vmin" viewBox="0 0 1000 1000" style="fill:#ff4757;"><path d="{PATH_PAUSE}"/></svg>'

def toggle_menu():
    menu_open[0] = not menu_open[0]
    left_panel.classes(add='menu-visible' if menu_open[0] else '', remove='menu-visible' if not menu_open[0] else '')


def _menu_hotkey(e: events.KeyEventArguments) -> None:
    """Q toggles side menu; works when grid buttons (div) are focused. Ignored in text fields."""
    if not e.action.keydown or e.action.repeat:
        return
    if e.modifiers.ctrl or e.modifiers.meta or e.modifiers.alt:
        return
    key = e.key.name if hasattr(e.key, 'name') else e.key
    if str(key).lower() != 'q':
        return
    toggle_menu()

def update_service_config(bid, price_per_min):
    if bid not in service_config:
        return
    service_config[bid]["price_per_min"] = price_per_min
    service_config[bid]["price_per_second"] = price_per_min / 60 if price_per_min > 0 else 0
    notify(f"Price changed: {service_label(bid)} — {price_per_min} UZS/min")
    update_price_bar()
    update_ui()

def format_money(amount):
    return f"{int(amount):,}".replace(",", " ")

LOCAL_STORAGE_KEY = "tesla_wash_state"

def build_app_state():
    return {
        "prices_per_min": {
            bid: config["price_per_min"]
            for bid, config in service_config.items()
        },
        "revenues": {
            bid: revenue for bid, revenue in service_revenue.items()
        },
        "free_pause_seconds": int(free_pause_seconds[0]),
        "bonus_percent": float(bonus_percent[0]),
        "header_show_timer": bool(header_show_timer[0]),
        "header_show_balance": bool(header_show_balance[0]),
        "service_button_order": list(service_button_order),
        "service_display_names": dict(service_display_names),
        "service_button_visible": {
            bid: bool(service_button_visible.get(bid, True)) for bid in service_button_order
        },
        "lang": current_lang[0],
        "display_mode": int(display_mode[0]),
    }

def save_app_state():
    state = build_app_state()
    state_json = json.dumps(state)
    # store JSON string safely in localStorage
    ui.run_javascript(
        f'localStorage.setItem("{LOCAL_STORAGE_KEY}", {json.dumps(state_json)});'
    )

def _apply_loaded_state(state_json: str):
    if not state_json:
        return
    try:
        data = json.loads(state_json)
    except Exception:
        return

    lg = data.get("lang")
    if isinstance(lg, str) and lg in LANGS:
        current_lang[0] = lg
    try:
        dm = int(data.get("display_mode", 0))
        display_mode[0] = 0 if dm == 0 else 1
    except Exception:
        pass

    order = data.get("service_button_order")
    if isinstance(order, list) and order:
        clean = []
        for x in order:
            if isinstance(x, str) and x != "btn_pause" and x.startswith("btn"):
                clean.append(x)
        if clean:
            service_button_order[:] = clean
    names = data.get("service_display_names")
    if isinstance(names, dict):
        service_display_names.clear()
        for k, v in names.items():
            if isinstance(k, str) and isinstance(v, str) and v.strip():
                service_display_names[k] = v.strip()
    for bid in service_button_order:
        ensure_service_slot(bid)

    prices = data.get("prices_per_min", {})
    for bid, val in prices.items():
        ensure_service_slot(bid)
        if bid in service_config:
            try:
                ppm = float(val)
            except Exception:
                continue
            service_config[bid]["price_per_min"] = ppm
            service_config[bid]["price_per_second"] = ppm / 60 if ppm > 0 else 0

    revenues = data.get("revenues", {})
    for bid, val in revenues.items():
        ensure_service_slot(bid)
        if bid in service_revenue:
            try:
                service_revenue[bid] = float(val)
            except Exception:
                continue

    try:
        free_pause_seconds[0] = max(0, int(data.get("free_pause_seconds", 0)))
    except Exception:
        pass
    try:
        bonus_percent[0] = max(0.0, float(data.get("bonus_percent", 0)))
    except Exception:
        pass
    header_show_timer[0] = bool(data.get("header_show_timer", True))
    header_show_balance[0] = bool(data.get("header_show_balance", True))
    vis = data.get("service_button_visible")
    if isinstance(vis, dict):
        for bid in service_button_order:
            if bid in vis:
                try:
                    service_button_visible[bid] = bool(vis[bid])
                except Exception:
                    pass

async def load_app_state():
    try:
        raw = await ui.run_javascript(
            f'return localStorage.getItem({json.dumps(LOCAL_STORAGE_KEY)});',
            timeout=5.0,
        )
    except Exception:
        return
    if raw is None:
        return
    s = str(raw).strip()
    if not s or s in ('undefined', 'null'):
        return
    _apply_loaded_state(s)

tab_contents = {}

def show_tab(tab_name):
    current_tab[0] = tab_name
    for tab_id, content in tab_contents.items():
        content.set_visibility(tab_id == tab_name)

@ui.page('/')
async def main_page():
    global main_display, main_unit, sub_display, left_panel, tab_contents
    btns.clear()
    pause_refs.clear()
    tab_contents.clear()
    revenue_name_refs.clear()
    info_name_refs.clear()
    price_per_min_refs.clear()
    save_btn_refs.clear()
    grid_label_refs.clear()
    display_svc_checkbox_refs.clear()
    services_name_inputs.clear()
    service_editor_live_values.clear()
    revenue_value_labels.clear()
    ui_refs.clear()
    await load_app_state()

    ui.timer(0, timer_loop, once=True)

    ui.add_head_html("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&display=swap');
    :root { --primary: #ffcc00; --bg: #020617; --btn-size: clamp(60px, 12vmin, 130px); }
    body { background: var(--bg); margin: 0; font-family: 'Orbitron', sans-serif; overflow: hidden; color: white; }
    .action-btn svg { fill: #64748b; }
    .icon-active svg { fill: var(--primary) !important; }
    .scale-active { transform: scale(1.1); z-index: 10; }
    .side-menu { position: fixed; top: 0; left: -280px; width: 280px; height: 100vh; background: #080c14; border-right: 2px solid var(--primary); z-index: 2000; display: flex; flex-direction: column; padding: 40px 20px; }
    .menu-visible { left: 0 !important; }
    .drawer-handle { display: none !important; }
    .bell-host--fixed { position: fixed; top: 50%; right: 20px; transform: translateY(-50%); z-index: 90; display: flex; align-items: center; justify-content: center; }
    .bell-btn { border: 1px solid rgba(248, 250, 252, 0.3); color: #facc15; border-radius: 18%; }
    .bell-btn--large {
      padding: 0;
      box-sizing: border-box;
      width: 60px !important;
      height: 60px !important;
      min-width: 60px !important;
      min-height: 60px !important;
      max-width: 60px !important;
      max-height: 60px !important;
      font-size: clamp(22px, 5vmin, 36px);
    }
    .bell-btn--small { padding: 0 !important; min-width: var(--btn-size) !important; min-height: var(--btn-size) !important; width: var(--btn-size) !important; height: var(--btn-size) !important; font-size: clamp(14px, 3vmin, 22px) !important; }
    .bell-btn .q-icon { width: 34px !important; height: 27px !important; font-size: 27px !important; }
    .bell-pressed { background: #22c55e; color: #020617 !important; box-shadow: 0 0 12px rgba(34,197,94,0.7); }
    /* Под полосой таймера (.custom-display), не перекрывает её */
    .price-bar {
      position: fixed;
      top: calc(env(safe-area-inset-top, 0px) + clamp(92px, 13vh, 120px));
      left: 50%;
      transform: translateX(-50%);
      z-index: 3000;
      background: var(--primary);
      color: var(--bg);
      padding: clamp(6px, 1.2vw, 12px) clamp(12px, 3vw, 24px);
      font-size: clamp(1.2vmin, 2vw, 2vmin);
      font-weight: 900;
      border-radius: 0 0 10px 10px;
      display: flex;
      align-items: center;
      gap: 8px;
      max-width: min(95vw, 420px);
      flex-wrap: wrap;
      justify-content: center;
    }
    .price-bar-icon-wrap { width: clamp(20px, 4vw, 28px); height: clamp(20px, 4vw, 28px); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
    .price-bar-label { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100%; }
    .price-bar-hidden { visibility: hidden; opacity: 0; pointer-events: none; }
    .price-bar-visible { visibility: visible; opacity: 1; }
    .custom-display {
      position: fixed; top: 0; left: 0; right: 0; width: 100%; max-width: 100%; margin-top: 0; box-sizing: border-box;
      z-index: 100; background: #0f172a; border: 1.5px solid var(--primary); border-top: none;
      border-radius: 0;
      padding: 0 max(12px, env(safe-area-inset-right, 0px)) clamp(10px, 1.5vw, 14px) max(12px, env(safe-area-inset-left, 0px));
      padding-top: max(0px, env(safe-area-inset-top, 0px));
      display: flex; flex-direction: column; align-items: stretch; gap: 0;
    }
    /* Промо в шапке на всю ширину: без скруглений, таймер скрыт */
    .custom-display.custom-display--with-idle-video .custom-display-meta {
      display: none !important;
    }
    .custom-display--with-idle-video .custom-display-top { gap: 0; }
    /* Только таймер: полоса на всю ширину, без скруглений; время и баланс по центру */
    .custom-display.custom-display--timer-only {
      left: 0 !important;
      right: 0 !important;
      width: 100% !important;
      max-width: 100% !important;
      border-radius: 0;
      padding: max(0px, env(safe-area-inset-top, 0px)) max(12px, env(safe-area-inset-right, 0px)) clamp(10px, 1.5vw, 14px) max(12px, env(safe-area-inset-left, 0px));
      align-items: stretch;
    }
    .custom-display--timer-only .custom-display-top {
      width: 100% !important;
      justify-content: center !important;
    }
    .custom-display--timer-only .custom-display-meta {
      align-items: center !important;
      text-align: center !important;
    }
    .custom-display--timer-only .items-baseline { justify-content: center !important; }
    .custom-display--timer-only .sub-info { align-self: center !important; }
    .custom-display--timer-only .header-idle-video-wrap {
      display: none !important;
      flex: 0 0 0 !important;
      width: 0 !important;
      min-width: 0 !important;
      height: 0 !important;
      margin: 0 !important;
      padding: 0 !important;
      overflow: hidden !important;
      border: none !important;
    }
    .custom-display--timer-only .custom-display-meta { display: flex !important; }
    .custom-display-top {
      width: 100%;
      align-items: flex-start !important;
      flex-wrap: nowrap !important;
      gap: 12px;
    }
    /* Видео растягивается от левого края до таймера */
    .header-idle-video-wrap {
      flex: 1 1 0;
      min-width: 0;
      width: auto;
      overflow: hidden;
      border-radius: 0;
      background: #000;
      align-self: flex-start;
    }
    .header-idle-video-el {
      width: 100%;
      height: 104px;
      max-height: 104px;
      display: block;
      object-fit: cover;
      vertical-align: top;
    }
    .custom-display-meta {
      display: flex; flex-direction: column; align-items: flex-end; text-align: right;
      flex: 0 0 auto;
      min-width: 0;
      padding: 4px 0 4px 4px;
      box-sizing: border-box;
    }
    .custom-display .items-baseline { justify-content: flex-end; width: 100%; flex-wrap: wrap; }
    .custom-display .sub-info { align-self: flex-end; margin-top: 2px; }
    .main-val { color: #00f2ff; font-size: clamp(4vmin, 6.2vmin, 8vmin); font-weight: 900; line-height: 1.1; letter-spacing: 0.02em; white-space: nowrap; }
    .main-unit { font-size: clamp(1.5vmin, 2vw, 2vmin); color: var(--primary); margin-left: 6px; }
    .sub-info { color: #94a3b8; font-size: clamp(1.6vmin, 2.2vmin, 2.5vmin); margin-top: 4px; }
    .main-stage { position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; flex-direction: row; align-items: stretch; justify-content: center; padding: 80px 0 80px; box-sizing: border-box; min-height: 0; }
    .main-stage.layout-idle { padding-top: clamp(130px, 20vh, 200px); }
    /* stretch — и центр, и правая колонка на всю высоту экрана (минус padding main-stage) */
    .main-stage.layout-active { justify-content: flex-start; align-items: stretch; padding: clamp(100px, 14vh, 152px) 4px 12px 10px; min-height: 0; }
    /* column: иначе при layout-active один ребёнок (видео) в row не растягивается — «квадратик» слева */
    .center-pane { flex: 1 1 0; display: flex; flex-direction: column; align-items: stretch; justify-content: center; min-width: 0; min-height: 0; position: relative; }
    .main-stage.layout-active .center-pane { align-self: stretch; }
    .tutorial-video-wrap { display: none; width: 100%; flex: 0 0 auto; align-items: center; justify-content: center; padding: 8px 16px; box-sizing: border-box; }
    .layout-active .tutorial-video-wrap { display: flex; flex: 1 1 0; min-width: 0; min-height: 0; }
    .tutorial-video-el { width: 601px; height: 500px; border-radius: 14px; border: 1px solid rgba(255,255,255,0.22); background: #000; object-fit: contain; }
    .idle-buttons-cluster { width: 100%; flex: 0 0 auto; }
    .layout-idle .idle-buttons-cluster { display: flex; align-items: center; justify-content: center; }
    .layout-active .idle-buttons-cluster { display: none !important; }
    .right-rail {
      display: none;
      flex: 0 0 auto;
      flex-shrink: 0;
      box-sizing: border-box;
      z-index: 90;
      align-self: stretch;
      min-height: 0;
      --btn-size: clamp(50px, 9.5vmin, 112px);
      grid-template-columns: repeat(2, var(--btn-size));
      grid-auto-rows: min-content;
      gap: clamp(0.9vmin, 1.6vmin, 2vmin);
      column-gap: clamp(1vmin, 1.8vmin, 2.2vmin);
      align-content: start;
      justify-items: center;
      /* сверху: таймер + жёлтая плашка режима (price-bar ниже таймера) */
      padding: clamp(160px, 22vh, 220px) 6px 12px 8px;
      padding-right: max(4px, env(safe-area-inset-right, 0px));
      margin-right: 0;
      overflow-x: hidden;
      overflow-y: auto;
      -webkit-overflow-scrolling: touch;
    }
    .layout-active .right-rail { display: grid; }
    .layout-active .right-rail .bell-rail-cell { justify-self: center; margin-top: 0; }
    .screen-center { width: 100%; display: flex; justify-content: center; align-items: center; }
    .buttons-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(var(--btn-size), 1fr)); gap: clamp(1.5vmin, 2.5vmin, 3vmin); max-width: min(95vw, calc(5 * var(--btn-size) + 4 * 2.5vmin)); } 
    .action-btn { width: var(--btn-size); height: var(--btn-size); border-radius: 18%; background: #1e293b; border: 1px solid rgba(255, 255, 255, 0.1); color: #64748b; display: flex; flex-direction: column; align-items: center; justify-content: center; cursor: pointer; }
    .active-yellow { border: 2.5px solid var(--primary) !important; color: white !important; }
    .pause-stopped { border: 2.5px solid #2ecc71 !important; color: #2ecc71 !important; }
    .pause-active { border: 2.5px solid #ff4757 !important; color: #ff4757 !important; }
    .tab-content { padding: 10px 0; }
    .tab-content::-webkit-scrollbar { width: 6px; }
    .tab-content::-webkit-scrollbar-track { background: #0f172a; }
    .tab-content::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 3px; }
    /* Side menu: Quasar inputs default to dark-on-dark — force readable text */
    .side-menu .menu-admin-input .q-field__native,
    .side-menu .menu-admin-input .q-field__input,
    .side-menu .menu-admin-input input {
      color: #f8fafc !important;
      -webkit-text-fill-color: #f8fafc !important;
      caret-color: #ffcc00;
      opacity: 1 !important;
      font-size: 15px !important;
    }
    .side-menu .menu-admin-input .q-field__control {
      background: rgba(30, 41, 59, 0.95) !important;
    }
    .side-menu .menu-admin-input .q-field__label {
      color: #cbd5e1 !important;
    }
    .side-menu .menu-admin-input .q-field__marginal,
    .side-menu .menu-admin-input .q-field__append {
      color: #f8fafc !important;
    }
    * { transition: none !important; }
    *:hover { transition: none !important; }
    </style>
    """)

    # --- МЕНЮ ---
    tab_contents = {}
    with ui.element('div').classes('side-menu') as left_panel:
        ui.label('TESLA WASH').classes('text-yellow-500 font-bold mb-8').style('font-size: 16px; letter-spacing: 4px')
        
        # Tab buttons
        with ui.column().classes('w-full'):
            lang_btn = ui.button().props('flat no-caps').classes('w-full mb-2 justify-start').on('click', lambda: show_tab('lang'))
            with lang_btn:
                with ui.row().classes('items-center w-full'):
                    ui.icon('language', color='yellow-500', size='24px').classes('mr-4')
                    lbl = ui.label(t('menu_lang')).classes('text-white text-sm font-bold')
                    ui_refs['menu_lang'] = lbl
            
            qr_btn = ui.button().props('flat no-caps').classes('w-full mb-2 justify-start')
            with qr_btn:
                with ui.row().classes('items-center w-full'):
                    ui.icon('qr_code_2', color='yellow-500', size='24px').classes('mr-4')
                    lbl = ui.label(t('menu_qr')).classes('text-white text-sm font-bold')
                    ui_refs['menu_qr'] = lbl
            
            cash_btn = ui.button().props('flat no-caps').classes('w-full mb-2 justify-start').on('click', lambda: show_tab('cash'))
            with cash_btn:
                with ui.row().classes('items-center w-full'):
                    ui.icon('payments', color='yellow-500', size='24px').classes('mr-4')
                    lbl = ui.label(t('menu_cash')).classes('text-white text-sm font-bold')
                    ui_refs['menu_cash'] = lbl
            
            info_btn = ui.button().props('flat no-caps').classes('w-full mb-2 justify-start').on('click', lambda: show_tab('info'))
            with info_btn:
                with ui.row().classes('items-center w-full'):
                    ui.icon('info', color='yellow-500', size='24px').classes('mr-4')
                    lbl = ui.label(t('menu_info')).classes('text-white text-sm font-bold')
                    ui_refs['menu_info'] = lbl

            services_menu_btn = ui.button().props('flat no-caps').classes('w-full mb-2 justify-start').on('click', lambda: show_tab('services'))
            with services_menu_btn:
                with ui.row().classes('items-center w-full'):
                    ui.icon('tune', color='yellow-500', size='24px').classes('mr-4')
                    lbl = ui.label(t('menu_services')).classes('text-white text-sm font-bold')
                    ui_refs['menu_services'] = lbl

            bonus_menu_btn = ui.button().props('flat no-caps').classes('w-full mb-2 justify-start').on('click', lambda: show_tab('bonus'))
            with bonus_menu_btn:
                with ui.row().classes('items-center w-full'):
                    ui.icon('card_giftcard', color='yellow-500', size='24px').classes('mr-4')
                    lbl = ui.label(t('menu_bonus')).classes('text-white text-sm font-bold')
                    ui_refs['menu_bonus'] = lbl

            free_pause_menu_btn = ui.button().props('flat no-caps').classes('w-full mb-2 justify-start').on('click', lambda: show_tab('free_pause'))
            with free_pause_menu_btn:
                with ui.row().classes('items-center w-full'):
                    ui.icon('timer', color='yellow-500', size='24px').classes('mr-4')
                    lbl = ui.label(t('menu_free_pause')).classes('text-white text-sm font-bold')
                    ui_refs['menu_free_pause'] = lbl

            display_menu_btn = ui.button().props('flat no-caps').classes('w-full mb-2 justify-start').on('click', lambda: show_tab('display'))
            with display_menu_btn:
                with ui.row().classes('items-center w-full'):
                    ui.icon('visibility', color='yellow-500', size='24px').classes('mr-4')
                    lbl = ui.label(t('menu_display')).classes('text-white text-sm font-bold')
                    ui_refs['menu_display'] = lbl
        
        # Tab content containers
        with ui.column().classes('w-full mt-4').style('max-height: calc(100vh - 200px); overflow-y: auto;') as tab_container:
            # CASH Tab
            with ui.column().classes('w-full') as cash_tab:
                cash_tab.set_visibility(False)
                tab_contents['cash'] = cash_tab
                lbl = ui.label(t('tab_revenue')).classes('text-yellow-500 font-bold mb-4 text-center').style('font-size: 14px')
                ui_refs['tab_revenue'] = lbl
                cash_rows_host_ref[0] = ui.column().classes('w-full')
                ui.separator().classes('my-4')
                with ui.row().classes('w-full justify-between items-center p-3').style('background: #0f172a; border: 2px solid var(--primary); border-radius: 8px;'):
                    tl = ui.label(t('total')).classes('text-white font-bold text-lg')
                    ui_refs['total'] = tl
                    trl = ui.label('0 UZS').classes('text-yellow-500 font-bold text-lg')
                    total_revenue_label_ref[0] = trl
                ui.timer(1.0, update_revenue_display)
            
            # Language Tab
            with ui.column().classes('w-full') as lang_tab:
                lang_tab.set_visibility(False)
                tab_contents['lang'] = lang_tab
                lbl = ui.label(t('tab_lang_title')).classes('text-yellow-500 font-bold mb-4 text-center').style('font-size: 14px')
                ui_refs['tab_lang_title'] = lbl
                with ui.column().classes('w-full gap-3'):
                    for lang_code in LANGS:
                        key = f'lang_{lang_code}'
                        ui.button(t(key)).classes('w-full').props('color=primary').on('click', lambda _, lc=lang_code: set_lang(lc))
            
            # INFO Tab
            with ui.column().classes('w-full') as info_tab:
                info_tab.set_visibility(False)
                tab_contents['info'] = info_tab
                lbl = ui.label(t('tab_price')).classes('text-yellow-500 font-bold mb-4 text-center').style('font-size: 14px')
                ui_refs['tab_price'] = lbl
                info_cards_host_ref[0] = ui.column().classes('w-full')

            # Bonus tab (admin — Q menu)
            with ui.column().classes('w-full') as bonus_tab:
                bonus_tab.set_visibility(False)
                tab_contents['bonus'] = bonus_tab
                stb = ui.label(t('tab_bonus')).classes('text-yellow-500 font-bold mb-2 text-center').style('font-size: 14px')
                ui_refs['tab_bonus'] = stb
                bh = ui.label(t('bonus_hint')).classes('text-gray-400 text-xs mb-2')
                ui_refs['bonus_hint'] = bh
                bp_input = ui.input(
                    label=t('bonus_label'),
                    value=str(bonus_percent[0]),
                    placeholder='0',
                ).props('outlined dense autocomplete=off').classes('w-full menu-admin-input')

                def save_bonus():
                    try:
                        raw = str(bp_input.value or '').strip().replace(',', '.')
                        bonus_percent[0] = max(0.0, float(raw or 0))
                        save_app_state()
                        ui.notify(t('bonus_saved'), color='green')
                        update_ui()
                    except Exception:
                        ui.notify(t('invalid_input'), color='red')

                ui.button(t('save'), on_click=save_bonus).classes('w-full mt-3').props('color=primary')

            # Free pause tab (admin — Q menu)
            with ui.column().classes('w-full') as free_pause_tab:
                free_pause_tab.set_visibility(False)
                tab_contents['free_pause'] = free_pause_tab
                stp = ui.label(t('tab_free_pause')).classes('text-yellow-500 font-bold mb-2 text-center').style('font-size: 14px')
                ui_refs['tab_free_pause'] = stp
                ph = ui.label(t('free_pause_hint')).classes('text-gray-400 text-xs mb-2')
                ui_refs['free_pause_hint'] = ph
                fp_input = ui.input(
                    label=t('free_pause_label'),
                    value=str(int(free_pause_seconds[0])),
                    placeholder='0',
                ).props('outlined dense autocomplete=off').classes('w-full menu-admin-input')

                def save_free_pause():
                    try:
                        raw = str(fp_input.value or '').strip().replace(',', '.')
                        free_pause_seconds[0] = max(0, int(float(raw or 0)))
                        save_app_state()
                        ui.notify(t('pause_saved'), color='green')
                    except Exception:
                        ui.notify(t('invalid_input'), color='red')

                ui.button(t('save'), on_click=save_free_pause).classes('w-full mt-3').props('color=primary')

            # Display: видимость таймера, баланса и кнопок услуг
            with ui.column().classes('w-full') as display_tab:
                display_tab.set_visibility(False)
                tab_contents['display'] = display_tab
                ui_refs['tab_display'] = ui.label(t('tab_display')).classes('text-yellow-500 font-bold mb-2 text-center').style('font-size: 14px')
                ui_refs['disp_hint'] = ui.label(t('disp_hint')).classes('text-gray-400 text-xs mb-3')

                def _on_timer_vis(e):
                    header_show_timer[0] = bool(e.value)
                    save_app_state()
                    apply_header_display_visibility()

                def _on_balance_vis(e):
                    header_show_balance[0] = bool(e.value)
                    save_app_state()
                    apply_header_display_visibility()

                ui_refs['disp_show_timer'] = ui.checkbox(
                    t('disp_show_timer'),
                    value=header_show_timer[0],
                    on_change=_on_timer_vis,
                ).classes('text-white text-sm mb-1')
                ui_refs['disp_show_balance'] = ui.checkbox(
                    t('disp_show_balance'),
                    value=header_show_balance[0],
                    on_change=_on_balance_vis,
                ).classes('text-white text-sm mb-4')

                ui_refs['disp_services'] = ui.label(t('disp_services')).classes('text-yellow-500 font-bold mb-2 text-sm')
                display_checks_host_ref[0] = ui.column().classes('w-full')

            # Услуги: названия, добавление
            with ui.column().classes('w-full') as services_tab:
                services_tab.set_visibility(False)
                tab_contents['services'] = services_tab
                ui_refs['tab_services'] = ui.label(t('tab_services')).classes('text-yellow-500 font-bold mb-2 text-center').style('font-size: 14px')
                ui_refs['services_hint'] = ui.label(t('services_hint')).classes('text-gray-400 text-xs mb-2')
                ui_refs['services_order_note'] = ui.label(t('services_order_note')).classes('text-gray-500 text-xs mb-2')
                services_editor_host_ref[0] = ui.column().classes('w-full')
                with ui.row().classes('w-full gap-2 mt-2'):
                    ui.button(t('services_save_names'), on_click=save_service_names_from_editor).classes('flex-grow').props('color=primary')
                    ui.button(t('service_add'), on_click=add_service_to_order).classes('flex-grow').props('outline')

    # Global Q — must go through NiceGUI so menu state and DOM stay in sync (raw JS toggle was unreliable).
    ui.keyboard(on_key=_menu_hotkey, ignore=['input', 'textarea', 'select'])

    layout_compact_state[0] = False
    last_tutorial_video_key[0] = None

    # --- Bell: в обычном режиме — справа по вертикали по центру; в режиме мойки — в одной строке с Старт/Стоп, размер как у кнопок
    bell_fixed_host_ref[0] = ui.element('div').classes('bell-host bell-host--fixed')
    with bell_fixed_host_ref[0]:
        bell_btn_ref[0] = ui.button(icon='notifications_active').props('flat round').classes(
            'bell-btn bell-btn--large bell-rail-cell'
        ).on('click', send_bell_signal)

    # --- Price bar (always visible when service selected) ---
    with ui.row().classes('price-bar price-bar-hidden').style('align-items: center;') as price_bar:
        price_bar_ref[0] = price_bar
        with ui.element('div').classes('price-bar-icon-wrap'):
            price_bar_icon_ref[0] = ui.html('')
        price_bar_label_ref[0] = ui.label('').classes('font-bold price-bar-label')

    # --- Timer display ---
    def swap_display():
        display_mode[0] = 1 if display_mode[0] == 0 else 0
        save_app_state()
        update_ui()

    _cd_root = ui.element('div').classes('custom-display custom-display--with-idle-video')
    custom_display_root_ref[0] = _cd_root
    with _cd_root:
        with ui.row().classes('custom-display-top w-full items-start'):
            header_idle_video_wrap_ref[0] = ui.element('div').classes('header-idle-video-wrap')
            with header_idle_video_wrap_ref[0]:
                ui.html(
                    f'<video id="headerIdleVideo" class="header-idle-video-el" muted playsinline loop '
                    f'preload="metadata" src={json.dumps(VIDEO_SRC)}></video>',
                    sanitize=False,
                )
            meta_el = ui.element('div').classes('custom-display-meta cursor-pointer').on('click', swap_display)
            custom_display_meta_ref[0] = meta_el
            with meta_el:
                tr_el = ui.row().classes('items-baseline')
                timer_row_ref[0] = tr_el
                with tr_el:
                    main_display = ui.label('').classes('main-val')
                    main_unit = ui.label('').classes('main-unit ml-2')
                sub_display = ui.label('').classes('sub-info')

    # --- Центр: сетка кнопок (простой) ИЛИ видео-туториал; справа — одна колонка кнопок в режиме активной мойки
    with ui.element('div').classes('main-stage layout-idle') as main_stage:
        main_stage_ref[0] = main_stage
        with ui.element('div').classes('center-pane'):
            with ui.element('div').classes('tutorial-video-wrap'):
                ui.html(
                    f'<video id="tutorialVideo" class="tutorial-video-el" muted playsinline loop '
                    f'preload="metadata" src={json.dumps(VIDEO_SRC)}></video>',
                    sanitize=False,
                )
            with ui.element('div').classes('idle-buttons-cluster'):
                with ui.element('div').classes('screen-center'):
                    with ui.element('div').classes('buttons-grid') as buttons_grid:
                        buttons_grid_ref[0] = buttons_grid
        right_rail_ref[0] = ui.element('div').classes('right-rail')

    repopulate_buttons_grid()
    repopulate_cash_tab_rows()
    repopulate_info_price_cards()
    repopulate_display_visibility_checks()
    repopulate_services_editor()
    refresh_all_ui_text()
    update_revenue_display()
    sync_header_idle_video(force=True)

ui.run(
    fullscreen=True,   # полноэкранный режим
    native=True,       # отдельное окно (не браузер)
    show=True,
    title="Tesla Pro",
    reload=False
)