"""
EXCLUSIVE MUSIC BOT — Audio Proxy Server
Выдаёт прямые ссылки на аудиофайлы из Telegram для воспроизведения в WebApp.
"""

import os
import requests
from flask import Flask, Response, jsonify, request
from flask_cors import CORS

BOT_TOKEN = "7611594840:AAEAh5xvmWnMIpybzkIHPNPKKvWlEbozJ_E"
_env_token = os.environ.get("BOT_TOKEN", "").strip().lstrip("=")
if _env_token:
    BOT_TOKEN = _env_token
TELEGRAM_API  = f"https://api.telegram.org/bot{BOT_TOKEN}"
TELEGRAM_FILE = f"https://api.telegram.org/file/bot{BOT_TOKEN}"

app = Flask(__name__)
CORS(app, origins="*")


@app.route("/")
def index():
    return jsonify({"status": "ok", "service": "EXCLUSIVE MUSIC BOT proxy"})


@app.route("/audio/<path:file_id>")
def stream_audio(file_id):
    """Стримит аудиофайл из Telegram напрямую в браузер."""
    try:
        # Получаем путь к файлу
        r = requests.get(f"{TELEGRAM_API}/getFile",
                         params={"file_id": file_id}, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data.get("ok"):
            return jsonify({"error": "Telegram error"}), 502

        file_path = data["result"]["file_path"]
        file_url  = f"{TELEGRAM_FILE}/{file_path}"

        # Поддержка Range (перемотка)
        range_header = request.headers.get("Range")
        req_headers  = {"Range": range_header} if range_header else {}

        tg = requests.get(file_url, headers=req_headers,
                          stream=True, timeout=60)

        ctype = tg.headers.get("Content-Type", "audio/mpeg")
        if "octet-stream" in ctype:
            ctype = "audio/mpeg"

        resp_headers = {
            "Content-Type": ctype,
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*",
        }
        for h in ("Content-Length", "Content-Range"):
            if h in tg.headers:
                resp_headers[h] = tg.headers[h]

        def generate():
            for chunk in tg.iter_content(chunk_size=16384):
                if chunk:
                    yield chunk

        return Response(generate(), status=tg.status_code,
                        headers=resp_headers)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🎵 EXCLUSIVE MUSIC BOT proxy на порту {port}")
    app.run(host="0.0.0.0", port=port, threaded=True)


import subprocess
import json as _json

@app.route("/yt/url")
def yt_url():
    """Возвращает прямую аудио-ссылку YouTube по запросу."""
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "no query"}), 400
    try:
        result = subprocess.run(
            ["yt-dlp", "-f", "bestaudio", "--get-url",
             "--no-playlist", f"ytsearch1:{q}"],
            capture_output=True, text=True, timeout=15
        )
        url = result.stdout.strip().split("\n")[0]
        if not url:
            return jsonify({"error": "not found"}), 404
        return jsonify({"url": url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/yt/stream")
def yt_stream():
    """Стримит аудио с YouTube напрямую."""
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "no query"}), 400
    try:
        result = subprocess.run(
            ["yt-dlp", "-f", "bestaudio", "--get-url",
             "--no-playlist", f"ytsearch1:{q}"],
            capture_output=True, text=True, timeout=15
        )
        yt_url_str = result.stdout.strip().split("\n")[0]
        if not yt_url_str:
            return jsonify({"error": "not found"}), 404

        range_header = request.headers.get("Range")
        req_headers = {"Range": range_header} if range_header else {}
        req_headers["User-Agent"] = "Mozilla/5.0"

        r = requests.get(yt_url_str, headers=req_headers, stream=True, timeout=60)
        ctype = r.headers.get("Content-Type", "audio/webm")

        resp_headers = {
            "Content-Type": ctype,
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=600",
            "Access-Control-Allow-Origin": "*",
        }
        for h in ("Content-Length", "Content-Range"):
            if h in r.headers:
                resp_headers[h] = r.headers[h]

        def generate():
            for chunk in r.iter_content(chunk_size=16384):
                if chunk:
                    yield chunk

        return Response(generate(), status=r.status_code, headers=resp_headers)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
