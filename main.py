import gc
import asyncio
import json
import time
from datetime import datetime
from nicegui import events, ui

try:
    from icons import SVG_PATHS
except Exception:
    SVG_PATHS = {f"btn{i}": "M500 100l100 800h-200z" for i in range(1, 16)}

# Configurable video source (static file or URL)
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
SERVICE_NAMES = {
    "btn1": "FOAM", "btn2": "WAX", "btn3": "WATER", "btn4": "AIR", "btn5": "OSMOS",
    "btn6": "TURBO", "btn7": "SHAMPOO", "btn8": "POLISH", "btn9": "STEAM", "btn10": "VACUUM",
    "btn11": "WHEELS", "btn12": "DRY", "btn13": "SMELL", "btn14": "WASH"
}

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
    },
}

def t(key):
    return TRANSLATIONS.get(current_lang[0], TRANSLATIONS["eng"]).get(key, key)

def set_lang(lang):
    current_lang[0] = lang
    refresh_all_ui_text()

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
        _set_el_text(el, t(bid))
    for bid, el in info_name_refs.items():
        _set_el_text(el, t(bid))
    for el in price_per_min_refs:
        _set_el_text(el, t('price_per_min'))
    for el in save_btn_refs:
        _set_el_text(el, t('save'))
    for bid, el in grid_label_refs.items():
        _set_el_text(el, t(bid))
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
pause_started_at = [None]
# Smooth countdown: bill every 1s via accumulator; display interpolates within current second
bill_accumulator = [0.0]
billing_phase_start = [None]  # monotonic() at start of current displayed second slice (when running)

def start_session_if_needed():
    if remaining_seconds[0] <= 0:
        remaining_seconds[0] = DEFAULT_SESSION_SECONDS

def switch_service(bid):
    active_btn_id[0] = bid
    refresh_button_visuals()
    notify(f"{t('selected')} {t(bid)}")
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
        "const v=document.getElementById('promoVideo');"
        "if(v){if(v.paused){v.play()}else{v.pause()}}"
    )

def video_restart():
    ui.run_javascript(
        "const v=document.getElementById('promoVideo');"
        "if(v){v.currentTime=0;v.play()}"
    )

price_bar_ref = [None]
price_bar_icon_ref = [None]
price_bar_label_ref = [None]

# --- SERVICE CONFIGURATION ---
def init_service_config():
    default_config = {}
    for bid, name in SERVICE_NAMES.items():
        price_per_min = 500
        default_config[bid] = {
            "name": name,
            "price_per_min": price_per_min,
            "price_per_second": price_per_min / 60,
        }
    return default_config

service_config = init_service_config()

# --- REVENUE TRACKING ---
service_revenue = {bid: 0.0 for bid in SERVICE_NAMES.keys()}

PATH_PAUSE = "M200 200h200v600h-200zM600 200h200v600h-200z" 
PATH_PLAY = "M300 200l500 300-500 300z" 

def get_current_price_per_second():
    """UZS per second from configured UZS/min (Info); avoids stale price_per_second in dict."""
    bid = active_btn_id[0]
    if not bid or bid not in service_config:
        return 0.0
    ppm = float(service_config[bid]["price_per_min"])
    return (ppm / 60.0) if ppm > 0 else 0.0


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

def update_price_bar():
    bar, icon_el, label_el = price_bar_ref[0], price_bar_icon_ref[0], price_bar_label_ref[0]
    if not bar or not label_el:
        return
    bid = active_btn_id[0]
    if not bid or bid not in service_config:
        bar.classes(remove="price-bar-visible", add="price-bar-hidden")
        return
    bar.classes(remove="price-bar-hidden", add="price-bar-visible")
    name = t(bid)
    price = service_config[bid]["price_per_min"]
    path = get_svg_path(bid)
    svg = f'<svg width="28" height="28" viewBox="0 0 1000 1000" style="fill:#020617; display:block;"><path d="{path}"/></svg>'
    if icon_el:
        icon_el.content = svg
    label_el.set_text(f"{name} — {price} UZS / MIN")

def update_ui():
    if 'main_display' not in globals(): return
    if (
        not is_paused[0]
        and active_btn_id[0]
        and remaining_seconds[0] > 0
        and billing_phase_start[0] is not None
    ):
        elapsed = time.monotonic() - billing_phase_start[0]
        display_sec_float = max(0.0, float(remaining_seconds[0]) - elapsed)
    else:
        display_sec_float = float(max(0, remaining_seconds[0]))
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
    notify(f"Price changed: {SERVICE_NAMES.get(bid, '')} — {price_per_min} UZS/min")
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

    prices = data.get("prices_per_min", {})
    for bid, val in prices.items():
        if bid in service_config:
            try:
                ppm = float(val)
            except Exception:
                continue
            service_config[bid]["price_per_min"] = ppm
            service_config[bid]["price_per_second"] = ppm / 60 if ppm > 0 else 0

    revenues = data.get("revenues", {})
    for bid, val in revenues.items():
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

def load_app_state():
    # NiceGUI version in this project does not support result callbacks from run_javascript,
    # so we safely skip loading here to avoid runtime errors.
    # App will start with default prices and revenues.
    pass

tab_contents = {}

def show_tab(tab_name):
    current_tab[0] = tab_name
    for tab_id, content in tab_contents.items():
        content.set_visibility(tab_id == tab_name)

@ui.page('/')
def main_page():
    global main_display, main_unit, sub_display, left_panel, tab_contents
    btns.clear()
    pause_refs.clear()
    tab_contents.clear()
    revenue_name_refs.clear()
    info_name_refs.clear()
    price_per_min_refs.clear()
    save_btn_refs.clear()
    grid_label_refs.clear()
    ui_refs.clear()
    load_app_state()

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
    .bell-btn { border: 1px solid rgba(248, 250, 252, 0.3); color: #facc15; padding: clamp(10px, 2.5vw, 18px); font-size: clamp(22px, 5vmin, 36px); min-width: clamp(44px, 10vmin, 56px); min-height: clamp(44px, 10vmin, 56px); }
    .bell-pressed { background: #22c55e; color: #020617 !important; box-shadow: 0 0 12px rgba(34,197,94,0.7); }
    .price-bar { position: fixed; top: 0; left: 50%; transform: translateX(-50%); z-index: 3000; background: var(--primary); color: var(--bg); padding: clamp(6px, 1.2vw, 12px) clamp(12px, 3vw, 24px); font-size: clamp(1.2vmin, 2vw, 2vmin); font-weight: 900; border-radius: 0 0 10px 10px; display: flex; align-items: center; gap: 8px; max-width: min(95vw, 420px); flex-wrap: wrap; justify-content: center; }
    .price-bar-icon-wrap { width: clamp(20px, 4vw, 28px); height: clamp(20px, 4vw, 28px); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
    .price-bar-label { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100%; }
    .price-bar-hidden { visibility: hidden; opacity: 0; pointer-events: none; }
    .price-bar-visible { visibility: visible; opacity: 1; }
    .custom-display { position: fixed; top: 20px; right: 0; z-index: 100; background: #0f172a; border: 1.5px solid var(--primary); border-radius: 25px 0 0 25px; padding: clamp(12px, 2vw, 18px) clamp(24px, 4vw, 40px); display: flex; flex-direction: column; align-items: flex-end; }
    .main-val { color: #00f2ff; font-size: clamp(4vmin, 6.2vmin, 8vmin); font-weight: 900; line-height: 1.1; letter-spacing: 0.02em; white-space: nowrap; }
    .main-unit { font-size: clamp(1.5vmin, 2vw, 2vmin); color: var(--primary); margin-left: 6px; }
    .sub-info { color: #94a3b8; font-size: clamp(1.6vmin, 2.2vmin, 2.5vmin); margin-top: 4px; }
    .grid-wrapper { position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center; padding: 80px 0 80px; }
    .screen-center { width: 100%; display: flex; justify-content: center; align-items: center; }
    .video-bottom-wrap { position: fixed; bottom: 16px; right: 16px; z-index: 80; max-width: clamp(260px, 30vw, 420px); }
    .video-bottom { width: 100%; height: auto; border-radius: 10px; border: 1px solid rgba(255,255,255,0.25); object-fit: cover; background: #000; display: block; }
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
        
        # Tab content containers
        with ui.column().classes('w-full mt-4').style('max-height: calc(100vh - 200px); overflow-y: auto;') as tab_container:
            # CASH Tab
            with ui.column().classes('w-full') as cash_tab:
                cash_tab.set_visibility(False)
                tab_contents['cash'] = cash_tab
                lbl = ui.label(t('tab_revenue')).classes('text-yellow-500 font-bold mb-4 text-center').style('font-size: 14px')
                ui_refs['tab_revenue'] = lbl
                
                revenue_labels = {}
                for bid in SERVICE_NAMES.keys():
                    with ui.row().classes('w-full justify-between items-center mb-3 p-2').style('background: #1e293b; border-radius: 8px;'):
                        nl = ui.label(t(bid)).classes('text-white font-bold')
                        revenue_name_refs[bid] = nl
                        revenue_labels[bid] = ui.label('0 UZS').classes('text-yellow-500 font-bold')
                
                ui.separator().classes('my-4')
                with ui.row().classes('w-full justify-between items-center p-3').style('background: #0f172a; border: 2px solid var(--primary); border-radius: 8px;'):
                    tl = ui.label(t('total')).classes('text-white font-bold text-lg')
                    ui_refs['total'] = tl
                    total_revenue_label = ui.label('0 UZS').classes('text-yellow-500 font-bold text-lg')
                
                def update_revenue_display():
                    total = 0
                    for bid in SERVICE_NAMES.keys():
                        revenue = service_revenue[bid]
                        total += revenue
                        if bid in revenue_labels:
                            revenue_labels[bid].set_text(f"{format_money(revenue)} UZS")
                    total_revenue_label.set_text(f"{format_money(total)} UZS")
                
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
                
                price_inputs = {}
                price_name_refs = {}
                
                for bid in SERVICE_NAMES.keys():
                    config = service_config[bid]
                    
                    with ui.card().classes('w-full mb-3').style('background: #1e293b;'):
                        nl = ui.label(t(bid)).classes('text-yellow-500 font-bold mb-2')
                        info_name_refs[bid] = nl

                        pl = ui.label(t('price_per_min')).classes('text-white text-sm mb-1')
                        price_per_min_refs.append(pl)
                        price_input = ui.input(
                            label='',
                            value=str(int(config["price_per_min"])),
                            placeholder='UZS/min',
                        ).props('outlined dense autocomplete=off').classes('w-full menu-admin-input')
                        price_inputs[bid] = price_input
                        
                        def make_save_handler(bid):
                            def save():
                                try:
                                    raw = str(price_inputs[bid].value or '').strip().replace(',', '.')
                                    price_per_min = int(float(raw or 0))
                                    if price_per_min <= 0:
                                        ui.notify(t('price_positive'), color='red')
                                        return
                                    update_service_config(bid, price_per_min)
                                    save_app_state()
                                    ui.notify(f"{t(bid)} {t('config_saved')}", color='green')
                                except Exception:
                                    ui.notify(t('invalid_input'), color='red')
                            return save
                        
                        save_btn = ui.button(t('save'), on_click=make_save_handler(bid)).classes('w-full mt-2').props('color=primary')
                        save_btn_refs.append(save_btn)

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

    # Global Q — must go through NiceGUI so menu state and DOM stay in sync (raw JS toggle was unreliable).
    ui.keyboard(on_key=_menu_hotkey, ignore=['input', 'textarea', 'select'])

    # --- Bell (admin call) center-right ---
    with ui.element('div').classes('fixed z-[110]').style('top: 50%; right: 20px; transform: translateY(-50%);'):
        bell_btn_ref[0] = ui.button(icon='notifications_active').props('flat round').classes('bell-btn').on('click', send_bell_signal)

    # --- Price bar (always visible when service selected) ---
    with ui.row().classes('price-bar price-bar-hidden').style('align-items: center;') as price_bar:
        price_bar_ref[0] = price_bar
        with ui.element('div').classes('price-bar-icon-wrap'):
            price_bar_icon_ref[0] = ui.html('')
        price_bar_label_ref[0] = ui.label('').classes('font-bold price-bar-label')

    # --- Timer display ---
    def swap_display():
        display_mode[0] = 1 if display_mode[0] == 0 else 0
        update_ui()

    with ui.element('div').classes('custom-display cursor-pointer').on('click', swap_display):
        with ui.row().classes('items-baseline'):
            main_display = ui.label('').classes('main-val')
            main_unit = ui.label('').classes('main-unit ml-2')
        sub_display = ui.label('').classes('sub-info')

    # --- СЕТКА ---
    BUTTONS_DATA = [
        "btn1", "btn2", "btn3", "btn4", "btn5", "btn6", "btn7", "btn8",
        "btn9", "btn10", "btn11", "btn12", "btn13", "btn14", "btn_pause"
    ]
    with ui.element('div').classes('grid-wrapper'):
        with ui.element('div').classes('screen-center'):
            with ui.element('div').classes('buttons-grid'):
                for bid in BUTTONS_DATA:
                    btn = ui.element('div').classes('action-btn icon-idle')
                    btn.on('click', lambda e, b=bid: handle_click(b))
                    with btn:
                        if bid == 'btn_pause':
                            pause_refs['svg'] = ui.html('')
                            pause_refs['label'] = ui.label(t('start')).classes('font-bold mt-2 text-center').style('font-size: 1.4vmin')
                        else:
                            path = SVG_PATHS.get(bid)
                            if not path:
                                path = "M500 200a300 300 0 1 0 0.001 0z"
                            ui.html(f'<svg width="4.5vmin" height="4.5vmin" viewBox="0 0 1000 1000"><path d="{path}"/></svg>')
                            lbl = ui.label(t(bid)).classes('font-bold mt-2 text-center').style('font-size: 1.4vmin')
                            grid_label_refs[bid] = lbl
                    btns[bid] = btn

    # --- Bottom-right video button ---
    with ui.element('div').classes('video-bottom-wrap'):
        ui.button(icon='ondemand_video').props('round fab color=primary').classes('shadow-lg')

    update_ui()
    update_price_bar()
    update_pause_visuals()

ui.run(
    fullscreen=True,   # полноэкранный режим
    native=True,       # отдельное окно (не браузер)
    show=True,
    title="Tesla Pro",
    reload=False
)