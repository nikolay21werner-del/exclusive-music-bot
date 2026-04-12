"""
EXCLUSIVE MUSIC BOT — Audio Proxy Server
Проксирует аудиофайлы из Telegram для воспроизведения в WebApp.

Запуск:
  pip install flask requests
  BOT_TOKEN=your_token python server.py
"""

import os
import requests
from flask import Flask, Response, jsonify, request
from flask_cors import CORS

BOT_TOKEN = os.environ.get("BOT_TOKEN", "7611594840:AAEAh5xvmWnMIpybzkIHPNPKKvWlEbozJ_E")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
TELEGRAM_FILE = f"https://api.telegram.org/file/bot{BOT_TOKEN}"

app = Flask(__name__)
CORS(app, origins="*")


@app.route("/")
def index():
    return jsonify({"status": "ok", "service": "EXCLUSIVE MUSIC BOT proxy"})


@app.route("/audio/<file_id>")
def stream_audio(file_id):
    """Получает файл из Telegram и стримит его браузеру."""
    try:
        # Шаг 1 — получаем путь к файлу
        r = requests.get(f"{TELEGRAM_API}/getFile", params={"file_id": file_id}, timeout=10)
        r.raise_for_status()
        data = r.json()

        if not data.get("ok"):
            return jsonify({"error": "Telegram API error", "details": data}), 502

        file_path = data["result"]["file_path"]

        # Шаг 2 — стримим файл
        file_url = f"{TELEGRAM_FILE}/{file_path}"
        range_header = request.headers.get("Range", None)

        headers = {}
        if range_header:
            headers["Range"] = range_header

        tg_resp = requests.get(file_url, headers=headers, stream=True, timeout=30)

        # Передаём заголовки браузеру
        response_headers = {
            "Content-Type": tg_resp.headers.get("Content-Type", "audio/mpeg"),
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600",
        }
        if "Content-Length" in tg_resp.headers:
            response_headers["Content-Length"] = tg_resp.headers["Content-Length"]
        if "Content-Range" in tg_resp.headers:
            response_headers["Content-Range"] = tg_resp.headers["Content-Range"]

        status_code = tg_resp.status_code

        def generate():
            for chunk in tg_resp.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

        return Response(generate(), status=status_code, headers=response_headers)

    except requests.exceptions.Timeout:
        return jsonify({"error": "Telegram timeout"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🎵 EXCLUSIVE MUSIC BOT proxy запущен на порту {port}")
    app.run(host="0.0.0.0", port=port)
