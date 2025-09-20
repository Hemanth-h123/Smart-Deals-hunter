import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
import json
import re
import time
from urllib.parse import urljoin, urlparse
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

from database import DatabaseManager, Product, Store, Category
from affiliate_manager import AffiliateManager
from config import Config

logger = logging.getLogger(__name__)

@dataclass
class ScrapedProduct:
    title: str
    price: float
    original_price: Optional[float]
    description: str
    image_url: str
    product_url: str
    store_name: str
    category: str
    rating: Optional[float] = None
    review_count: int = 0
    discount_percentage: Optional[float] = None

class WebsiteScraper:
    def __init__(self):
        self.db = DatabaseManager()
        self.affiliate_manager = AffiliateManager()
        self.session = None
        self.headers = {
            'User-Agent': Config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def init_session(self):
        """Initialize aiohttp session"""
        if not self.session:
            connector = aiohttp.TCPConnector(limit=10)
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self.headers
            )
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def scrape_amazon_deals(self, max_products: int = 50) -> List[ScrapedProduct]:
        """Scrape Amazon deals and popular products"""
        products = []
        
        # Amazon deals URLs
        urls = [
            "https://www.amazon.com/gp/goldbox",  # Today's Deals
            "https://www.amazon.com/Best-Sellers/zgbs",  # Best Sellers
            "https://www.amazon.com/gp/new-releases",  # New Releases
        ]
        
        await self.init_session()
        
        for url in urls:
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract products from Amazon pages
                        page_products = self._extract_amazon_products(soup, url)
                        products.extend(page_products)
                        
                        if len(products) >= max_products:
                            break
                
                await asyncio.sleep(Config.REQUEST_DELAY)
                
            except Exception as e:
                logger.error(f"Error scraping Amazon URL {url}: {e}")
        
        return products[:max_products]
    
    def _extract_amazon_products(self, soup: BeautifulSoup, base_url: str) -> List[ScrapedProduct]:
        """Extract products from Amazon page"""
        products = []
        
        # Different selectors for different Amazon page types
        product_selectors = [
            '[data-testid="product-card"]',
            '.s-result-item',
            '.dealContainer',
            '.a-carousel-card',
            '.octopus-dlp-asin-section'
        ]
        
        for selector in product_selectors:
            items = soup.select(selector)
            if items:
                for item in items[:10]:  # Limit per selector
                    try:
                        product = self._parse_amazon_product(item, base_url)
                        if product:
                            products.append(product)
                    except Exception as e:
                        logger.debug(f"Error parsing Amazon product: {e}")
                break
        
        return products
    
    def _parse_amazon_product(self, item, base_url: str) -> Optional[ScrapedProduct]:
        """Parse individual Amazon product"""
        try:
            # Title
            title_selectors = ['h3 a span', '.s-title-instructions-style h3 a span', 'h2 a span', '.dealTitleTwoLine a']
            title = self._get_text_by_selectors(item, title_selectors)
            
            if not title or len(title) < 10:
                return None
            
            # Price
            price_selectors = ['.a-price-whole', '.a-offscreen', '.dealPriceText']
            price_text = self._get_text_by_selectors(item, price_selectors)
            price = self._extract_price(price_text) if price_text else None
            
            # Original price
            original_price_selectors = ['.a-text-price .a-offscreen', '.dealStrikeThroughPrice']
            original_price_text = self._get_text_by_selectors(item, original_price_selectors)
            original_price = self._extract_price(original_price_text) if original_price_text else None
            
            # Product URL
            link_selectors = ['h3 a', 'h2 a', '.dealTitleTwoLine a']
            relative_url = self._get_attribute_by_selectors(item, link_selectors, 'href')
            product_url = urljoin(base_url, relative_url) if relative_url else None
            
            if not product_url:
                return None
            
            # Image
            img_selectors = ['img.s-image', 'img[data-src]', '.dealImage img']
            image_url = self._get_attribute_by_selectors(item, img_selectors, 'src') or \
                       self._get_attribute_by_selectors(item, img_selectors, 'data-src')
            
            # Rating
            rating_selectors = ['.a-icon-alt']
            rating_text = self._get_text_by_selectors(item, rating_selectors)
            rating = self._extract_rating(rating_text) if rating_text else None
            
            # Category (basic categorization)
            category = self._categorize_product(title)
            
            # Calculate discount
            discount_percentage = None
            if price and original_price and original_price > price:
                discount_percentage = ((original_price - price) / original_price) * 100
            
            return ScrapedProduct(
                title=title[:255],  # Limit title length
                price=price or 0.0,
                original_price=original_price,
                description=title,  # Use title as description
                image_url=image_url or '',
                product_url=product_url,
                store_name='Amazon',
                category=category,
                rating=rating,
                discount_percentage=discount_percentage
            )
            
        except Exception as e:
            logger.debug(f"Error parsing Amazon product: {e}")
            return None
    
    async def scrape_ebay_deals(self, max_products: int = 30) -> List[ScrapedProduct]:
        """Scrape eBay deals"""
        products = []
        
        urls = [
            "https://www.ebay.com/sch/i.html?_nkw=&_sacat=0&_odkw=&_osacat=0&_dcat=0&rt=nc&LH_BIN=1&_udlo=&_udhi=&_samilow=&_samihi=&_sadis=15&_stpos=&_sargn=-1%26saslc%3D1&_salic=1&_sop=12&_dmd=1&_ipg=60",
        ]
        
        await self.init_session()
        
        for url in urls:
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        page_products = self._extract_ebay_products(soup, url)
                        products.extend(page_products)
                
                await asyncio.sleep(Config.REQUEST_DELAY)
                
            except Exception as e:
                logger.error(f"Error scraping eBay: {e}")
        
        return products[:max_products]
    
    def _extract_ebay_products(self, soup: BeautifulSoup, base_url: str) -> List[ScrapedProduct]:
        """Extract products from eBay page"""
        products = []
        items = soup.select('.s-item')
        
        for item in items[:20]:
            try:
                product = self._parse_ebay_product(item, base_url)
                if product:
                    products.append(product)
            except Exception as e:
                logger.debug(f"Error parsing eBay product: {e}")
        
        return products
    
    def _parse_ebay_product(self, item, base_url: str) -> Optional[ScrapedProduct]:
        """Parse individual eBay product"""
        try:
            # Title
            title_elem = item.select_one('.s-item__title')
            title = title_elem.get_text().strip() if title_elem else None
            
            if not title or 'shop on ebay' in title.lower():
                return None
            
            # Price
            price_elem = item.select_one('.s-item__price')
            price_text = price_elem.get_text().strip() if price_elem else None
            price = self._extract_price(price_text) if price_text else None
            
            # Product URL
            link_elem = item.select_one('.s-item__link')
            product_url = link_elem.get('href') if link_elem else None
            
            # Image
            img_elem = item.select_one('.s-item__image img')
            image_url = img_elem.get('src') if img_elem else None
            
            # Category
            category = self._categorize_product(title)
            
            if not all([title, price, product_url]):
                return None
            
            return ScrapedProduct(
                title=title[:255],
                price=price or 0.0,
                original_price=None,
                description=title,
                image_url=image_url or '',
                product_url=product_url,
                store_name='eBay',
                category=category
            )
            
        except Exception as e:
            logger.debug(f"Error parsing eBay product: {e}")
            return None
    
    def _get_text_by_selectors(self, element, selectors: List[str]) -> Optional[str]:
        """Get text using multiple selectors"""
        for selector in selectors:
            elem = element.select_one(selector)
            if elem:
                return elem.get_text().strip()
        return None
    
    def _get_attribute_by_selectors(self, element, selectors: List[str], attribute: str) -> Optional[str]:
        """Get attribute using multiple selectors"""
        for selector in selectors:
            elem = element.select_one(selector)
            if elem and elem.get(attribute):
                return elem.get(attribute)
        return None
    
    def _extract_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text"""
        if not price_text:
            return None
        
        # Remove currency symbols and extract number
        price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
        if price_match:
            try:
                return float(price_match.group())
            except ValueError:
                return None
        return None
    
    def _extract_rating(self, rating_text: str) -> Optional[float]:
        """Extract rating from text"""
        if not rating_text:
            return None
        
        rating_match = re.search(r'(\d+\.?\d*)', rating_text)
        if rating_match:
            try:
                rating = float(rating_match.group(1))
                return rating if 0 <= rating <= 5 else None
            except ValueError:
                return None
        return None
    
    def _categorize_product(self, title: str) -> str:
        """Automatically categorize product based on title"""
        title_lower = title.lower()
        
        # Electronics keywords
        electronics_keywords = ['phone', 'laptop', 'computer', 'tablet', 'headphone', 'speaker', 'tv', 'monitor', 'camera', 'gaming', 'console', 'iphone', 'samsung', 'apple', 'sony', 'lg']
        
        # Clothing keywords
        clothing_keywords = ['shirt', 'pants', 'dress', 'shoes', 'jacket', 'coat', 'jeans', 'sneakers', 'boots', 'hat', 'cap', 'sweater', 'hoodie', 'shorts']
        
        # Beauty keywords
        beauty_keywords = ['makeup', 'lipstick', 'foundation', 'mascara', 'skincare', 'cream', 'serum', 'perfume', 'cologne', 'beauty', 'cosmetic']
        
        # Kitchen keywords
        kitchen_keywords = ['kitchen', 'cooking', 'pot', 'pan', 'knife', 'blender', 'mixer', 'coffee', 'maker', 'cookware', 'utensil']
        
        # Household keywords
        household_keywords = ['vacuum', 'cleaning', 'furniture', 'home', 'decor', 'lamp', 'chair', 'table', 'bed', 'storage']
        
        # Check categories
        if any(keyword in title_lower for keyword in electronics_keywords):
            return 'electronics'
        elif any(keyword in title_lower for keyword in clothing_keywords):
            # Determine if men's or women's clothing
            if any(word in title_lower for word in ['men', 'mens', "men's", 'male', 'boy']):
                return 'mens_clothing'
            elif any(word in title_lower for word in ['women', 'womens', "women's", 'female', 'girl', 'ladies']):
                return 'womens_clothing'
            else:
                return 'mens_clothing'  # Default to men's
        elif any(keyword in title_lower for keyword in beauty_keywords):
            return 'beauty'
        elif any(keyword in title_lower for keyword in kitchen_keywords):
            return 'kitchen'
        elif any(keyword in title_lower for keyword in household_keywords):
            return 'household'
        else:
            return 'electronics'  # Default category

class AutomatedProductManager:
    def __init__(self):
        self.db = DatabaseManager()
        self.scraper = WebsiteScraper()
        self.affiliate_manager = AffiliateManager()
    
    async def run_automated_scraping(self):
        """Run automated product scraping from all websites"""
        logger.info("Starting automated product scraping...")
        
        try:
            # Scrape from different websites
            all_products = []
            
            # Amazon
            logger.info("Scraping Amazon...")
            amazon_products = await self.scraper.scrape_amazon_deals(50)
            all_products.extend(amazon_products)
            
            # eBay
            logger.info("Scraping eBay...")
            ebay_products = await self.scraper.scrape_ebay_deals(30)
            all_products.extend(ebay_products)
            
            # Process and save products
            await self._process_scraped_products(all_products)
            
            logger.info(f"Automated scraping completed. Processed {len(all_products)} products.")
            
        except Exception as e:
            logger.error(f"Error in automated scraping: {e}")
        finally:
            await self.scraper.close_session()
    
    async def _process_scraped_products(self, scraped_products: List[ScrapedProduct]):
        """Process and save scraped products to database"""
        session = self.db.get_session()
        added_count = 0
        
        for scraped_product in scraped_products:
            try:
                # Check if product already exists
                existing = session.query(Product).filter_by(
                    title=scraped_product.title
                ).first()
                
                if existing:
                    # Update price if different
                    if existing.price != scraped_product.price:
                        existing.price = scraped_product.price
                        existing.updated_at = datetime.utcnow()
                    continue
                
                # Get or create store
                store = session.query(Store).filter_by(name=scraped_product.store_name).first()
                if not store:
                    store = Store(name=scraped_product.store_name)
                    session.add(store)
                    session.flush()
                
                # Get category
                category = session.query(Category).filter_by(name=scraped_product.category).first()
                if not category:
                    # Use default category if not found
                    category = session.query(Category).filter_by(name='electronics').first()
                
                # Generate affiliate link
                affiliate_url = self.affiliate_manager.generate_affiliate_link(
                    scraped_product.product_url,
                    scraped_product.store_name,
                    scraped_product.title
                )
                
                # Create product
                product = Product(
                    title=scraped_product.title,
                    description=scraped_product.description,
                    price=scraped_product.price,
                    original_price=scraped_product.original_price,
                    discount_percentage=scraped_product.discount_percentage,
                    image_url=scraped_product.image_url,
                    product_url=scraped_product.product_url,
                    affiliate_url=affiliate_url,
                    category_id=category.id if category else None,
                    store_id=store.id,
                    rating=scraped_product.rating,
                    review_count=scraped_product.review_count,
                    is_daily_deal=scraped_product.discount_percentage and scraped_product.discount_percentage > 20,
                    is_active=True
                )
                
                session.add(product)
                added_count += 1
                
            except Exception as e:
                logger.error(f"Error processing product {scraped_product.title}: {e}")
        
        session.commit()
        logger.info(f"Added {added_count} new products to database")
    
    async def schedule_automated_scraping(self):
        """Schedule automated scraping to run periodically"""
        import schedule
        
        # Schedule scraping every 6 hours
        schedule.every(6).hours.do(lambda: asyncio.create_task(self.run_automated_scraping()))
        
        # Schedule daily deals update every day at 8 AM
        schedule.every().day.at("08:00").do(lambda: asyncio.create_task(self.run_automated_scraping()))
        
        logger.info("Automated scraping scheduled")
        
        while True:
            schedule.run_pending()
            await asyncio.sleep(60)  # Check every minute

# Admin command to trigger manual scraping
async def manual_scraping_command(update, context):
    """Admin command to trigger manual product scraping"""
    user_id = update.effective_user.id
    
    # Check if user is admin (you'll need to implement this check)
    from admin_panel import AdminPanel
    admin_panel = AdminPanel()
    
    if not admin_panel.is_admin(user_id):
        await update.message.reply_text("❌ Access denied. Admin privileges required.")
        return
    
    await update.message.reply_text("🔄 Starting automated product scraping from all websites...")
    
    try:
        manager = AutomatedProductManager()
        await manager.run_automated_scraping()
        
        await update.message.reply_text(
            "✅ **Automated Scraping Completed!**\n\n"
            "Products have been scraped from:\n"
            "• Amazon (deals & bestsellers)\n"
            "• eBay (popular items)\n"
            "• Auto-categorized by keywords\n"
            "• Affiliate links generated\n\n"
            "Use /admin to manage the new products!"
        )
        
    except Exception as e:
        logger.error(f"Manual scraping error: {e}")
        await update.message.reply_text(f"❌ Error during scraping: {str(e)}")
