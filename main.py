import gc
import asyncio
import json
from nicegui import ui

try:
    from icons import SVG_PATHS
except:
    SVG_PATHS = {f"btn{i}": "M500 100l100 800h-200z" for i in range(1, 16)}

gc.collect()

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

# --- СИСТЕМНАЯ ЛОГИКА ---
balance = [5000000.0]
active_btn_id = [None]
is_paused = [True]  
display_mode = [0] 
currency_code = ["UZS"]
menu_open = [False]
current_tab = [None]

btns, pause_refs = {}, {}

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
    if not active_btn_id[0] or active_btn_id[0] not in service_config:
        return 0
    return service_config[active_btn_id[0]]["price_per_second"]

def update_ui():
    if 'main_display' not in globals(): return
    rate = get_current_price_per_second()
    total_seconds = int(balance[0] / rate) if rate > 0 else 0
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    time_str = f"{minutes:02d}:{seconds:02d}"
    money = int(balance[0])
    formatted_money = f"{money:,}".replace(",", " ")

    main_display.set_text(time_str)
    main_unit.set_text("TIME")
    sub_display.set_text(f"{formatted_money} {currency_code[0]}")

async def timer_loop():
    while True:
        if not is_paused[0] and active_btn_id[0] and balance[0] > 0:
            price_per_sec = get_current_price_per_second()
            if price_per_sec > 0:
                balance[0] -= price_per_sec
                service_revenue[active_btn_id[0]] += price_per_sec
                if balance[0] <= 0: 
                    balance[0] = 0
                    stop_everything()
                update_ui()
                save_app_state()
        await asyncio.sleep(1)

def stop_everything():
    is_paused[0] = True
    active_btn_id[0] = None
    refresh_button_visuals()
    update_ui()
    update_pause_visuals()

def handle_click(bid):
    if bid == 'btn_pause': 
        toggle_pause()
        return
    
    action = BUTTON_ACTIONS.get(bid)
    if action:
        action()
    
    active_btn_id[0] = bid
    # temporary fixed session: 30 minutes per activation
    price_per_sec = get_current_price_per_second()
    if price_per_sec > 0:
        balance[0] = 30 * 60 * price_per_sec
    else:
        balance[0] = 0
    refresh_button_visuals()
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
        ui.notify("CHOOSE MODE", color='orange')
        return
    is_paused[0] = not is_paused[0]
    update_pause_visuals()

def update_pause_visuals():
    p_btn = btns.get('btn_pause')
    if not p_btn or 'svg' not in pause_refs: return
    
    if is_paused[0]:
        p_btn.classes(remove='pause-active scale-active', add='pause-stopped')
        pause_refs['label'].set_text('START')
        pause_refs['svg'].content = f'<svg width="5.5vmin" height="5.5vmin" viewBox="0 0 1000 1000" style="fill:#2ecc71; transition: 0.3s;"><path d="{PATH_PLAY}"/></svg>'
    else:
        p_btn.classes(remove='pause-stopped', add='pause-active scale-active')
        pause_refs['label'].set_text('STOP')
        pause_refs['svg'].content = f'<svg width="5.5vmin" height="5.5vmin" viewBox="0 0 1000 1000" style="fill:#ff4757; transition: 0.3s;"><path d="{PATH_PAUSE}"/></svg>'

def toggle_menu():
    menu_open[0] = not menu_open[0]
    left_panel.classes(add='menu-visible' if menu_open[0] else '', remove='menu-visible' if not menu_open[0] else '')

def update_service_config(bid, price_per_min):
    if bid not in service_config:
        return
    service_config[bid]["price_per_min"] = price_per_min
    service_config[bid]["price_per_second"] = price_per_min / 60 if price_per_min > 0 else 0
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
    btns.clear(); pause_refs.clear()
    tab_contents.clear()
    
    load_app_state()

    ui.timer(0, timer_loop, once=True)

    ui.add_head_html("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&display=swap');
    :root { --primary: #ffcc00; --bg: #020617; --btn-size: clamp(75px, 13vmin, 130px); }
    body { background: var(--bg); margin: 0; font-family: 'Orbitron', sans-serif; overflow: hidden; color: white; }
    .action-btn svg { fill: #64748b; transition: 0.2s; }
    .icon-active svg { fill: var(--primary) !important; }
    .scale-active { transform: scale(1.1); z-index: 10; }
    .side-menu { position: fixed; top: 0; left: -280px; width: 280px; height: 100vh; background: #080c14; border-right: 2px solid var(--primary); z-index: 2000; transition: 0.4s; display: flex; flex-direction: column; padding: 40px 20px; }
    .menu-visible { left: 0 !important; }
    .drawer-handle { display: none !important; }
    .custom-display { position: fixed; top: 20px; right: 0; z-index: 100; background: #0f172a; border: 1.5px solid var(--primary); border-radius: 25px 0 0 25px; padding: 15px 35px; display: flex; flex-direction: column; align-items: flex-end; }
    .main-val { color: #00f2ff; font-size: 5.5vmin; font-weight: 900; line-height: 1; }
    .main-unit { font-size: 1.8vmin; color: var(--primary); }
    .sub-info { color: #94a3b8; font-size: 2vmin; margin-top: 4px; }
    .screen-center { position: absolute; top: 52%; left: 50%; transform: translate(-50%, -40%); width: 95%; display: flex; justify-content: center; }
    .buttons-grid { display: grid; grid-template-columns: repeat(5, var(--btn-size)); gap: 2.5vmin; } 
    .action-btn { width: var(--btn-size); height: var(--btn-size); border-radius: 18%; background: #1e293b; border: 1px solid rgba(255, 255, 255, 0.1); color: #64748b; display: flex; flex-direction: column; align-items: center; justify-content: center; cursor: pointer; transition: 0.2s; }
    .active-yellow { border: 2.5px solid var(--primary) !important; color: white !important; }
    .pause-stopped { border: 2.5px solid #2ecc71 !important; color: #2ecc71 !important; }
    .pause-active { border: 2.5px solid #ff4757 !important; color: #ff4757 !important; }
    .tab-content { padding: 10px 0; }
    .tab-content::-webkit-scrollbar { width: 6px; }
    .tab-content::-webkit-scrollbar-track { background: #0f172a; }
    .tab-content::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 3px; }
    </style>
    <script>
    document.addEventListener('keydown', function(e) {
        if (e.key === 'q' || e.key === 'Q') {
            e.preventDefault();
            const menu = document.querySelector('.side-menu');
            if (menu) {
                menu.classList.toggle('menu-visible');
            }
        }
    });
    </script>
    """)

    # --- МЕНЮ ---
    tab_contents = {}
    with ui.element('div').classes('side-menu') as left_panel:
        ui.label('TESLA WASH').classes('text-yellow-500 font-bold mb-8').style('font-size: 16px; letter-spacing: 4px')
        
        # Tab buttons
        with ui.column().classes('w-full'):
            lang_btn = ui.button().props('flat no-caps').classes('w-full mb-2 justify-start')
            with lang_btn:
                with ui.row().classes('items-center w-full'):
                    ui.icon('language', color='yellow-500', size='24px').classes('mr-4')
                    ui.label('Language').classes('text-white text-sm font-bold')
            
            qr_btn = ui.button().props('flat no-caps').classes('w-full mb-2 justify-start')
            with qr_btn:
                with ui.row().classes('items-center w-full'):
                    ui.icon('qr_code_2', color='yellow-500', size='24px').classes('mr-4')
                    ui.label('QR').classes('text-white text-sm font-bold')
            
            cash_btn = ui.button().props('flat no-caps').classes('w-full mb-2 justify-start').on('click', lambda: show_tab('cash'))
            with cash_btn:
                with ui.row().classes('items-center w-full'):
                    ui.icon('payments', color='yellow-500', size='24px').classes('mr-4')
                    ui.label('Cash').classes('text-white text-sm font-bold')
            
            info_btn = ui.button().props('flat no-caps').classes('w-full mb-2 justify-start').on('click', lambda: show_tab('info'))
            with info_btn:
                with ui.row().classes('items-center w-full'):
                    ui.icon('info', color='yellow-500', size='24px').classes('mr-4')
                    ui.label('Info').classes('text-white text-sm font-bold')
        
        # Tab content containers
        with ui.column().classes('w-full mt-4').style('max-height: calc(100vh - 200px); overflow-y: auto;') as tab_container:
            # CASH Tab
            with ui.column().classes('w-full') as cash_tab:
                cash_tab.set_visibility(False)
                tab_contents['cash'] = cash_tab
                ui.label('REVENUE DASHBOARD').classes('text-yellow-500 font-bold mb-4 text-center').style('font-size: 14px')
                
                revenue_labels = {}
                for bid in SERVICE_NAMES.keys():
                    name = SERVICE_NAMES[bid]
                    with ui.row().classes('w-full justify-between items-center mb-3 p-2').style('background: #1e293b; border-radius: 8px;'):
                        ui.label(name).classes('text-white font-bold')
                        revenue_labels[bid] = ui.label('0 UZS').classes('text-yellow-500 font-bold')
                
                ui.separator().classes('my-4')
                with ui.row().classes('w-full justify-between items-center p-3').style('background: #0f172a; border: 2px solid var(--primary); border-radius: 8px;'):
                    ui.label('TOTAL').classes('text-white font-bold text-lg')
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
            
            # INFO Tab
            with ui.column().classes('w-full') as info_tab:
                info_tab.set_visibility(False)
                tab_contents['info'] = info_tab
                ui.label('PRICE CONFIGURATION').classes('text-yellow-500 font-bold mb-4 text-center').style('font-size: 14px')
                
                price_inputs = {}
                
                for bid in SERVICE_NAMES.keys():
                    name = SERVICE_NAMES[bid]
                    config = service_config[bid]
                    
                    with ui.card().classes('w-full mb-3').style('background: #1e293b;'):
                        ui.label(name).classes('text-yellow-500 font-bold mb-2')

                        ui.label('Price / minute (UZS):').classes('text-white text-sm mb-1')
                        price_input = ui.number(label='', value=config["price_per_min"], format='%.0f', precision=0).classes('w-full text-white')
                        price_inputs[bid] = price_input
                        
                        def make_save_handler(bid):
                            def save():
                                try:
                                    price_per_min = int(price_inputs[bid].value)
                                    if price_per_min <= 0:
                                        ui.notify("Price must be positive", color='red')
                                        return
                                    update_service_config(bid, price_per_min)
                                    save_app_state()
                                    ui.notify(f"{SERVICE_NAMES[bid]} configuration saved", color='green')
                                except Exception:
                                    ui.notify("Invalid input", color='red')
                            return save
                        
                        ui.button('SAVE', on_click=make_save_handler(bid)).classes('w-full mt-2').props('color=primary')
    

    # --- ДИСПЛЕЙ ---
    with ui.element('div').classes('custom-display cursor-pointer').on('click', lambda: (display_mode.__setitem__(0, 1 if display_mode[0] == 0 else 0), update_ui())):
        with ui.row().classes('items-baseline'):
            global main_display, main_unit, sub_display
            main_display = ui.label('').classes('main-val')
            main_unit = ui.label('').classes('main-unit ml-2')
        sub_display = ui.label('').classes('sub-info')

    # --- СЕТКА ---
    BUTTONS_DATA = [
        ("btn1", "FOAM"), ("btn2", "WAX"), ("btn3", "WATER"), ("btn4", "AIR"), ("btn5", "OSMOS"),
        ("btn6", "TURBO"), ("btn7", "SHAMPOO"), ("btn8", "POLISH"), ("btn9", "STEAM"), ("btn10", "VACUUM"),
        ("btn11", "WHEELS"), ("btn12", "DRY"), ("btn13", "SMELL"), ("btn14", "WASH"), ("btn_pause", "START")
    ]

    with ui.element('div').classes('screen-center'):
        with ui.element('div').classes('buttons-grid'):
            for bid, label in BUTTONS_DATA:
                btn = ui.element('div').classes('action-btn icon-idle')
                btn.on('click', lambda e, b=bid: handle_click(b))
                with btn:
                    if bid == 'btn_pause':
                        pause_refs['svg'] = ui.html('')
                        pause_refs['label'] = ui.label(label).classes('font-bold mt-2 text-center').style('font-size: 1.4vmin')
                    else:
                        path = SVG_PATHS.get(bid)
                        if not path:
                            # fallback minimal icon (circle)
                            path = "M500 200a300 300 0 1 0 0.001 0z"
                        ui.html(f'<svg width="4.5vmin" height="4.5vmin" viewBox="0 0 1000 1000"><path d="{path}"/></svg>')
                        ui.label(label).classes('font-bold mt-2 text-center').style('font-size: 1.4vmin')
                btns[bid] = btn
    
    update_ui()
    update_pause_visuals()

ui.run(
    fullscreen=True,   # полноэкранный режим
    native=True,       # отдельное окно (не браузер)
    show=True,
    title="Tesla Pro",
    reload=False
)