import webview

html = """
<html>
  <body>
    <h1>Hello from Python!</h1>
    <button onclick="pywebview.api.say_hello()">Click me</button>
  </body>
</html>
"""

class Api:
    def say_hello(self):
        print("Button clicked!")

# Полноэкранное окно
webview.create_window("My Window", html=html, js_api=Api(), fullscreen=True)
webview.start()

a = _pat_11BKK3PJY0DQDm89uvQ8FY_
1= eTesvbY4cEd2ufjYTzHM7S6Lf6rEXPuILLsXkVNcCth5YALDBAHb6iWKzWK