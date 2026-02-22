import gc
import asyncio
from nicegui import ui

try:
    from icons import SVG_PATHS
except:
    SVG_PATHS = {f"btn{i}": "M500 100l100 800h-200z" for i in range(1, 16)}

gc.collect()

# --- БЛОК ФУНКЦИЙ ДЛЯ КАЖДОЙ КНОПКИ 
# Здесь прописывай логику для каждой кнопки отдельно
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

# --- СИСТЕМНАЯ ЛОГИКА ---
balance = [5000000.0]
current_rate = [0]
last_valid_rate = [10]
active_btn_id = [None]
is_paused = [True]  
display_mode = [0] 
currency_code = ["UZS"]
menu_open = [False]

btns, pause_refs = {}, {}

RATES = {f"btn{i}": 10 for i in range(1, 15)}
RATES.update({"btn1": 150, "btn2": 200}) # Цены за секунду

PATH_PAUSE = "M200 200h200v600h-200zM600 200h200v600h-200z" 
PATH_PLAY = "M300 200l500 300-500 300z" 

def update_ui():
    if 'main_display' not in globals(): return
    rate = current_rate[0] if current_rate[0] > 0 else last_valid_rate[0]
    sec = int(balance[0] / rate) if rate > 0 else 0
    money = int(balance[0])
    formatted_money = f"{money:,}".replace(",", " ")
    
    if display_mode[0] == 0:
        main_display.set_text(f"{sec}")
        main_unit.set_text("SEC")
        sub_display.set_text(f"{formatted_money} {currency_code[0]}")
    else:
        main_display.set_text(f"{formatted_money}")
        main_unit.set_text(currency_code[0])
        sub_display.set_text(f"{sec} SECONDS")

async def timer_loop():
    while True:
        if not is_paused[0] and active_btn_id[0] and balance[0] > 0:
            balance[0] -= current_rate[0]
            if balance[0] <= 0: 
                balance[0] = 0
                stop_everything()
            update_ui()
        await asyncio.sleep(1)

def stop_everything():
    is_paused[0], active_btn_id[0], current_rate[0] = True, None, 0
    refresh_button_visuals()
    update_ui()
    update_pause_visuals()

def handle_click(bid):
    if bid == 'btn_pause': 
        toggle_pause()
        return
    
    # 1. Выполняем специфическое действие кнопки через словарь
    action = BUTTON_ACTIONS.get(bid)
    if action:
        action()
    
    # 2. Логика выбора режима
    active_btn_id[0] = bid
    current_rate[0] = last_valid_rate[0] = RATES.get(bid, 10)
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

@ui.page('/')
def main_page():
    global main_display, main_unit, sub_display, left_panel
    btns.clear(); pause_refs.clear()
    
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
    .drawer-handle { position: absolute; top: 20px; right: -55px; width: 55px; height: 55px; background: #080c14; border: 2px solid var(--primary); border-left: none; border-radius: 0 12px 12px 0; color: var(--primary); display: flex; align-items: center; justify-content: center; cursor: pointer; }
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
    </style>
    """)

    # --- МЕНЮ ---
    with ui.element('div').classes('side-menu') as left_panel:
        with ui.element('div').classes('drawer-handle').on('click', toggle_menu):
            ui.icon('menu', size='30px')
        ui.label('TESLA WASH').classes('text-yellow-500 font-bold mb-8').style('font-size: 16px; letter-spacing: 4px')
        for icon, label in [('language', 'LANG'), ('qr_code_2', 'QR'), ('payments', 'CASH'), ('info', 'INFO')]:
            with ui.button().props('flat no-caps').classes('w-full mb-2'):
                with ui.row().classes('items-center w-full'):
                    ui.icon(icon, color='yellow-500', size='24px').classes('mr-4')
                    ui.label(label).classes('text-white text-sm font-bold')

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
                        path = SVG_PATHS.get(bid, "")
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