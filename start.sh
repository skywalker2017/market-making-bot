#!/bin/bash

# Start script for market-making-bot
echo "Starting market-making bot..."

source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Make sure your environment variables are set correctly."
fi

# Start the bot in the background and save its PID
python3 -u main.py "$@" > bot.log 2>&1 &
PID=$!

# Save the PID to a file for the stop script
echo $PID > bot.pid

echo "Market-making bot started with PID: $PID"
echo "Logs are being written to bot.log"
echo "Use ./stop.sh to stop the bot"
