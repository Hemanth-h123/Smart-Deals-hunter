import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from database import DatabaseManager, Product, Category, Store, User, ClickTracking
from affiliate_manager import AffiliateManager
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
import json

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class BotHandlers:
    def __init__(self, mini_app=None):
        self.db = DatabaseManager()
        self.affiliate_manager = AffiliateManager()
        self.mini_app = mini_app
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # Register user in database
        self.register_user(user)
        
        welcome_message = f"""
🛍️ **Welcome to Affiliate Deals Bot!** 🛍️

Hello {user.first_name}! I'm your personal shopping assistant that helps you find the best deals from stores worldwide.

🔥 **What I can do:**
• Show daily deals and discounts
• Browse products by categories
• Search for specific items
• Track the best prices
• Get notifications for new deals

📱 **Categories Available:**
{self.get_categories_text()}

**Quick Commands:**
/deals - View today's hot deals
/categories - Browse by category
/search - Search for products
/help - Get help

Ready to start shopping? Choose an option below! 👇
        """
        
        # Add daily deals preview to welcome message
        daily_deals_preview = self.get_daily_deals_preview()
        if daily_deals_preview:
            welcome_message += "\n\n🔥 **Today's Top Deals:**\n" + daily_deals_preview
        
        keyboard = []
        
        # Add mini app button if available
        if self.mini_app and self.mini_app.webapp_url:
            keyboard.append([InlineKeyboardButton("🛍️ Open Deals App", web_app=WebAppInfo(url=self.mini_app.webapp_url))])
        
        keyboard.extend([
            [InlineKeyboardButton("🔥 Daily Deals", callback_data="daily_deals")],
            [InlineKeyboardButton("📱 Electronics", callback_data="electronics"),
             InlineKeyboardButton("👔 Clothing", callback_data="clothing")],
            [InlineKeyboardButton("💄 Beauty", callback_data="beauty"),
             InlineKeyboardButton("🏠 Household", callback_data="household")],
            [InlineKeyboardButton("🔍 Search Products", callback_data="search")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🤖 **Affiliate Deals Bot Help**

**Commands:**
/start - Start the bot and see main menu
/deals - View today's hot deals
/categories - Browse products by category
/search <query> - Search for specific products
/settings - Manage your preferences
/help - Show this help message

**How to use:**
1️⃣ Browse categories or search for products
2️⃣ Click on products to see details
3️⃣ Use affiliate links to purchase and support us
4️⃣ Set preferences for personalized deals

**Categories:**
{self.get_categories_text()}

**Features:**
• Real-time price tracking
• Daily deal notifications
• Multi-store comparison
• Personalized recommendations
• Discount alerts

Need more help? Contact @YourSupportUsername
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def deals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /deals command - show daily deals"""
        session = self.db.get_session()
        
        # Get daily deals (products marked as daily deals or created today)
        today = datetime.now().date()
        daily_deals = session.query(Product).filter(
            or_(
                Product.is_daily_deal == True,
                Product.created_at >= today
            )
        ).filter(Product.is_active == True).limit(10).all()
        
        if not daily_deals:
            await update.message.reply_text("🔍 No daily deals available right now. Check back later!")
            return
        
        message = "🔥 **Today's Hot Deals** 🔥\n\n"
        keyboard = []
        
        for i, product in enumerate(daily_deals, 1):
            discount_text = f" (-{product.discount_percentage:.0f}%)" if product.discount_percentage else ""
            price_text = f"${product.price:.2f}" if product.price else "Price on request"
            
            message += f"{i}. **{product.title}**\n"
            message += f"💰 {price_text}{discount_text}\n"
            message += f"🏪 {product.store.name if product.store else 'Unknown Store'}\n\n"
            
            keyboard.append([InlineKeyboardButton(f"🛒 View Deal {i}", callback_data=f"product_{product.id}")])
        
        keyboard.append([InlineKeyboardButton("🔄 Refresh Deals", callback_data="daily_deals")])
        keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def categories_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /categories command"""
        await self.show_categories(update, context)
    
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /search command"""
        query = ' '.join(context.args) if context.args else None
        
        if not query:
            await update.message.reply_text(
                "🔍 **Search Products**\n\n"
                "Usage: `/search <product name>`\n\n"
                "Examples:\n"
                "• `/search iPhone 15`\n"
                "• `/search Nike shoes`\n"
                "• `/search laptop`\n"
                "• `/search skincare`\n\n"
                "Try searching for any product!",
                parse_mode='Markdown'
            )
            return
        
        await self.search_products(update, context, query)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "main_menu":
            await self.show_main_menu(query, context)
        elif data == "daily_deals":
            await self.show_daily_deals(query, context)
        elif data == "search":
            await self.show_search_interface(query, context)
        elif data == "settings":
            await self.show_settings(query, context)
        elif data.startswith("settings_"):
            await self.handle_settings_callback(query, context, data)
        elif data.startswith("category_"):
            category_name = data.replace("category_", "")
            await self.show_category_products(query, context, category_name)
        elif data.startswith("product_"):
            product_id = int(data.replace("product_", ""))
            await self.show_product_details(query, context, product_id)
        elif data == "clothing":
            await self.show_clothing_subcategories(query, context)
        else:
            await self.show_category_products(query, context, data)
    
    async def show_main_menu(self, query, context):
        """Show main menu"""
        keyboard = []
        
        # Add mini app button if available
        if self.mini_app and self.mini_app.webapp_url:
            keyboard.append([InlineKeyboardButton("🛍️ Open Deals App", web_app=WebAppInfo(url=self.mini_app.webapp_url))])
        
        keyboard.extend([
            [InlineKeyboardButton("🔥 Daily Deals", callback_data="daily_deals")],
            [InlineKeyboardButton("📱 Electronics", callback_data="electronics"),
             InlineKeyboardButton("👔 Clothing", callback_data="clothing")],
            [InlineKeyboardButton("💄 Beauty", callback_data="beauty"),
             InlineKeyboardButton("🏠 Household", callback_data="household")],
            [InlineKeyboardButton("🔍 Search Products", callback_data="search")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🛍️ **Affiliate Deals Bot - Main Menu**\n\n"
            "Choose a category to browse products or search for specific items:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def show_categories(self, update, context):
        """Show all categories"""
        session = self.db.get_session()
        categories = session.query(Category).all()
        
        keyboard = []
        for category in categories:
            button_text = f"{category.emoji} {category.display_name}" if category.emoji else category.display_name
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"category_{category.name}")])
        
        keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = "📂 **Product Categories**\n\nChoose a category to browse products:"
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_clothing_subcategories(self, query, context):
        """Show clothing subcategories"""
        keyboard = [
            [InlineKeyboardButton("👔 Men's Clothing", callback_data="category_mens_clothing")],
            [InlineKeyboardButton("👗 Women's Clothing", callback_data="category_womens_clothing")],
            [InlineKeyboardButton("👟 Shoes", callback_data="category_shoes")],
            [InlineKeyboardButton("👜 Accessories", callback_data="category_accessories")],
            [InlineKeyboardButton("🔙 Back to Categories", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "👕 **Clothing Categories**\n\nChoose a clothing category:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def show_daily_deals(self, query, context):
        """Show daily deals"""
        session = self.db.get_session()
        
        today = datetime.now().date()
        daily_deals = session.query(Product).filter(
            or_(
                Product.is_daily_deal == True,
                Product.created_at >= today
            )
        ).filter(Product.is_active == True).limit(8).all()
        
        if not daily_deals:
            await query.edit_message_text("🔍 No daily deals available right now. Check back later!")
            return
        
        message = "🔥 **Today's Hot Deals** 🔥\n\n"
        keyboard = []
        
        for i, product in enumerate(daily_deals, 1):
            discount_text = f" (-{product.discount_percentage:.0f}%)" if product.discount_percentage else ""
            price_text = f"${product.price:.2f}" if product.price else "Check Price"
            
            message += f"{i}. **{product.title[:50]}{'...' if len(product.title) > 50 else ''}**\n"
            message += f"💰 {price_text}{discount_text}\n"
            message += f"🏪 {product.store.name if product.store else 'Multiple Stores'}\n\n"
            
            keyboard.append([InlineKeyboardButton(f"🛒 View Deal {i}", callback_data=f"product_{product.id}")])
        
        keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data="daily_deals")])
        keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_category_products(self, query, context, category_name):
        """Show products in a specific category"""
        session = self.db.get_session()
        
        category = session.query(Category).filter_by(name=category_name).first()
        if not category:
            await query.edit_message_text("❌ Category not found!")
            return
        
        products = session.query(Product).filter(
            and_(Product.category_id == category.id, Product.is_active == True)
        ).limit(8).all()
        
        if not products:
            keyboard = [[InlineKeyboardButton("🔙 Back to Categories", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"🔍 No products found in **{category.display_name}** category.\n\n"
                "Products will be added soon!",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        message = f"{category.emoji} **{category.display_name}**\n\n"
        keyboard = []
        
        for i, product in enumerate(products, 1):
            price_text = f"${product.price:.2f}" if product.price else "Check Price"
            discount_text = f" (-{product.discount_percentage:.0f}%)" if product.discount_percentage else ""
            
            message += f"{i}. **{product.title[:45]}{'...' if len(product.title) > 45 else ''}**\n"
            message += f"💰 {price_text}{discount_text}\n"
            message += f"🏪 {product.store.name if product.store else 'Multiple Stores'}\n\n"
            
            keyboard.append([InlineKeyboardButton(f"🛒 View Product {i}", callback_data=f"product_{product.id}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Categories", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_product_details(self, query, context, product_id):
        """Show detailed product information"""
        session = self.db.get_session()
        product = session.query(Product).filter_by(id=product_id).first()
        
        if not product:
            await query.edit_message_text("❌ Product not found!")
            return
        
        # Track click
        user = query.from_user
        self.track_click(user.id, product_id)
        
        price_text = f"${product.price:.2f}" if product.price else "Check Price"
        original_price_text = f" ~~${product.original_price:.2f}~~" if product.original_price and product.original_price > product.price else ""
        discount_text = f"\n💥 **{product.discount_percentage:.0f}% OFF**" if product.discount_percentage else ""
        rating_text = f"\n⭐ {product.rating}/5 ({product.review_count} reviews)" if product.rating else ""
        
        message = f"🛒 **{product.title}**\n\n"
        
        if product.description:
            message += f"📝 {product.description[:200]}{'...' if len(product.description) > 200 else ''}\n\n"
        
        message += f"💰 **Price:** {price_text}{original_price_text}{discount_text}\n"
        message += f"🏪 **Store:** {product.store.name if product.store else 'Multiple Stores'}\n"
        message += f"📂 **Category:** {product.category.display_name if product.category else 'General'}{rating_text}\n"
        
        if product.expires_at:
            message += f"⏰ **Deal expires:** {product.expires_at.strftime('%Y-%m-%d %H:%M')}\n"
        
        keyboard = [
            [InlineKeyboardButton("🛒 Buy Now", url=product.affiliate_url)],
            [InlineKeyboardButton("🔗 View Original", url=product.product_url)],
            [InlineKeyboardButton("🔙 Back", callback_data=f"category_{product.category.name}" if product.category else "main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def search_products(self, update, context, query_text):
        """Search for products"""
        session = self.db.get_session()
        
        # Search in title and description
        products = session.query(Product).filter(
            and_(
                or_(
                    Product.title.ilike(f'%{query_text}%'),
                    Product.description.ilike(f'%{query_text}%')
                ),
                Product.is_active == True
            )
        ).limit(8).all()
        
        if not products:
            await update.message.reply_text(
                f"🔍 No products found for **'{query_text}'**\n\n"
                "Try searching with different keywords or browse our categories.",
                parse_mode='Markdown'
            )
            return
        
        message = f"🔍 **Search Results for '{query_text}'**\n\n"
        keyboard = []
        
        for i, product in enumerate(products, 1):
            price_text = f"${product.price:.2f}" if product.price else "Check Price"
            discount_text = f" (-{product.discount_percentage:.0f}%)" if product.discount_percentage else ""
            
            message += f"{i}. **{product.title[:45]}{'...' if len(product.title) > 45 else ''}**\n"
            message += f"💰 {price_text}{discount_text}\n"
            message += f"🏪 {product.store.name if product.store else 'Multiple Stores'}\n\n"
            
            keyboard.append([InlineKeyboardButton(f"🛒 View Product {i}", callback_data=f"product_{product.id}")])
        
        keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_search_interface(self, query, context):
        """Show search interface"""
        keyboard = [
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🔍 **Search Products**\n\n"
            "To search for products, use the command:\n"
            "`/search <product name>`\n\n"
            "**Examples:**\n"
            "• `/search iPhone`\n"
            "• `/search Nike shoes`\n"
            "• `/search laptop`\n"
            "• `/search skincare`\n\n"
            "I'll find the best deals matching your search!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def search_products(self, update, context, query_text):
        """Search for products based on query"""
        session = self.db.get_session()
        
        # Search in title and description
        search_results = session.query(Product).filter(
            and_(
                or_(
                    Product.title.ilike(f'%{query_text}%'),
                    Product.description.ilike(f'%{query_text}%')
                ),
                Product.is_active == True
            )
        ).limit(10).all()
        
        if not search_results:
            await update.message.reply_text(
                f"🔍 **Search Results for '{query_text}'**\n\n"
                "❌ No products found matching your search.\n\n"
                "**Try:**\n"
                "• Using different keywords\n"
                "• Checking spelling\n"
                "• Using broader terms\n\n"
                "Use `/search <product name>` to try again."
            )
            return
        
        message = f"🔍 **Search Results for '{query_text}'**\n\n"
        message += f"Found {len(search_results)} product(s):\n\n"
        
        keyboard = []
        
        for i, product in enumerate(search_results, 1):
            discount_text = f" (-{product.discount_percentage:.0f}%)" if product.discount_percentage else ""
            price_text = f"${product.price:.2f}" if product.price else "Check Price"
            
            message += f"{i}. **{product.title[:60]}{'...' if len(product.title) > 60 else ''}**\n"
            message += f"💰 {price_text}{discount_text}\n"
            message += f"🏪 {product.store.name if product.store else 'Multiple Stores'}\n"
            if product.rating:
                message += f"⭐ {product.rating}/5 ({product.review_count} reviews)\n"
            message += "\n"
            
            keyboard.append([InlineKeyboardButton(f"🛒 View Product {i}", callback_data=f"product_{product.id}")])
        
        keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        
        session.close()
    
    async def show_settings(self, query, context):
        """Show user settings"""
        keyboard = [
            [InlineKeyboardButton("🔔 Notifications", callback_data="settings_notifications")],
            [InlineKeyboardButton("💰 Price Alerts", callback_data="settings_price_alerts")],
            [InlineKeyboardButton("📂 Preferred Categories", callback_data="settings_categories")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "⚙️ **Settings**\n\n"
            "Manage your preferences and notifications:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_settings_callback(self, query, context, data):
        """Handle settings-related callbacks"""
        if data == "settings_notifications":
            await self.show_notification_settings(query, context)
        elif data == "settings_price_alerts":
            await self.show_price_alert_settings(query, context)
        elif data == "settings_categories":
            await self.show_category_preferences(query, context)
        elif data.startswith("toggle_category_"):
            category_name = data.replace("toggle_category_", "")
            await self.toggle_category_preference(query, context, category_name)
        elif data.startswith("toggle_notifications"):
            await self.toggle_notifications(query, context)
    
    async def show_notification_settings(self, query, context):
        """Show notification settings"""
        user_id = query.from_user.id
        session = self.db.get_session()
        user = session.query(User).filter_by(telegram_id=user_id).first()
        
        notifications_status = "✅ Enabled" if user and user.notifications_enabled else "❌ Disabled"
        
        keyboard = [
            [InlineKeyboardButton(f"🔔 Daily Deals: {notifications_status}", callback_data="toggle_notifications")],
            [InlineKeyboardButton("🔙 Back to Settings", callback_data="settings")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🔔 **Notification Settings**\n\n"
            f"Daily Deals Notifications: {notifications_status}\n\n"
            "Toggle notifications to receive daily deal alerts and price drop notifications.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        session.close()
    
    async def show_price_alert_settings(self, query, context):
        """Show price alert settings"""
        keyboard = [
            [InlineKeyboardButton("🔔 Set Price Alert", callback_data="create_price_alert")],
            [InlineKeyboardButton("📋 My Alerts", callback_data="view_price_alerts")],
            [InlineKeyboardButton("🔙 Back to Settings", callback_data="settings")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "💰 **Price Alert Settings**\n\n"
            "Get notified when products drop to your target price!\n\n"
            "**Features:**\n"
            "• Set custom price targets\n"
            "• Automatic price monitoring\n"
            "• Instant notifications\n\n"
            "*Note: Price alerts are currently in development*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def show_category_preferences(self, query, context):
        """Show category preferences"""
        user_id = query.from_user.id
        session = self.db.get_session()
        categories = session.query(Category).all()
        
        keyboard = []
        for category in categories[:8]:  # Show first 8 categories
            # For now, show all as enabled (can be enhanced with user preferences table)
            status = "✅"
            button_text = f"{status} {category.emoji} {category.display_name}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"toggle_category_{category.name}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Settings", callback_data="settings")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "📂 **Category Preferences**\n\n"
            "Select categories you're interested in to receive personalized deals:\n\n"
            "*Click to toggle categories on/off*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        session.close()
    
    async def toggle_notifications(self, query, context):
        """Toggle user notifications"""
        user_id = query.from_user.id
        session = self.db.get_session()
        user = session.query(User).filter_by(telegram_id=user_id).first()
        
        if user:
            user.notifications_enabled = not user.notifications_enabled
            session.commit()
            status = "enabled" if user.notifications_enabled else "disabled"
            await query.answer(f"Notifications {status}!")
        else:
            await query.answer("User not found!")
        
        session.close()
        await self.show_notification_settings(query, context)
    
    async def toggle_category_preference(self, query, context, category_name):
        """Toggle category preference"""
        # For now, just show a message (can be enhanced with preferences table)
        await query.answer(f"Category preference updated!")
        await self.show_category_preferences(query, context)
    
    def register_user(self, telegram_user):
        """Register or update user in database"""
        session = self.db.get_session()
        
        user = session.query(User).filter_by(telegram_id=telegram_user.id).first()
        
        if not user:
            user = User(
                telegram_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name
            )
            session.add(user)
        else:
            # Update user info
            user.username = telegram_user.username
            user.first_name = telegram_user.first_name
            user.last_name = telegram_user.last_name
            user.last_active = datetime.utcnow()
        
        session.commit()
    
    def track_click(self, telegram_user_id, product_id):
        """Track product click for analytics"""
        session = self.db.get_session()
        
        user = session.query(User).filter_by(telegram_id=telegram_user_id).first()
        if user:
            click = ClickTracking(
                user_id=user.id,
                product_id=product_id,
                clicked_at=datetime.utcnow()
            )
            session.add(click)
            session.commit()
    
    def get_categories_text(self):
        """Get formatted categories text"""
        session = self.db.get_session()
        categories = session.query(Category).all()
        
        text = ""
        for category in categories:
            emoji = category.emoji if category.emoji else "•"
            text += f"{emoji} {category.display_name}\n"
        
        return text
    
    def get_daily_deals_preview(self):
        """Get preview of top 3 daily deals for chat message"""
        session = self.db.get_session()
        
        today = datetime.now().date()
        daily_deals = session.query(Product).filter(
            or_(
                Product.is_daily_deal == True,
                Product.created_at >= today
            )
        ).filter(Product.is_active == True).order_by(Product.discount_percentage.desc()).limit(3).all()
        
        if not daily_deals:
            return ""
        
        preview_text = ""
        for i, product in enumerate(daily_deals, 1):
            discount_text = f" (-{product.discount_percentage:.0f}%)" if product.discount_percentage else ""
            price_text = f"${product.price:.2f}" if product.price else "Check Price"
            
            preview_text += f"{i}. **{product.title[:35]}{'...' if len(product.title) > 35 else ''}**\n"
            preview_text += f"   💰 {price_text}{discount_text} | 🏪 {product.store.name if product.store else 'Store'}\n"
        
        preview_text += "\n👆 *Tap 'Open Deals App' to see all deals!*"
        return preview_text
