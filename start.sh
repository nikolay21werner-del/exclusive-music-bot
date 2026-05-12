#!/bin/bash
echo "Starting EXCLUSIVE MUSIC BOT + Proxy Server..."
# Start bot in background
python bot.py &
BOT_PID=$!
echo "Bot PID: $BOT_PID"
# Start server in foreground (Railway needs a running process)
python server.py
