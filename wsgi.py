#!/usr/bin/env python3
"""
WSGI entry point for Render deployment
This file tricks Render into thinking it's a Flask app but actually runs the bot
"""
import os
import subprocess
import sys
from flask import Flask

# Create a dummy Flask app for Render's auto-detection
app = Flask(__name__)

@app.route('/health')
def health():
    return {"status": "healthy", "service": "telegram-affiliate-bot"}, 200

@app.route('/')
def home():
    return {"message": "Telegram Affiliate Bot is running!", "status": "active"}, 200

# When this file is imported by gunicorn, start the actual bot
if __name__ != '__main__':
    # This runs when gunicorn imports this file
    import threading
    import time
    
    def start_bot():
        """Start the actual bot in a separate process"""
        time.sleep(2)  # Give Flask time to start
        try:
            subprocess.Popen([sys.executable, 'integrated_bot.py'])
        except Exception as e:
            print(f"Failed to start bot: {e}")
    
    # Start bot in background thread
    threading.Thread(target=start_bot, daemon=True).start()

if __name__ == '__main__':
    # Direct execution - just run the bot
    exec(open('integrated_bot.py').read())
