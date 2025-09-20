#!/usr/bin/env python3
"""
Run the web application with HTTPS tunnel for Telegram Mini App
"""

from webapp import app
from mini_app_integration import MiniAppIntegration
import logging
import time
import threading

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Start the web app with HTTPS tunnel"""
    logger.info("Starting Affiliate Bot Web App...")
    
    # Initialize mini app integration
    mini_app = MiniAppIntegration()
    
    # Start web app server with tunnel
    webapp_thread = mini_app.start_webapp_server()
    
    if mini_app.webapp_url:
        logger.info(f"✅ Web app is running at: {mini_app.webapp_url}")
        logger.info("🔗 This URL can be used for Telegram Mini App integration")
        logger.info("📱 Add this URL to your Telegram bot's web app settings")
        
        # Save the URL to a file for the bot to use
        with open('webapp_url.txt', 'w') as f:
            f.write(mini_app.webapp_url)
        logger.info("💾 Web app URL saved to webapp_url.txt")
    else:
        logger.warning("⚠️ HTTPS tunnel failed. Web app running locally only.")
        logger.info("💡 Make sure ngrok is properly configured and try again")
    
    try:
        logger.info("🚀 Web app server is running. Press Ctrl+C to stop.")
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down web app...")

if __name__ == "__main__":
    main()
