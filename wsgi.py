"""后端入口：python wsgi.py，或 flask --app wsgi run --port 8000。"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
