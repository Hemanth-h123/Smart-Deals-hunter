import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_ADMIN_ID = int(os.getenv('TELEGRAM_ADMIN_ID', 0))
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///affiliate_bot.db')
    
    # Affiliate Network Configuration
    AMAZON_ACCESS_KEY = os.getenv('AMAZON_ACCESS_KEY')
    AMAZON_SECRET_KEY = os.getenv('AMAZON_SECRET_KEY')
    AMAZON_ASSOCIATE_TAG = os.getenv('AMAZON_ASSOCIATE_TAG')
    
    CLICKBANK_API_KEY = os.getenv('CLICKBANK_API_KEY')
    SHAREASALE_API_TOKEN = os.getenv('SHAREASALE_API_TOKEN')
    SHAREASALE_SECRET_KEY = os.getenv('SHAREASALE_SECRET_KEY')
    
    # Web Scraping Settings
    USER_AGENT = os.getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    REQUEST_DELAY = int(os.getenv('REQUEST_DELAY', 1))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Product Categories
    CATEGORIES = {
        'daily_deals': '🔥 Daily Deals',
        'electronics': '📱 Electronics',
        'mens_clothing': '👔 Men\'s Clothing',
        'womens_clothing': '👗 Women\'s Clothing',
        'beauty': '💄 Beauty Products',
        'household': '🏠 Household Items',
        'kitchen': '🍳 Kitchen Items',
        'sports': '⚽ Sports & Fitness',
        'books': '📚 Books',
        'toys': '🧸 Toys & Games',
        'automotive': '🚗 Automotive',
        'health': '💊 Health & Wellness'
    }
    
    # Supported Stores/Websites
    SUPPORTED_STORES = [
        'Amazon', 'eBay', 'AliExpress', 'Walmart', 'Target', 'Best Buy',
        'Nike', 'Adidas', 'Zara', 'H&M', 'Sephora', 'Ulta',
        'Home Depot', 'Lowe\'s', 'IKEA', 'Wayfair'
    ]
