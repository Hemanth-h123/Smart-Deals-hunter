#!/usr/bin/env python3
"""
Integrated Telegram Affiliate Bot with all features
"""
import logging
import asyncio
import signal
import sys
import threading
from datetime import datetime
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from flask import Flask

from config import Config
from database import DatabaseManager
from bot_handlers import BotHandlers
from admin_panel import AdminPanel
from mini_app_integration import MiniAppIntegration
from price_monitor import BackgroundTaskManager
from analytics import AnalyticsManager
from notifications import NotificationManager
from group_manager import GroupManager

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class IntegratedAffiliateBot:
    def __init__(self):
        """Initialize the integrated bot with all features"""
        self.db = DatabaseManager()
        self.analytics = AnalyticsManager()
        self.notification_manager = NotificationManager()
        self.background_tasks = BackgroundTaskManager()
        
        # Initialize mini app integration
        self.mini_app = MiniAppIntegration()
        
        # Initialize handlers with mini app integration
        self.bot_handlers = BotHandlers(mini_app=self.mini_app)
        self.admin_panel = AdminPanel()
        self.group_manager = GroupManager(analytics_manager=self.analytics)
        
        # Create application
        self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        logger.info("Integrated Affiliate Bot initialized")
    
    def setup_handlers(self):
        """Set up all command and callback handlers"""
        # Admin commands
        self.application.add_handler(CommandHandler("admin", self.admin_panel.admin_command))
        
        # Group commands
        for handler in self.group_manager.get_handlers():
            self.application.add_handler(handler)
        
        # User commands
        self.application.add_handler(CommandHandler("start", self.bot_handlers.start_command))
        self.application.add_handler(CommandHandler("help", self.bot_handlers.help_command))
        self.application.add_handler(CommandHandler("deals", self.bot_handlers.deals_command))
        self.application.add_handler(CommandHandler("categories", self.bot_handlers.categories_command))
        self.application.add_handler(CommandHandler("search", self.enhanced_search_command))
        
        # Callback query handler
        self.application.add_handler(CallbackQueryHandler(self.enhanced_callback_handler))
        
        # Web app data handler
        self.application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, self.mini_app.handle_webapp_data))
        
        logger.info("All handlers registered successfully")
    
    async def enhanced_search_command(self, update, context):
        """Enhanced search command with analytics tracking"""
        user_id = update.effective_user.id
        query = ' '.join(context.args) if context.args else None
        
        # Track search action
        self.analytics.track_user_action(user_id, 'search', {'query': query})
        
        # Call original search handler
        await self.bot_handlers.search_command(update, context)
    
    async def enhanced_callback_handler(self, update, context):
        """Enhanced callback handler with analytics tracking"""
        query = update.callback_query
        user_id = query.from_user.id
        data = query.data
        
        # Track button clicks
        if data.startswith("product_"):
            product_id = int(data.replace("product_", ""))
            self.analytics.track_click(user_id, product_id, 'product_view')
        elif data.startswith("category_"):
            category = data.replace("category_", "")
            self.analytics.track_user_action(user_id, 'category_browse', {'category': category})
        else:
            self.analytics.track_user_action(user_id, 'button_click', {'button': data})
        
        # Call original callback handler
        await self.bot_handlers.button_callback(update, context)
    
    def start_background_services(self):
        """Start all background services"""
        logger.info("Starting background services...")
        
        # Start web app server with HTTPS tunnel
        try:
            webapp_thread = self.mini_app.start_webapp_server()
            if self.mini_app.webapp_url:
                logger.info(f"Web app running at: {self.mini_app.webapp_url}")
                
                # Save URL for external access
                with open('webapp_url.txt', 'w') as f:
                    f.write(self.mini_app.webapp_url)
            else:
                logger.warning("Web app running locally only (no HTTPS tunnel)")
        except Exception as e:
            logger.error(f"Failed to start web app: {e}")
        
        # Start background task manager
        try:
            self.background_tasks.start_all_tasks()
            logger.info("Background tasks started successfully")
        except Exception as e:
            logger.error(f"Failed to start background tasks: {e}")
        
        # Start notification scheduler
        try:
            self.notification_manager.start_scheduler()
            logger.info("Notification scheduler started")
        except Exception as e:
            logger.error(f"Failed to start notification scheduler: {e}")
        
        # Schedule auto group posting
        try:
            from telegram.ext import JobQueue
            job_queue = self.application.job_queue
            
            # Schedule daily auto deals posting at 9 AM
            job_queue.run_daily(
                self.group_manager.auto_post_deals,
                time=datetime.time(9, 0),  # 9:00 AM
                name="daily_group_deals"
            )
            
            # Schedule hourly deals for groups with hourly frequency
            job_queue.run_repeating(
                self.group_manager.auto_post_deals,
                interval=3600,  # 1 hour
                name="hourly_group_deals"
            )
            
            logger.info("Group auto-posting scheduler started")
        except Exception as e:
            logger.error(f"Failed to start group scheduler: {e}")
        
        # Start health server for Render
        try:
            threading.Thread(target=self.start_health_server, daemon=True).start()
            logger.info("Health server started for Render")
        except Exception as e:
            logger.error(f"Failed to start health server: {e}")
    
    def start_health_server(self):
        """Start health check server for Render"""
        app = Flask(__name__)
        
        @app.route('/health')
        def health():
            return {"status": "healthy", "service": "telegram-affiliate-bot"}, 200
        
        @app.route('/')
        def home():
            return {"message": "Telegram Affiliate Bot is running!", "status": "active"}, 200
        
        # Run on the port Render provides
        port = int(os.environ.get('PORT', 10000))
        app.run(host='0.0.0.0', port=port, debug=False)
    
    def get_system_status(self):
        """Get comprehensive system status"""
        try:
            # Database stats
            session = self.db.get_session()
            from database import Product, User, Category, Store
            
            db_stats = {
                'products': session.query(Product).count(),
                'active_products': session.query(Product).filter_by(is_active=True).count(),
                'daily_deals': session.query(Product).filter_by(is_daily_deal=True).count(),
                'users': session.query(User).count(),
                'categories': session.query(Category).count(),
                'stores': session.query(Store).count()
            }
            session.close()
            
            # Analytics stats
            analytics_stats = self.analytics.get_global_stats()
            
            # Price monitor stats
            monitor_stats = self.background_tasks.price_monitor.get_monitoring_stats()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'database': db_stats,
                'analytics': analytics_stats,
                'monitoring': monitor_stats,
                'webapp_url': self.mini_app.webapp_url,
                'services': {
                    'webapp': bool(self.mini_app.webapp_url),
                    'price_monitor': self.background_tasks.price_monitor.running,
                    'notifications': True  # Assume running if no errors
                }
            }
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}
    
    async def send_startup_notification(self):
        """Send startup notification to admin"""
        try:
            admin_id = Config.TELEGRAM_ADMIN_ID
            if admin_id:
                status = self.get_system_status()
                
                message = "🚀 **Affiliate Bot Started Successfully!**\n\n"
                message += f"📊 **Database:**\n"
                message += f"• Products: {status['database']['products']} ({status['database']['active_products']} active)\n"
                message += f"• Daily Deals: {status['database']['daily_deals']}\n"
                message += f"• Users: {status['database']['users']}\n"
                message += f"• Categories: {status['database']['categories']}\n"
                message += f"• Stores: {status['database']['stores']}\n\n"
                
                message += f"🔧 **Services:**\n"
                message += f"• Web App: {'✅' if status['services']['webapp'] else '❌'}\n"
                message += f"• Price Monitor: {'✅' if status['services']['price_monitor'] else '❌'}\n"
                message += f"• Notifications: {'✅' if status['services']['notifications'] else '❌'}\n\n"
                
                if status['webapp_url']:
                    message += f"🌐 **Web App URL:** {status['webapp_url']}\n\n"
                
                message += f"⏰ **Started at:** {status['timestamp']}\n"
                message += f"🤖 **Bot is ready to serve users!**"
                
                await self.application.bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode='Markdown'
                )
                logger.info("Startup notification sent to admin")
        except Exception as e:
            logger.error(f"Failed to send startup notification: {e}")
    
    async def run(self):
        """Run the integrated bot"""
        logger.info("Starting Integrated Affiliate Bot...")
        
        # Setup handlers
        self.setup_handlers()
        
        # Start background services
        self.start_background_services()
        
        # Initialize and start the bot
        await self.application.initialize()
        await self.application.start()
        
        # Send startup notification
        await self.send_startup_notification()
        
        logger.info("🤖 Integrated Affiliate Bot is running!")
        logger.info("📱 Users can now interact with the bot")
        logger.info("🛍️ All features are active and ready")
        logger.info("Press Ctrl+C to stop the bot")
        
        # Start polling
        await self.application.updater.start_polling()
        
        try:
            # Keep the bot running
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Shutting down bot...")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Gracefully shutdown the bot"""
        logger.info("Shutting down Integrated Affiliate Bot...")
        
        # Stop background tasks
        self.background_tasks.stop_all_tasks()
        
        # Stop the application
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
        
        logger.info("Bot shutdown complete")

def main():
    """Main function to run the integrated bot"""
    try:
        bot = IntegratedAffiliateBot()
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()
