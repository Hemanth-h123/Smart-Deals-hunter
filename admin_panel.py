import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import DatabaseManager, Product, Category, Store, User
from affiliate_manager import ProductScraper
from datetime import datetime, timedelta
from config import Config

logger = logging.getLogger(__name__)

class AdminPanel:
    def __init__(self):
        self.db = DatabaseManager()
        self.scraper = ProductScraper()
    
    def is_admin(self, user_id):
        """Check if user is admin"""
        return user_id == Config.TELEGRAM_ADMIN_ID
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin command"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            return
        
        keyboard = [
            [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
            [InlineKeyboardButton("➕ Add Product", callback_data="admin_add_product"),
             InlineKeyboardButton("📝 Manage Products", callback_data="admin_manage_products")],
            [InlineKeyboardButton("🏪 Manage Stores", callback_data="admin_manage_stores"),
             InlineKeyboardButton("📂 Manage Categories", callback_data="admin_manage_categories")],
            [InlineKeyboardButton("👥 User Management", callback_data="admin_users"),
             InlineKeyboardButton("📈 Analytics", callback_data="admin_analytics")],
            [InlineKeyboardButton("🔄 Add Sample Data", callback_data="admin_sample_data")],
            [InlineKeyboardButton("🤖 Auto-Scrape Products", callback_data="admin_auto_scrape")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🛠️ **Admin Panel**\n\n"
            "Welcome to the admin dashboard. Choose an option:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_admin_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin panel callbacks"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if not self.is_admin(user_id):
            await query.answer("❌ Access denied")
            return
        
        await query.answer()
        data = query.data
        
        if data == "admin_main":
            await self.show_admin_main_menu(query, context)
        elif data == "admin_stats":
            await self.show_statistics(query, context)
        elif data == "admin_add_product":
            await self.show_add_product_form(query, context)
        elif data == "admin_manage_products":
            await self.show_manage_products(query, context)
        elif data == "admin_manage_stores":
            await self.show_manage_stores(query, context)
        elif data == "admin_manage_categories":
            await self.show_manage_categories(query, context)
        elif data == "admin_users":
            await self.show_user_management(query, context)
        elif data == "admin_analytics":
            await self.show_analytics(query, context)
        elif data == "admin_sample_data":
            await self.add_sample_data(query, context)
        elif data == "admin_auto_scrape":
            await self.start_auto_scraping(query, context)
        elif data.startswith("admin_delete_product_"):
            product_id = int(data.replace("admin_delete_product_", ""))
            await self.delete_product(query, context, product_id)
        elif data.startswith("admin_toggle_product_"):
            product_id = int(data.replace("admin_toggle_product_", ""))
            await self.toggle_product_status(query, context, product_id)
    
    async def show_admin_main_menu(self, query, context):
        """Show main admin menu"""
        keyboard = [
            [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
            [InlineKeyboardButton("➕ Add Product", callback_data="admin_add_product"),
             InlineKeyboardButton("📝 Manage Products", callback_data="admin_manage_products")],
            [InlineKeyboardButton("🏪 Manage Stores", callback_data="admin_manage_stores"),
             InlineKeyboardButton("📂 Manage Categories", callback_data="admin_manage_categories")],
            [InlineKeyboardButton("👥 User Management", callback_data="admin_users"),
             InlineKeyboardButton("📈 Analytics", callback_data="admin_analytics")],
            [InlineKeyboardButton("🔄 Add Sample Data", callback_data="admin_sample_data")],
            [InlineKeyboardButton("🤖 Auto-Scrape Products", callback_data="admin_auto_scrape")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🛠️ **Admin Panel**\n\n"
            "Welcome to the admin dashboard. Choose an option:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def show_statistics(self, query, context):
        """Show bot statistics"""
        session = self.db.get_session()
        
        total_products = session.query(Product).count()
        active_products = session.query(Product).filter_by(is_active=True).count()
        daily_deals = session.query(Product).filter_by(is_daily_deal=True, is_active=True).count()
        total_users = session.query(User).count()
        active_users = session.query(User).filter_by(is_active=True).count()
        total_categories = session.query(Category).count()
        total_stores = session.query(Store).count()
        
        # Recent activity (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        new_users_week = session.query(User).filter(User.created_at >= week_ago).count()
        new_products_week = session.query(Product).filter(Product.created_at >= week_ago).count()
        
        message = f"""
📊 **Bot Statistics**

**Products:**
• Total Products: {total_products}
• Active Products: {active_products}
• Daily Deals: {daily_deals}
• New This Week: {new_products_week}

**Users:**
• Total Users: {total_users}
• Active Users: {active_users}
• New This Week: {new_users_week}

**System:**
• Categories: {total_categories}
• Stores: {total_stores}

**Database Status:** ✅ Connected
**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="admin_stats")],
            [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_manage_products(self, query, context):
        """Show product management interface"""
        session = self.db.get_session()
        
        # Get recent products
        products = session.query(Product).order_by(Product.created_at.desc()).limit(10).all()
        
        if not products:
            keyboard = [
                [InlineKeyboardButton("➕ Add First Product", callback_data="admin_add_product")],
                [InlineKeyboardButton("🔙 Back", callback_data="admin_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "📝 **Product Management**\n\nNo products found. Add your first product!",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        message = "📝 **Product Management**\n\nRecent Products:\n\n"
        keyboard = []
        
        for i, product in enumerate(products, 1):
            status_emoji = "✅" if product.is_active else "❌"
            deal_emoji = "🔥" if product.is_daily_deal else ""
            
            message += f"{i}. {status_emoji} **{product.title[:40]}{'...' if len(product.title) > 40 else ''}**\n"
            message += f"   💰 ${product.price:.2f} | 🏪 {product.store.name if product.store else 'No Store'}{deal_emoji}\n\n"
            
            keyboard.append([
                InlineKeyboardButton(f"✏️ Edit {i}", callback_data=f"admin_edit_product_{product.id}"),
                InlineKeyboardButton(f"🔄 Toggle {i}", callback_data=f"admin_toggle_product_{product.id}"),
                InlineKeyboardButton(f"🗑️ Delete {i}", callback_data=f"admin_delete_product_{product.id}")
            ])
        
        keyboard.append([InlineKeyboardButton("➕ Add New Product", callback_data="admin_add_product")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_main")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_add_product_form(self, query, context):
        """Show add product form instructions"""
        message = """
➕ **Add New Product**

To add a product, send me a message in this format:

```
/addproduct
Title: Product Name Here
Price: 99.99
Original Price: 129.99 (optional)
Description: Product description here
Category: electronics (or other category name)
Store: Amazon (or other store name)
URL: https://example.com/product-link
Image: https://example.com/image.jpg (optional)
Daily Deal: yes/no (optional)
```

**Available Categories:**
• electronics, mens_clothing, womens_clothing
• beauty, household, kitchen, sports
• books, toys, automotive, health

**Example:**
```
/addproduct
Title: iPhone 15 Pro Max
Price: 1199.99
Original Price: 1299.99
Description: Latest iPhone with advanced features
Category: electronics
Store: Amazon
URL: https://amazon.com/dp/example
Daily Deal: yes
```
        """
        
        keyboard = [
            [InlineKeyboardButton("📝 View Sample Products", callback_data="admin_sample_data")],
            [InlineKeyboardButton("🔙 Back to Products", callback_data="admin_manage_products")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def add_sample_data(self, query, context):
        """Add sample data to database"""
        try:
            self.scraper.add_sample_products()
            
            keyboard = [
                [InlineKeyboardButton("📊 View Statistics", callback_data="admin_stats")],
                [InlineKeyboardButton("📝 Manage Products", callback_data="admin_manage_products")],
                [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_main")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "✅ **Sample Data Added Successfully!**\n\n"
                "Added sample products across all categories:\n"
                "• Electronics (iPhone, Samsung TV)\n"
                "• Clothing (Nike Sneakers)\n"
                "• Beauty (Fenty Foundation)\n"
                "• Household (Dyson Vacuum)\n"
                "• Kitchen (Instant Pot)\n\n"
                "You can now test the bot functionality!",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error adding sample data: {e}")
            await query.edit_message_text(
                f"❌ **Error Adding Sample Data**\n\n"
                f"Error: {str(e)}\n\n"
                "Please check the logs for more details.",
                parse_mode='Markdown'
            )
    
    async def show_user_management(self, query, context):
        """Show user management interface"""
        session = self.db.get_session()
        
        total_users = session.query(User).count()
        active_users = session.query(User).filter_by(is_active=True).count()
        recent_users = session.query(User).order_by(User.created_at.desc()).limit(5).all()
        
        message = f"""
👥 **User Management**

**Overview:**
• Total Users: {total_users}
• Active Users: {active_users}
• Inactive Users: {total_users - active_users}

**Recent Users:**
        """
        
        for i, user in enumerate(recent_users, 1):
            username = f"@{user.username}" if user.username else "No username"
            name = f"{user.first_name} {user.last_name or ''}".strip()
            status = "✅" if user.is_active else "❌"
            
            message += f"\n{i}. {status} **{name}** ({username})"
            message += f"\n   ID: {user.telegram_id} | Joined: {user.created_at.strftime('%Y-%m-%d')}"
        
        keyboard = [
            [InlineKeyboardButton("📊 User Analytics", callback_data="admin_user_analytics")],
            [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_analytics(self, query, context):
        """Show detailed analytics"""
        session = self.db.get_session()
        
        # Get click statistics
        from sqlalchemy import func
        click_stats = session.query(
            func.count().label('total_clicks')
        ).first()
        
        # Top categories by product count
        category_stats = session.query(
            Category.display_name,
            func.count(Product.id).label('product_count')
        ).join(Product).group_by(Category.id).order_by(func.count(Product.id).desc()).limit(5).all()
        
        # Top stores by product count
        store_stats = session.query(
            Store.name,
            func.count(Product.id).label('product_count')
        ).join(Product).group_by(Store.id).order_by(func.count(Product.id).desc()).limit(5).all()
        
        message = f"""
📈 **Analytics Dashboard**

**Click Statistics:**
• Total Clicks: {click_stats.total_clicks if click_stats else 0}

**Top Categories:**
        """
        
        for i, (category, count) in enumerate(category_stats, 1):
            message += f"\n{i}. {category}: {count} products"
        
        message += "\n\n**Top Stores:**"
        for i, (store, count) in enumerate(store_stats, 1):
            message += f"\n{i}. {store}: {count} products"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="admin_analytics")],
            [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def delete_product(self, query, context, product_id):
        """Delete a product"""
        session = self.db.get_session()
        product = session.query(Product).filter_by(id=product_id).first()
        
        if product:
            product_title = product.title
            session.delete(product)
            session.commit()
            
            await query.edit_message_text(
                f"✅ **Product Deleted**\n\n"
                f"Successfully deleted: **{product_title}**",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("❌ Product not found!")
    
    async def toggle_product_status(self, query, context, product_id):
        """Toggle product active status"""
        session = self.db.get_session()
        product = session.query(Product).filter_by(id=product_id).first()
        
        if product:
            product.is_active = not product.is_active
            session.commit()
            
            status = "activated" if product.is_active else "deactivated"
            await query.edit_message_text(
                f"✅ **Product {status.title()}**\n\n"
                f"**{product.title}** has been {status}.",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("❌ Product not found!")
    
    async def process_add_product_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process /addproduct command with product details"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            return
        
        text = update.message.text
        lines = text.split('\n')[1:]  # Skip the /addproduct line
        
        product_data = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                product_data[key.strip().lower()] = value.strip()
        
        # Validate required fields
        required_fields = ['title', 'price', 'category', 'store', 'url']
        missing_fields = [field for field in required_fields if field not in product_data]
        
        if missing_fields:
            await update.message.reply_text(
                f"❌ **Missing Required Fields:**\n\n"
                f"Please provide: {', '.join(missing_fields)}\n\n"
                f"Use /admin to see the correct format.",
                parse_mode='Markdown'
            )
            return
        
        try:
            # Add product to database
            session = self.db.get_session()
            
            # Get or create category
            category = session.query(Category).filter_by(name=product_data['category']).first()
            if not category:
                await update.message.reply_text(f"❌ Category '{product_data['category']}' not found!")
                return
            
            # Get or create store
            store = session.query(Store).filter_by(name=product_data['store']).first()
            if not store:
                store = Store(name=product_data['store'])
                session.add(store)
                session.commit()
            
            # Generate affiliate link
            from affiliate_manager import AffiliateManager
            affiliate_manager = AffiliateManager()
            affiliate_url = affiliate_manager.generate_affiliate_link(
                product_data['url'],
                product_data['store'],
                product_data['title']
            )
            
            # Create product
            product = Product(
                title=product_data['title'],
                description=product_data.get('description', ''),
                price=float(product_data['price']),
                original_price=float(product_data['original price']) if 'original price' in product_data else None,
                product_url=product_data['url'],
                affiliate_url=affiliate_url,
                image_url=product_data.get('image'),
                category_id=category.id,
                store_id=store.id,
                is_daily_deal=product_data.get('daily deal', '').lower() in ['yes', 'true', '1']
            )
            
            # Calculate discount if original price provided
            if product.original_price and product.price:
                product.discount_percentage = ((product.original_price - product.price) / product.original_price) * 100
            
            session.add(product)
            session.commit()
            
            await update.message.reply_text(
                f"✅ **Product Added Successfully!**\n\n"
                f"**Title:** {product.title}\n"
                f"**Price:** ${product.price:.2f}\n"
                f"**Category:** {category.display_name}\n"
                f"**Store:** {store.name}\n"
                f"**Daily Deal:** {'Yes' if product.is_daily_deal else 'No'}\n\n"
                f"Product is now available in the bot!",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error adding product: {e}")
            await update.message.reply_text(
                f"❌ **Error Adding Product**\n\n"
                f"Error: {str(e)}\n\n"
                f"Please check the format and try again.",
                parse_mode='Markdown'
            )
    
    async def start_auto_scraping(self, query, context):
        """Start automated product scraping"""
        await query.edit_message_text(
            "🤖 **Starting Automated Product Scraping**\n\n"
            "This will scrape products from:\n"
            "• Amazon (deals & bestsellers)\n"
            "• eBay (popular items)\n"
            "• Auto-categorize products\n"
            "• Generate affiliate links\n\n"
            "⏳ Please wait, this may take a few minutes...",
            parse_mode='Markdown'
        )
        
        try:
            from product_scraper import AutomatedProductManager
            manager = AutomatedProductManager()
            await manager.run_automated_scraping()
            
            keyboard = [
                [InlineKeyboardButton("📊 View Statistics", callback_data="admin_stats")],
                [InlineKeyboardButton("📝 Manage Products", callback_data="admin_manage_products")],
                [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_main")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "✅ **Automated Scraping Completed!**\n\n"
                "Successfully scraped products from multiple websites:\n"
                "• Amazon deals and bestsellers\n"
                "• eBay popular items\n"
                "• Auto-categorized by keywords\n"
                "• Affiliate links generated\n"
                "• Duplicate products filtered\n\n"
                "Products are now available in your bot!",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Auto-scraping error: {e}")
            keyboard = [
                [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"❌ **Error During Auto-Scraping**\n\n"
                f"Error: {str(e)}\n\n"
                "Please check the logs for more details.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
