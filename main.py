"""Control panel: one active button at a time; each button maps to one GPIO on Raspberry Pi Zero 2W."""
from nicegui import ui
from icons import SVG_PATHS

# 14 buttons, each wired to one BCM GPIO on the Pi (change pins to match your wiring)
BUTTONS = [
    {"id": "btn1",  "label": "пена",       "gpio": 2},
    {"id": "btn2",  "label": "сердце",     "gpio": 3},
    {"id": "btn3",  "label": "Кнопка 3",   "gpio": 4},
    {"id": "btn4",  "label": "Кнопка 4",   "gpio": 17},
    {"id": "btn5",  "label": "Кнопка 5",   "gpio": 27},
    {"id": "btn6",  "label": "Кнопка 6",   "gpio": 22},
    {"id": "btn7",  "label": "Кнопка 7",   "gpio": 23},
    {"id": "btn8",  "label": "Кнопка 8",   "gpio": 24},
    {"id": "btn9",  "label": "Кнопка 9",   "gpio": 10},
    {"id": "btn10", "label": "Кнопка 10",  "gpio": 9},
    {"id": "btn11", "label": "Кнопка 11",  "gpio": 11},
    {"id": "btn12", "label": "Кнопка 12",  "gpio": 5},
    {"id": "btn13", "label": "Кнопка 13",  "gpio": 6},
    {"id": "btn14", "label": "Кнопка 14",  "gpio": 13},
]

def send_to_pi(button_id: str, gpio: int) -> None:
    """Send active button to Pi: set this GPIO high, others low. Implement your transport (HTTP/socket/MQTT)."""
    # Example: requests.post("http://<PI_IP>/gpio", json={"active_gpio": gpio})
    print(button_id, "GPIO", gpio)

def apply_active_card() -> None:
    """Keep the selected card visually active (re-apply after any UI update)."""
    if active[0]:
        ui.run_javascript(
            "document.querySelectorAll('.action-btn').forEach(e=>e.classList.remove('active'));"
            f"var el=document.getElementById('{active[0]}');if(el)el.classList.add('active');"
        )

def on_button(btn_id: str, gpio: int) -> None:
    """Handle card click: switch active card and (on first selection) start timer."""
    prev_active = active[0]
    active[0] = btn_id
    send_to_pi(btn_id, gpio)

    # First selection: start fresh 1:00 timer.
    # Switching between cards while one is already active: keep current timer value.
    if not prev_active:
        timer_seconds[0] = 60
        is_paused[0] = False
        timer_label.set_text(format_time(60))
        pause_btn.set_text("Pause")

    apply_active_card()

active: list[str] = [""]
timer_seconds = [60]   # 1:00; runs only when a card is selected and not paused
is_paused = [True]     # True until user selects a card (then auto-start) or clicks Start

def format_time(s: int) -> str:
    return f"{s // 60:02d}:{s % 60:02d}"

def tick() -> None:
    if not active[0]:
        return
    if is_paused[0]:
        return
    if timer_seconds[0] <= 0:
        timer_seconds[0] = 60
        timer_label.set_text(format_time(60))
    else:
        timer_seconds[0] -= 1
        timer_label.set_text(format_time(timer_seconds[0]))
    apply_active_card()

def toggle_pause() -> None:
    if not active[0]:
        return
    is_paused[0] = not is_paused[0]
    if is_paused[0]:
        pause_btn.set_text("Start")
        pause_btn.style("color:#00ff00;")  # green for start
    else:
        pause_btn.set_text("Pause")
        pause_btn.style("color:#ff006e;")  # red when running / paused button

ui.add_head_html("""
<style>
:root{--primary-blue:#1E3A8A;--light-blue:#3B82F6;}
body{background:linear-gradient(135deg,#0F172A,#1E3A8A);margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;}
.timer-box{position:fixed;top:16px;right:16px;text-align:center;box-shadow:rgba(74,144,226,0.4) 0px 10px 40px;min-width:200px;background:linear-gradient(135deg,var(--primary-blue),var(--light-blue));padding:20px 40px;border-radius:20px;font-size:28px;font-weight:bold;color:rgba(255,255,255,.95);font-variant-numeric:tabular-nums;}
.buttons-container{position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);display:flex;flex-wrap:wrap;gap:24px;padding:24px;align-items:center;justify-content:center;}
.action-btn{padding:10px;width:120px;height:120px;border:4px solid rgba(255,255,255,.1);border-radius:25px;background:rgba(30,58,138,.3);color:#fff;transition:all .3s cubic-bezier(.34,1.56,.64,1);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;cursor:pointer;box-sizing:border-box;}
.action-btn.active{transform:scale(1.08) translateY(-4px);filter:brightness(1.3) drop-shadow(0 0 10px rgba(0,255,0,.6));border-color:rgb(0,255,0)!important;box-shadow:0 5px 20px rgba(0,255,0,.4);}
.action-btn.active svg path,.action-btn.active svg circle{fill:rgb(0,255,0);}
.action-btn-icon{width:100px;height:100px;display:flex;align-items:center;justify-content:center;}
.pause-row{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);}
.start-stop-button{
    font-size:16px;
    font-weight:700;
    cursor:pointer;
    display:flex;
    align-items:center;
    text-transform:uppercase;
    letter-spacing:1px;
    padding:16px 40px;
    border:2px solid currentColor;
    border-radius:12px;
    background:rgba(255,0,110,0.1);
    transition:0.3s;
    gap:10px;
}
</style>
""")

with ui.element("div").classes("timer-box"):
    timer_label = ui.label(format_time(timer_seconds[0]))

with ui.element("div").classes("buttons-container"):
    for b in BUTTONS:
        bid, label, gpio = b["id"], b["label"], b["gpio"]
        path = SVG_PATHS.get(bid)
        icon = f'<svg width="100" height="100" viewBox="0 0 1000 1000" style="fill:#F0F4F8"><path d="{path}"/></svg>' if path else '<div class="action-btn-icon"><!-- SVG --></div>'
        el = ui.html(f'<div id="{bid}" class="action-btn">{icon}<p style="font-size:20px;font-weight:bold">{label}</p></div>')
        el.on("click", lambda _bid=bid, _gpio=gpio: on_button(_bid, _gpio))

with ui.element("div").classes("pause-row"):
    pause_btn = ui.button("Start", on_click=toggle_pause)
    pause_btn.classes("start-stop-button")
    pause_btn.style("color:#00ff00;")  # green when paused / ready to start

ui.timer(1.0, tick)

ui.run(native=True, fullscreen=True, reload=False)
