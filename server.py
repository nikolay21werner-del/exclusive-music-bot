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


@app.route("/play", methods=["POST", "OPTIONS"])
def play_track():
    """WebApp отправляет file_id и chat_id — бот отсылает аудио пользователю."""
    if request.method == "OPTIONS":
        resp = Response()
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp

    try:
        data = request.get_json(force=True)
        file_id = data.get("file_id", "")
        chat_id = data.get("chat_id", "")
        title   = data.get("title", "")
        artist  = data.get("artist", "")

        if not file_id or not chat_id:
            return jsonify({"error": "file_id and chat_id required"}), 400

        caption = f"🎵 <b>{title}</b> \u2014 {artist}\n\n🔥 EXCLUSIVE MUSIC BOT"

        r = requests.post(
            f"{TELEGRAM_API}/sendAudio",
            json={
                "chat_id": chat_id,
                "audio": file_id,
                "caption": caption,
                "parse_mode": "HTML",
            },
            timeout=15,
        )
        result = r.json()
        resp = jsonify({"ok": result.get("ok"), "result": "sent"})
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp

    except Exception as e:
        return jsonify({"error": str(e)}), 500


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

        # Шаг 2 — скачиваем файл и отдаём браузеру
        file_url = f"{TELEGRAM_FILE}/{file_path}"

        tg_resp = requests.get(file_url, stream=True, timeout=60)
        tg_resp.raise_for_status()

        content_type = tg_resp.headers.get("Content-Type", "audio/mpeg")
        # Убеждаемся что тип аудио
        if "octet-stream" in content_type:
            content_type = "audio/mpeg"

        response_headers = {
            "Content-Type": content_type,
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=86400",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Range, Content-Type",
        }
        if "Content-Length" in tg_resp.headers:
            response_headers["Content-Length"] = tg_resp.headers["Content-Length"]

        def generate():
            for chunk in tg_resp.iter_content(chunk_size=16384):
                if chunk:
                    yield chunk

        return Response(generate(), status=200, headers=response_headers)

    except requests.exceptions.Timeout:
        return jsonify({"error": "Telegram timeout"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🎵 EXCLUSIVE MUSIC BOT proxy запущен на порту {port}")
    app.run(host="0.0.0.0", port=port)
