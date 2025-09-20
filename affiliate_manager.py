import requests
import hashlib
import hmac
import base64
import time
import json
from urllib.parse import urlencode, quote
from config import Config
from database import DatabaseManager, Product, Store, Category
import logging

logger = logging.getLogger(__name__)

class AffiliateManager:
    def __init__(self):
        self.db = DatabaseManager()
    
    def generate_affiliate_link(self, product_url, store_name, product_title=""):
        """Generate affiliate link based on store"""
        store_name = store_name.lower()
        
        if 'amazon' in store_name:
            return self.generate_amazon_affiliate_link(product_url)
        elif 'ebay' in store_name:
            return self.generate_ebay_affiliate_link(product_url)
        elif 'aliexpress' in store_name:
            return self.generate_aliexpress_affiliate_link(product_url)
        else:
            # For other stores, add tracking parameters
            return self.add_tracking_parameters(product_url, store_name)
    
    def generate_amazon_affiliate_link(self, product_url):
        """Generate Amazon affiliate link"""
        if not Config.AMAZON_ASSOCIATE_TAG:
            return product_url
        
        # Extract ASIN from URL if possible
        asin = self.extract_amazon_asin(product_url)
        
        if asin:
            # Create clean affiliate link
            affiliate_url = f"https://www.amazon.com/dp/{asin}?tag={Config.AMAZON_ASSOCIATE_TAG}"
        else:
            # Add tag to existing URL
            separator = "&" if "?" in product_url else "?"
            affiliate_url = f"{product_url}{separator}tag={Config.AMAZON_ASSOCIATE_TAG}"
        
        return affiliate_url
    
    def generate_ebay_affiliate_link(self, product_url):
        """Generate eBay affiliate link"""
        # eBay Partner Network integration would go here
        # For now, return original URL with tracking
        return self.add_tracking_parameters(product_url, "ebay")
    
    def generate_aliexpress_affiliate_link(self, product_url):
        """Generate AliExpress affiliate link"""
        # AliExpress affiliate program integration would go here
        return self.add_tracking_parameters(product_url, "aliexpress")
    
    def add_tracking_parameters(self, url, store_name):
        """Add custom tracking parameters to URL"""
        separator = "&" if "?" in url else "?"
        tracking_id = f"affiliate_bot_{int(time.time())}"
        return f"{url}{separator}utm_source=affiliate_bot&utm_medium=telegram&utm_campaign={store_name}&ref={tracking_id}"
    
    def extract_amazon_asin(self, url):
        """Extract ASIN from Amazon URL"""
        import re
        
        # Common ASIN patterns in Amazon URLs
        patterns = [
            r'/dp/([A-Z0-9]{10})',
            r'/gp/product/([A-Z0-9]{10})',
            r'asin=([A-Z0-9]{10})',
            r'/([A-Z0-9]{10})(?:[/?]|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def validate_affiliate_link(self, url):
        """Validate that affiliate link is working"""
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            return response.status_code == 200
        except:
            return False

class ProductScraper:
    def __init__(self):
        self.db = DatabaseManager()
        self.affiliate_manager = AffiliateManager()
        self.headers = {
            'User-Agent': Config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    def scrape_amazon_product(self, product_url):
        """Scrape Amazon product details"""
        try:
            response = requests.get(product_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract product details
            title = self.extract_amazon_title(soup)
            price = self.extract_amazon_price(soup)
            image_url = self.extract_amazon_image(soup)
            rating = self.extract_amazon_rating(soup)
            
            return {
                'title': title,
                'price': price,
                'image_url': image_url,
                'rating': rating,
                'description': title  # Use title as description for now
            }
        
        except Exception as e:
            logger.error(f"Error scraping Amazon product: {e}")
            return None
    
    def extract_amazon_title(self, soup):
        """Extract product title from Amazon page"""
        selectors = [
            '#productTitle',
            '.product-title',
            'h1.a-size-large'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        return "Product Title Not Found"
    
    def extract_amazon_price(self, soup):
        """Extract price from Amazon page"""
        price_selectors = [
            '.a-price-whole',
            '.a-offscreen',
            '#price_inside_buybox',
            '.a-price .a-offscreen'
        ]
        
        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text().strip()
                # Extract numeric value
                import re
                price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                if price_match:
                    return float(price_match.group())
        
        return None
    
    def extract_amazon_image(self, soup):
        """Extract main product image from Amazon page"""
        img_selectors = [
            '#landingImage',
            '.a-dynamic-image',
            '#imgBlkFront'
        ]
        
        for selector in img_selectors:
            element = soup.select_one(selector)
            if element and element.get('src'):
                return element.get('src')
        
        return None
    
    def extract_amazon_rating(self, soup):
        """Extract product rating from Amazon page"""
        rating_selectors = [
            '.a-icon-alt',
            '[data-hook="average-star-rating"] .a-icon-alt'
        ]
        
        for selector in rating_selectors:
            element = soup.select_one(selector)
            if element:
                rating_text = element.get_text()
                import re
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    return float(rating_match.group(1))
        
        return None
    
    def add_sample_products(self):
        """Add sample products for testing"""
        session = self.db.get_session()
        
        # Get categories and stores
        electronics_cat = session.query(Category).filter_by(name='electronics').first()
        clothing_cat = session.query(Category).filter_by(name='mens_clothing').first()
        beauty_cat = session.query(Category).filter_by(name='beauty').first()
        household_cat = session.query(Category).filter_by(name='household').first()
        kitchen_cat = session.query(Category).filter_by(name='kitchen').first()
        
        amazon_store = session.query(Store).filter_by(name='Amazon').first()
        ebay_store = session.query(Store).filter_by(name='eBay').first()
        
        sample_products = [
            # Electronics
            {
                'title': 'Apple iPhone 15 Pro Max 256GB - Natural Titanium',
                'description': 'Latest iPhone with A17 Pro chip, titanium design, and advanced camera system',
                'price': 1199.99,
                'original_price': 1299.99,
                'discount_percentage': 7.7,
                'category': electronics_cat,
                'store': amazon_store,
                'product_url': 'https://www.amazon.com/dp/B0CHX1W1XY',
                'is_daily_deal': True,
                'rating': 4.5,
                'review_count': 1250
            },
            {
                'title': 'Samsung 65" QLED 4K Smart TV QN90C',
                'description': 'Premium QLED TV with Quantum HDR and smart features',
                'price': 1499.99,
                'original_price': 1799.99,
                'discount_percentage': 16.7,
                'category': electronics_cat,
                'store': amazon_store,
                'product_url': 'https://www.amazon.com/dp/B0BVX7D5P9',
                'is_featured': True,
                'rating': 4.3,
                'review_count': 890
            },
            # Clothing
            {
                'title': 'Nike Air Max 270 Men\'s Sneakers',
                'description': 'Comfortable running shoes with Air Max technology',
                'price': 89.99,
                'original_price': 130.00,
                'discount_percentage': 30.8,
                'category': clothing_cat,
                'store': amazon_store,
                'product_url': 'https://www.amazon.com/dp/B07KZQM7ZH',
                'is_daily_deal': True,
                'rating': 4.4,
                'review_count': 2100
            },
            # Beauty
            {
                'title': 'Fenty Beauty Pro Filt\'r Foundation',
                'description': 'Long-wear foundation with medium to full coverage',
                'price': 38.00,
                'original_price': 42.00,
                'discount_percentage': 9.5,
                'category': beauty_cat,
                'store': amazon_store,
                'product_url': 'https://www.amazon.com/dp/B075FCQC8V',
                'rating': 4.2,
                'review_count': 3500
            },
            # Household
            {
                'title': 'Dyson V15 Detect Cordless Vacuum',
                'description': 'Advanced cordless vacuum with laser detection',
                'price': 649.99,
                'original_price': 749.99,
                'discount_percentage': 13.3,
                'category': household_cat,
                'store': amazon_store,
                'product_url': 'https://www.amazon.com/dp/B08TBZQZPX',
                'is_featured': True,
                'rating': 4.6,
                'review_count': 1800
            },
            # Kitchen
            {
                'title': 'Instant Pot Duo 7-in-1 Electric Pressure Cooker',
                'description': 'Multi-functional pressure cooker for quick meals',
                'price': 79.99,
                'original_price': 99.99,
                'discount_percentage': 20.0,
                'category': kitchen_cat,
                'store': amazon_store,
                'product_url': 'https://www.amazon.com/dp/B00FLYWNYQ',
                'is_daily_deal': True,
                'rating': 4.7,
                'review_count': 45000
            }
        ]
        
        for product_data in sample_products:
            # Generate affiliate link
            affiliate_url = self.affiliate_manager.generate_affiliate_link(
                product_data['product_url'],
                product_data['store'].name,
                product_data['title']
            )
            
            # Check if product already exists
            existing = session.query(Product).filter_by(
                title=product_data['title']
            ).first()
            
            if not existing:
                product = Product(
                    title=product_data['title'],
                    description=product_data['description'],
                    price=product_data['price'],
                    original_price=product_data.get('original_price'),
                    discount_percentage=product_data.get('discount_percentage'),
                    product_url=product_data['product_url'],
                    affiliate_url=affiliate_url,
                    category_id=product_data['category'].id if product_data['category'] else None,
                    store_id=product_data['store'].id if product_data['store'] else None,
                    is_daily_deal=product_data.get('is_daily_deal', False),
                    is_featured=product_data.get('is_featured', False),
                    rating=product_data.get('rating'),
                    review_count=product_data.get('review_count', 0)
                )
                session.add(product)
        
        session.commit()
        logger.info("Sample products added successfully")

# API Integration Classes
class AmazonAPI:
    def __init__(self):
        self.access_key = Config.AMAZON_ACCESS_KEY
        self.secret_key = Config.AMAZON_SECRET_KEY
        self.associate_tag = Config.AMAZON_ASSOCIATE_TAG
    
    def search_products(self, keywords, category=None):
        """Search Amazon products using Product Advertising API"""
        # This would integrate with Amazon Product Advertising API
        # For now, return empty list
        return []

class ClickBankAPI:
    def __init__(self):
        self.api_key = Config.CLICKBANK_API_KEY
    
    def get_products(self, category=None):
        """Get ClickBank products"""
        # This would integrate with ClickBank API
        return []

class ShareASaleAPI:
    def __init__(self):
        self.api_token = Config.SHAREASALE_API_TOKEN
        self.secret_key = Config.SHAREASALE_SECRET_KEY
    
    def get_products(self, merchant_id=None):
        """Get ShareASale products"""
        # This would integrate with ShareASale API
        return []
