#!/bin/bash

source venv/bin/activate

# Simple stop script for market-making-bot
echo "Stopping market-making bot..."

# Find all python main.py processes and kill them
echo "Finding and killing all main.py processes..."
ps aux | grep "main.py" | awk '{print $2}' | xargs -r kill -2

# Give processes a moment to handle the SIGINT and cancel orders
echo "Waiting for processes to terminate gracefully..."
sleep 3

# Check if any processes are still running and force kill if necessary
REMAINING=$(ps aux | grep "main.py" | awk '{print $2}')
if [ ! -z "$REMAINING" ]; then
    echo "Some processes are still running. Force killing..."
    ps aux | grep "main.py" | awk '{print $2}' | xargs -r kill -9
    echo "All processes terminated."
else
    echo "All bot processes have been stopped successfully."
fi

# Clean up PID file if it exists
[ -f "bot.pid" ] && rm bot.pid
