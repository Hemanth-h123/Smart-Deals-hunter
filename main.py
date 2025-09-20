#!/usr/bin/env python3
"""
Telegram Affiliate Bot - Main Application
A comprehensive bot for managing affiliate links across multiple product categories
"""

import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import Config
from database import init_database
from bot_handlers import BotHandlers
from admin_panel import AdminPanel
from product_scraper import manual_scraping_command
from mini_app_integration import MiniAppIntegration

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
)
logger = logging.getLogger(__name__)

class AffiliateTelegramBot:
    def __init__(self):
        self.mini_app = MiniAppIntegration()
        self.bot_handlers = BotHandlers(mini_app=self.mini_app)
        self.admin_panel = AdminPanel()
        
        # Initialize database
        logger.info("Initializing database...")
        self.db = init_database()
        logger.info("Database initialized successfully")
        
        # Start web app server for mini app
        logger.info("Starting web app server...")
        self.mini_app.start_webapp_server()
        
        # Create application
        self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Register handlers
        self.register_handlers()
    
    def register_handlers(self):
        """Register all bot handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.bot_handlers.start_command))
        self.application.add_handler(CommandHandler("help", self.bot_handlers.help_command))
        self.application.add_handler(CommandHandler("deals", self.bot_handlers.deals_command))
        self.application.add_handler(CommandHandler("categories", self.bot_handlers.categories_command))
        self.application.add_handler(CommandHandler("search", self.bot_handlers.search_command))
        
        # Admin commands
        self.application.add_handler(CommandHandler("admin", self.admin_panel.admin_command))
        self.application.add_handler(CommandHandler("addproduct", self.admin_panel.process_add_product_command))
        self.application.add_handler(CommandHandler("scrapeproducts", manual_scraping_command))
        
        # Callback query handlers
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query))
        
        # Message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
        
        # Web App data handler
        self.application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, self.mini_app.handle_webapp_data))
        
        logger.info("All handlers registered successfully")
    
    async def handle_callback_query(self, update: Update, context):
        """Route callback queries to appropriate handlers"""
        query = update.callback_query
        data = query.data
        
        if data.startswith("admin_"):
            await self.admin_panel.handle_admin_callback(update, context)
        else:
            await self.bot_handlers.button_callback(update, context)
    
    async def handle_text_message(self, update: Update, context):
        """Handle text messages"""
        text = update.message.text.lower()
        
        # Handle search queries
        if any(keyword in text for keyword in ['search', 'find', 'looking for']):
            # Extract search query
            search_terms = text.replace('search', '').replace('find', '').replace('looking for', '').strip()
            if search_terms:
                await self.bot_handlers.search_products(update, context, search_terms)
                return
        
        # Handle category requests
        category_keywords = {
            'electronics': ['phone', 'laptop', 'tv', 'electronics', 'gadget'],
            'clothing': ['clothes', 'shirt', 'shoes', 'fashion', 'wear'],
            'beauty': ['makeup', 'beauty', 'cosmetics', 'skincare'],
            'household': ['home', 'furniture', 'household', 'cleaning'],
            'kitchen': ['kitchen', 'cooking', 'appliance', 'cookware'],
            'deals': ['deals', 'discount', 'sale', 'offer']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in text for keyword in keywords):
                if category == 'deals':
                    await self.bot_handlers.deals_command(update, context)
                else:
                    # Show category products
                    query_data = f"category_{category}"
                    # Create a mock callback query
                    from types import SimpleNamespace
                    mock_query = SimpleNamespace()
                    mock_query.data = query_data
                    mock_query.from_user = update.effective_user
                    mock_query.edit_message_text = update.message.reply_text
                    mock_query.answer = lambda: None
                    
                    await self.bot_handlers.show_category_products(mock_query, context, category)
                return
        
        # Default response for unrecognized messages
        await update.message.reply_text(
            "🤖 I didn't understand that. Here are some things you can try:\n\n"
            "• /deals - View daily deals\n"
            "• /search <product> - Search for products\n"
            "• /categories - Browse categories\n"
            "• /help - Get help\n\n"
            "Or just tell me what you're looking for! 😊"
        )
    
    async def error_handler(self, update: Update, context):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Sorry, something went wrong. Please try again later."
            )
    
    def run(self):
        """Start the bot"""
        logger.info("Starting Affiliate Telegram Bot...")
        
        # Add error handler
        self.application.add_error_handler(self.error_handler)
        
        # Start the bot
        try:
            logger.info("Bot is running! Press Ctrl+C to stop.")
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Error running bot: {e}")
        finally:
            # Cleanup
            if hasattr(self, 'db'):
                self.db.close()
            logger.info("Bot shutdown complete")

def main():
    """Main function"""
    # Check if bot token is configured
    if not Config.TELEGRAM_BOT_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found!")
        print("Please create a .env file with your bot token:")
        print("TELEGRAM_BOT_TOKEN=your_bot_token_here")
        print("TELEGRAM_ADMIN_ID=your_telegram_user_id")
        return
    
    # Create and run bot
    bot = AffiliateTelegramBot()
    bot.run()

if __name__ == "__main__":
    main()
