
# Add this to your integrated_bot.py for Render health checks
import threading
from flask import Flask

def start_health_server():
    """Start health check server for Render"""
    app = Flask(__name__)
    
    @app.route('/health')
    def health():
        return {"status": "healthy", "service": "telegram-affiliate-bot"}, 200
    
    @app.route('/')
    def home():
        return {"message": "Telegram Affiliate Bot is running!", "status": "active"}, 200
    
    # Run health server in background
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=False)

# Add this to your integrated_bot.py main function:
# threading.Thread(target=start_health_server, daemon=True).start()
