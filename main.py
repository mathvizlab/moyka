from nicegui import ui

# 1. Можно добавить свой CSS файл или стили строкой
ui.add_head_html('''
    <style>
        .my-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            color: white;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }
        .btn-glow:hover {
            box-shadow: 0 0 20px #764ba2;
            transform: scale(1.05);
            transition: 0.3s;
        }
    </style>
''')

with ui.card().classes('my-card'):
    ui.label('Привет с Raspberry Pi!').style('font-size: 24px; font-weight: bold;')
    
    def on_click():
        ui.notify('Python выполнил задачу!', color='positive')

    ui.button('Твоя кнопка из React', on_click=on_click) \
        .classes('btn-glow') \
        .props('flat color=white')

# Запуск в режиме "родного окна" (использует упрощенный браузер)
ui.run(native=True, window_size=(800, 480), title='Moyka App')