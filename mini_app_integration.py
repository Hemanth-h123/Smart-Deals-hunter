"""
Integration module for Telegram Mini App functionality
"""

import asyncio
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from webapp import app
from database import DatabaseManager, Product
from sqlalchemy import or_
from datetime import datetime
import logging
from tunnel_setup import setup_ngrok_tunnel

logger = logging.getLogger(__name__)

class MiniAppIntegration:
    def __init__(self, webapp_url=None):
        self.webapp_url = webapp_url
        self.db = DatabaseManager()
        self.tunnel_url = None
    
    async def send_daily_deals_message(self, context, chat_id):
        """Send daily deals message with mini app button"""
        session = self.db.get_session()
        
        # Get top 5 daily deals
        today = datetime.now().date()
        daily_deals = session.query(Product).filter(
            or_(
                Product.is_daily_deal == True,
                Product.created_at >= today
            )
        ).filter(Product.is_active == True).order_by(Product.discount_percentage.desc()).limit(5).all()
        
        if not daily_deals:
            message = "🔍 No daily deals available right now. Check back later!"
        else:
            message = "🔥 **Today's Hot Deals** 🔥\n\n"
            
            for i, product in enumerate(daily_deals, 1):
                discount_text = f" (-{product.discount_percentage:.0f}%)" if product.discount_percentage else ""
                price_text = f"${product.price:.2f}" if product.price else "Check Price"
                
                message += f"{i}. **{product.title[:40]}{'...' if len(product.title) > 40 else ''}**\n"
                message += f"💰 {price_text}{discount_text}\n"
                message += f"🏪 {product.store.name if product.store else 'Multiple Stores'}\n\n"
            
            message += "👆 *Open the app below to see ALL deals and browse categories!*"
        
        # Use tunnel URL if available, otherwise skip web app button
        keyboard = []
        if self.webapp_url:
            keyboard.append([InlineKeyboardButton("🛍️ Open Deals App", web_app=WebAppInfo(url=self.webapp_url))])
        
        keyboard.extend([
            [InlineKeyboardButton("🔄 Refresh Deals", callback_data="daily_deals"),
             InlineKeyboardButton("📂 Categories", callback_data="categories")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error sending daily deals message: {e}")
    
    def get_webapp_button(self, text="🛍️ Open Deals App"):
        """Get web app button for inline keyboards"""
        if self.webapp_url:
            return InlineKeyboardButton(text, web_app=WebAppInfo(url=self.webapp_url))
        return None
    
    async def handle_webapp_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle data sent from the web app"""
        if update.web_app_data:
            data = update.web_app_data.data
            # Process web app data if needed
            logger.info(f"Received web app data: {data}")
    
    def start_webapp_server(self):
        """Start the Flask web app server with HTTPS tunnel"""
        def run_server():
            app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        
        # Start Flask server
        webapp_thread = threading.Thread(target=run_server, daemon=True)
        webapp_thread.start()
        logger.info("Web app server started on http://localhost:5000")
        
        # Setup HTTPS tunnel
        try:
            self.tunnel_url = setup_ngrok_tunnel(5000)
            if self.tunnel_url:
                self.webapp_url = self.tunnel_url
                logger.info(f"HTTPS tunnel active: {self.webapp_url}")
            else:
                logger.warning("Failed to setup HTTPS tunnel. Mini app buttons will be disabled.")
                self.webapp_url = None
        except Exception as e:
            logger.error(f"Error setting up tunnel: {e}")
            self.webapp_url = None
        
        return webapp_thread
