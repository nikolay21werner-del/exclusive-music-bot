#!/bin/bash
echo "Starting EXCLUSIVE MUSIC BOT + Proxy Server..."

# Export token explicitly if not already set
export BOT_TOKEN="${BOT_TOKEN:-7611594840:AAEAh5xvmWnMIpybzkIHPNPKKvWlEbozJ_E}"

echo "Bot token: ${BOT_TOKEN:0:10}..."

# Start bot in background with auto-restart loop
(while true; do
  echo "[BOT] Starting bot..."
  python bot.py
  echo "[BOT] Bot crashed, restarting in 5s..."
  sleep 5
done) &

echo "Bot loop started"

# Start proxy server in foreground (Railway keeps container alive via this)
python server.py
