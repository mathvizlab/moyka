import multiprocessing
from nicegui import ui

# 1. Твои стили (оставляем как есть)
ui.add_head_html('''
    <style>
        body { background-color: #121212; }
        .my-card {
            background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
            border: 1px solid #333;
            border-radius: 20px;
            color: white;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        .btn-glow {
            background: #00d8ff !important; /* Цвет React */
            color: black !important;
            font-weight: bold;
            transition: 0.3s;
        }
        .btn-glow:hover {
            box-shadow: 0 0 15px #00d8ff;
            transform: translateY(-2px);
        }
    </style>
''')

# 2. Оборачиваем создание интерфейса в функцию (хорошая практика)
def build_ui():
    with ui.column().classes('w-full items-center q-pa-md'):
        with ui.card().classes('my-card'):
            ui.label('Moyka OS').style('font-size: 32px; font-family: sans-serif;')
            ui.label('Интерфейс на Python + CSS').classes('text-grey-4')
            
            def on_click():
                ui.notify('Сигнал отправлен!', color='info', icon='rocket')

            ui.button('ЗАПУСТИТЬ', on_click=on_click) \
                .classes('btn-glow q-mt-md') \
                .props('rounded')

# 3. КРИТИЧЕСКИ ВАЖНЫЙ БЛОК ДЛЯ RASPBERRY PI
if __name__ in {"__main__", "__mp_main__"}:
    # Отключаем лишние процессы, чтобы не было ошибки SemLock
    multiprocessing.freeze_support()
    
    build_ui()
    
    ui.run(
        native=True, 
        window_size=(800, 480), 
        title='Moyka App',
        reload=False,     # Обязательно False на Pi Zero
        dark=True,        # Включаем темную тему движка
        show=False        # Не открывать браузер отдельно, только окно
    )

#     sudo apt update
# sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.0