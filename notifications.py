import asyncio
import schedule
import time
from datetime import datetime, timedelta
from telegram import Bot
from telegram.error import TelegramError
from database import DatabaseManager, User, Product
from config import Config
import logging

logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self):
        self.db = DatabaseManager()
        self.bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
    
    async def send_daily_deals_notification(self):
        """Send daily deals to subscribed users"""
        session = self.db.get_session()
        
        # Get today's deals
        today = datetime.now().date()
        daily_deals = session.query(Product).filter(
            Product.is_daily_deal == True,
            Product.is_active == True
        ).limit(5).all()
        
        if not daily_deals:
            logger.info("No daily deals to send")
            return
        
        # Get active users
        users = session.query(User).filter_by(is_active=True).all()
        
        message = "🔥 **Today's Hot Deals** 🔥\n\n"
        for i, product in enumerate(daily_deals, 1):
            discount_text = f" (-{product.discount_percentage:.0f}%)" if product.discount_percentage else ""
            price_text = f"${product.price:.2f}" if product.price else "Check Price"
            
            message += f"{i}. **{product.title[:40]}{'...' if len(product.title) > 40 else ''}**\n"
            message += f"💰 {price_text}{discount_text}\n"
            message += f"🏪 {product.store.name if product.store else 'Multiple Stores'}\n\n"
        
        message += "Use /deals to see all deals and get shopping! 🛒"
        
        # Send to all users
        sent_count = 0
        for user in users:
            try:
                await self.bot.send_message(
                    chat_id=user.telegram_id,
                    text=message,
                    parse_mode='Markdown'
                )
                sent_count += 1
                await asyncio.sleep(0.1)  # Rate limiting
            except TelegramError as e:
                logger.error(f"Failed to send notification to user {user.telegram_id}: {e}")
                if "bot was blocked" in str(e).lower():
                    user.is_active = False
                    session.commit()
        
        logger.info(f"Daily deals notification sent to {sent_count} users")
    
    async def send_price_drop_alert(self, product, old_price, new_price, discount_percentage):
        """Send price drop alert for a specific product"""
        session = self.db.get_session()
        
        try:
            # Get users who have notifications enabled
            users = session.query(User).filter_by(
                is_active=True,
                notifications_enabled=True
            ).all()
            
            if not users:
                return
            
            message = f"🚨 **PRICE DROP ALERT** 🚨\n\n"
            message += f"🛒 **{product.title[:60]}{'...' if len(product.title) > 60 else ''}**\n\n"
            message += f"💰 **Was:** ${old_price:.2f}\n"
            message += f"💸 **Now:** ${new_price:.2f}\n"
            message += f"📉 **Save:** ${old_price - new_price:.2f} ({discount_percentage:.0f}% OFF)\n\n"
            message += f"🏪 **Store:** {product.store.name if product.store else 'Multiple Stores'}\n"
            message += f"⏰ **Limited time offer - Act fast!**\n\n"
            message += f"Use /start to browse deals!"
            
            sent_count = 0
            for user in users:
                try:
                    await self.bot.send_message(
                        chat_id=user.telegram_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    sent_count += 1
                    await asyncio.sleep(0.1)  # Rate limiting
                except TelegramError as e:
                    logger.error(f"Failed to send price alert to user {user.telegram_id}: {e}")
                    if "bot was blocked" in str(e).lower():
                        user.is_active = False
            
            session.commit()
            logger.info(f"Price drop alert sent to {sent_count} users for product {product.id}")
            
        except Exception as e:
            logger.error(f"Error sending price drop alert: {e}")
        finally:
            session.close()
    
    async def send_price_drop_alerts(self):
        """Send price drop alerts for tracked products"""
        logger.info("Price drop alerts check completed")
    
    def start_scheduler(self):
        """Start the notification scheduler"""
        # Schedule daily deals notification at 9 AM
        schedule.every().day.at("09:00").do(
            lambda: asyncio.create_task(self.send_daily_deals_notification())
        )
        
        # Schedule price drop checks every hour
        schedule.every().hour.do(
            lambda: asyncio.create_task(self.send_price_drop_alerts())
        )
        
        logger.info("Notification scheduler started")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

class UserPreferences:
    def __init__(self):
        self.db = DatabaseManager()
    
    def update_user_preferences(self, telegram_id, preferences):
        """Update user notification preferences"""
        session = self.db.get_session()
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        
        if user:
            user.preferred_categories = preferences.get('categories', '')
            user.max_price_filter = preferences.get('max_price')
            user.min_discount_filter = preferences.get('min_discount')
            session.commit()
            return True
        
        return False
    
    def get_user_preferences(self, telegram_id):
        """Get user preferences"""
        session = self.db.get_session()
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        
        if user:
            return {
                'categories': user.preferred_categories,
                'max_price': user.max_price_filter,
                'min_discount': user.min_discount_filter
            }
        
        return None
