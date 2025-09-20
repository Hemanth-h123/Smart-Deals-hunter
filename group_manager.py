"""
Group Manager for Telegram Affiliate Bot
Handles group functionality for sharing product links directly
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from telegram.constants import ChatType, ParseMode
from database import DatabaseManager, Product, Category, Store
from analytics import AnalyticsManager
import asyncio
import random

logger = logging.getLogger(__name__)

class GroupManager:
    def __init__(self, analytics_manager: AnalyticsManager = None):
        """Initialize Group Manager"""
        self.db = DatabaseManager()
        self.analytics = analytics_manager or AnalyticsManager()
        self.authorized_groups = set()  # Store authorized group IDs
        self.group_settings = {}  # Store group-specific settings
        
        logger.info("Group Manager initialized")
    
    def is_admin_or_creator(self, chat_member: ChatMember) -> bool:
        """Check if user is admin or creator of the group"""
        return chat_member.status in ['administrator', 'creator']
    
    async def authorize_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Authorize a group to receive product links"""
        chat = update.effective_chat
        user = update.effective_user
        
        if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
            await update.message.reply_text("❌ This command can only be used in groups!")
            return
        
        # Check if user is admin
        try:
            chat_member = await context.bot.get_chat_member(chat.id, user.id)
            if not self.is_admin_or_creator(chat_member):
                await update.message.reply_text("❌ Only group administrators can authorize this bot!")
                return
        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
            await update.message.reply_text("❌ Error checking permissions!")
            return
        
        # Authorize the group
        self.authorized_groups.add(chat.id)
        self.group_settings[chat.id] = {
            'name': chat.title,
            'authorized_by': user.id,
            'authorized_at': datetime.now(),
            'auto_deals': True,
            'categories': [],  # Empty means all categories
            'posting_frequency': 'daily'  # daily, hourly, manual
        }
        
        welcome_message = f"""✅ **Group Authorized Successfully!**

🛍️ **{chat.title}** is now authorized to receive affiliate product links!

**Available Commands:**
• `/deals` - Get today's hot deals
• `/category <name>` - Get products from specific category  
• `/random_deal` - Get a random deal
• `/group_settings` - Configure group preferences
• `/stop_deals` - Stop automatic deal posting

**Auto Features:**
• 🔥 Daily deals will be posted automatically
• 📱 Products from all categories included
• ⚙️ Use `/group_settings` to customize

Ready to start sharing amazing deals! 🚀"""

        await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)
        logger.info(f"Group {chat.id} ({chat.title}) authorized by user {user.id}")
    
    async def deauthorize_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Deauthorize a group"""
        chat = update.effective_chat
        user = update.effective_user
        
        if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
            await update.message.reply_text("❌ This command can only be used in groups!")
            return
        
        # Check if user is admin
        try:
            chat_member = await context.bot.get_chat_member(chat.id, user.id)
            if not self.is_admin_or_creator(chat_member):
                await update.message.reply_text("❌ Only group administrators can manage bot authorization!")
                return
        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
            return
        
        # Deauthorize the group
        if chat.id in self.authorized_groups:
            self.authorized_groups.remove(chat.id)
            if chat.id in self.group_settings:
                del self.group_settings[chat.id]
            
            await update.message.reply_text("✅ Group deauthorized. No more automatic deals will be posted.")
            logger.info(f"Group {chat.id} deauthorized by user {user.id}")
        else:
            await update.message.reply_text("❌ This group is not currently authorized.")
    
    async def post_deals_to_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Post current deals to the group"""
        chat = update.effective_chat
        
        if chat.id not in self.authorized_groups:
            await update.message.reply_text("❌ This group is not authorized. Use /authorize_group first!")
            return
        
        # Get daily deals
        session = self.db.get_session()
        try:
            # Get products with discounts (daily deals)
            deals = session.query(Product).filter(
                Product.discount_percentage > 0
            ).order_by(Product.discount_percentage.desc()).limit(5).all()
            
            if not deals:
                await update.message.reply_text("😔 No deals available right now. Check back later!")
                return
            
            deals_message = "🔥 **TODAY'S HOT DEALS** 🔥\n\n"
            
            for i, product in enumerate(deals, 1):
                original_price = product.price / (1 - product.discount_percentage / 100)
                savings = original_price - product.price
                
                deals_message += f"**{i}. {product.name}**\n"
                deals_message += f"💰 ~~${original_price:.2f}~~ **${product.price:.2f}**\n"
                deals_message += f"💸 Save ${savings:.2f} ({product.discount_percentage}% OFF)\n"
                deals_message += f"⭐ {product.rating}/5 ({product.reviews_count} reviews)\n"
                deals_message += f"🛒 [**GET DEAL**]({product.affiliate_url})\n"
                deals_message += f"🏪 {product.store.name}\n\n"
            
            deals_message += "💡 *Click 'GET DEAL' to purchase with our affiliate link*"
            
            await context.bot.send_message(
                chat_id=chat.id,
                text=deals_message,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            
            # Track analytics
            self.analytics.track_group_post(chat.id, 'deals', len(deals))
            
        except Exception as e:
            logger.error(f"Error posting deals to group {chat.id}: {e}")
            await update.message.reply_text("❌ Error fetching deals. Please try again later.")
        finally:
            session.close()
    
    async def post_category_products(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Post products from a specific category"""
        chat = update.effective_chat
        
        if chat.id not in self.authorized_groups:
            await update.message.reply_text("❌ This group is not authorized. Use /authorize_group first!")
            return
        
        # Get category name from command
        if not context.args:
            await update.message.reply_text("❌ Please specify a category. Example: `/category electronics`")
            return
        
        category_name = " ".join(context.args).lower()
        
        session = self.db.get_session()
        try:
            # Find category
            category = session.query(Category).filter(
                Category.name.ilike(f"%{category_name}%")
            ).first()
            
            if not category:
                await update.message.reply_text(f"❌ Category '{category_name}' not found!")
                return
            
            # Get products from category
            products = session.query(Product).filter(
                Product.category_id == category.id
            ).order_by(Product.rating.desc()).limit(3).all()
            
            if not products:
                await update.message.reply_text(f"😔 No products found in '{category.name}' category.")
                return
            
            category_message = f"📱 **{category.name.upper()} PRODUCTS** 📱\n\n"
            
            for i, product in enumerate(products, 1):
                discount_text = ""
                if product.discount_percentage > 0:
                    original_price = product.price / (1 - product.discount_percentage / 100)
                    discount_text = f" ~~${original_price:.2f}~~ ({product.discount_percentage}% OFF)"
                
                category_message += f"**{i}. {product.name}**\n"
                category_message += f"💰 ${product.price:.2f}{discount_text}\n"
                category_message += f"⭐ {product.rating}/5 ({product.reviews_count} reviews)\n"
                category_message += f"🛒 [**BUY NOW**]({product.affiliate_url})\n"
                category_message += f"🏪 {product.store.name}\n\n"
            
            category_message += "💡 *Click 'BUY NOW' to purchase with our affiliate link*"
            
            await context.bot.send_message(
                chat_id=chat.id,
                text=category_message,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            
            # Track analytics
            self.analytics.track_group_post(chat.id, 'category', len(products))
            
        except Exception as e:
            logger.error(f"Error posting category products to group {chat.id}: {e}")
            await update.message.reply_text("❌ Error fetching products. Please try again later.")
        finally:
            session.close()
    
    async def post_random_deal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Post a random deal to the group"""
        chat = update.effective_chat
        
        if chat.id not in self.authorized_groups:
            await update.message.reply_text("❌ This group is not authorized. Use /authorize_group first!")
            return
        
        session = self.db.get_session()
        try:
            # Get a random product with discount
            products = session.query(Product).filter(
                Product.discount_percentage > 0
            ).all()
            
            if not products:
                await update.message.reply_text("😔 No deals available right now!")
                return
            
            product = random.choice(products)
            original_price = product.price / (1 - product.discount_percentage / 100)
            savings = original_price - product.price
            
            deal_message = f"🎲 **RANDOM DEAL ALERT** 🎲\n\n"
            deal_message += f"**{product.name}**\n\n"
            deal_message += f"💰 ~~${original_price:.2f}~~ **${product.price:.2f}**\n"
            deal_message += f"💸 Save ${savings:.2f} ({product.discount_percentage}% OFF)\n"
            deal_message += f"⭐ {product.rating}/5 ({product.reviews_count} reviews)\n"
            deal_message += f"📱 Category: {product.category.name}\n"
            deal_message += f"🏪 Store: {product.store.name}\n\n"
            deal_message += f"🛒 [**GRAB THIS DEAL**]({product.affiliate_url})\n\n"
            deal_message += "⚡ *Limited time offer - Act fast!*"
            
            await context.bot.send_message(
                chat_id=chat.id,
                text=deal_message,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            
            # Track analytics
            self.analytics.track_group_post(chat.id, 'random_deal', 1)
            
        except Exception as e:
            logger.error(f"Error posting random deal to group {chat.id}: {e}")
            await update.message.reply_text("❌ Error fetching deal. Please try again later.")
        finally:
            session.close()
    
    async def show_group_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show and manage group settings"""
        chat = update.effective_chat
        user = update.effective_user
        
        if chat.id not in self.authorized_groups:
            await update.message.reply_text("❌ This group is not authorized. Use /authorize_group first!")
            return
        
        # Check if user is admin
        try:
            chat_member = await context.bot.get_chat_member(chat.id, user.id)
            if not self.is_admin_or_creator(chat_member):
                await update.message.reply_text("❌ Only group administrators can manage settings!")
                return
        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
            return
        
        settings = self.group_settings.get(chat.id, {})
        
        settings_message = f"⚙️ **GROUP SETTINGS** ⚙️\n\n"
        settings_message += f"📱 **Group:** {chat.title}\n"
        settings_message += f"🔄 **Auto Deals:** {'✅ Enabled' if settings.get('auto_deals', True) else '❌ Disabled'}\n"
        settings_message += f"⏰ **Frequency:** {settings.get('posting_frequency', 'daily').title()}\n"
        settings_message += f"📂 **Categories:** {'All' if not settings.get('categories') else ', '.join(settings.get('categories', []))}\n\n"
        
        settings_message += "**Available Commands:**\n"
        settings_message += "• `/toggle_auto_deals` - Enable/disable automatic posting\n"
        settings_message += "• `/set_frequency daily|hourly` - Set posting frequency\n"
        settings_message += "• `/set_categories electronics,clothing` - Set specific categories\n"
        settings_message += "• `/reset_categories` - Include all categories\n"
        
        await update.message.reply_text(settings_message, parse_mode=ParseMode.MARKDOWN)
    
    async def auto_post_deals(self, context: ContextTypes.DEFAULT_TYPE):
        """Automatically post deals to authorized groups"""
        for group_id in self.authorized_groups.copy():
            settings = self.group_settings.get(group_id, {})
            
            if not settings.get('auto_deals', True):
                continue
            
            try:
                session = self.db.get_session()
                
                # Get deals based on group preferences
                query = session.query(Product).filter(Product.discount_percentage > 0)
                
                if settings.get('categories'):
                    category_names = settings.get('categories')
                    categories = session.query(Category).filter(
                        Category.name.in_(category_names)
                    ).all()
                    category_ids = [cat.id for cat in categories]
                    query = query.filter(Product.category_id.in_(category_ids))
                
                deals = query.order_by(Product.discount_percentage.desc()).limit(3).all()
                
                if deals:
                    deals_message = "🔥 **AUTO DEALS UPDATE** 🔥\n\n"
                    
                    for i, product in enumerate(deals, 1):
                        original_price = product.price / (1 - product.discount_percentage / 100)
                        
                        deals_message += f"**{i}. {product.name}**\n"
                        deals_message += f"💰 ~~${original_price:.2f}~~ **${product.price:.2f}**\n"
                        deals_message += f"💸 {product.discount_percentage}% OFF\n"
                        deals_message += f"🛒 [**GET DEAL**]({product.affiliate_url})\n\n"
                    
                    deals_message += "⚡ *Limited time offers - Don't miss out!*"
                    
                    await context.bot.send_message(
                        chat_id=group_id,
                        text=deals_message,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True
                    )
                    
                    # Track analytics
                    self.analytics.track_group_post(group_id, 'auto_deals', len(deals))
                
                session.close()
                
            except Exception as e:
                logger.error(f"Error auto-posting to group {group_id}: {e}")
                # Remove group if bot was removed/blocked
                if "chat not found" in str(e).lower() or "bot was blocked" in str(e).lower():
                    self.authorized_groups.discard(group_id)
                    if group_id in self.group_settings:
                        del self.group_settings[group_id]
    
    def get_handlers(self):
        """Get all command handlers for groups"""
        return [
            CommandHandler("authorize_group", self.authorize_group),
            CommandHandler("deauthorize_group", self.deauthorize_group),
            CommandHandler("deals", self.post_deals_to_group),
            CommandHandler("category", self.post_category_products),
            CommandHandler("random_deal", self.post_random_deal),
            CommandHandler("group_settings", self.show_group_settings),
        ]
