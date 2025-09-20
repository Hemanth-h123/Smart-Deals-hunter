"""
Real Affiliate Link Generator for Multiple Networks
Handles Amazon Associates, eBay Partner Network, AliExpress, and other affiliate programs
"""

import requests
import hashlib
import hmac
import base64
import time
import json
import re
from urllib.parse import urlencode, quote, urlparse, parse_qs
from config import Config
from database import DatabaseManager, Product, Store
import logging

logger = logging.getLogger(__name__)

class RealAffiliateGenerator:
    def __init__(self):
        self.db = DatabaseManager()
        
    def generate_affiliate_link(self, product_url: str, store_name: str, product_id: str = None) -> str:
        """Generate real affiliate link based on store"""
        store_name = store_name.lower()
        
        try:
            if 'amazon' in store_name:
                return self.generate_amazon_link(product_url, product_id)
            elif 'ebay' in store_name:
                return self.generate_ebay_link(product_url, product_id)
            elif 'aliexpress' in store_name:
                return self.generate_aliexpress_link(product_url, product_id)
            elif 'walmart' in store_name:
                return self.generate_walmart_link(product_url, product_id)
            elif 'target' in store_name:
                return self.generate_target_link(product_url, product_id)
            elif 'bestbuy' in store_name or 'best buy' in store_name:
                return self.generate_bestbuy_link(product_url, product_id)
            else:
                return self.generate_generic_tracking_link(product_url, store_name)
                
        except Exception as e:
            logger.error(f"Error generating affiliate link for {store_name}: {e}")
            return product_url
    
    def generate_amazon_link(self, product_url: str, product_id: str = None) -> str:
        """Generate Amazon Associates affiliate link"""
        if not Config.AMAZON_ASSOCIATE_TAG:
            logger.warning("Amazon Associate Tag not configured")
            return product_url
        
        # Extract ASIN from URL
        asin = self.extract_amazon_asin(product_url) or product_id
        
        if asin:
            # Clean affiliate link format
            affiliate_url = f"https://www.amazon.com/dp/{asin}?tag={Config.AMAZON_ASSOCIATE_TAG}&linkCode=ogi&th=1&psc=1"
            logger.info(f"Generated Amazon affiliate link: {affiliate_url}")
            return affiliate_url
        else:
            # Add tag to existing URL
            separator = "&" if "?" in product_url else "?"
            return f"{product_url}{separator}tag={Config.AMAZON_ASSOCIATE_TAG}"
    
    def generate_ebay_link(self, product_url: str, product_id: str = None) -> str:
        """Generate eBay Partner Network affiliate link"""
        if not hasattr(Config, 'EBAY_CAMPAIGN_ID') or not Config.EBAY_CAMPAIGN_ID:
            logger.warning("eBay Campaign ID not configured")
            return product_url
        
        # eBay affiliate link format
        base_url = "https://rover.ebay.com/rover/1/711-53200-19255-0/1"
        params = {
            'icep_ff3': '2',
            'pub': Config.EBAY_CAMPAIGN_ID,
            'toolid': '10001',
            'campid': '5338452986',
            'customid': '',
            'icep_item': product_id or self.extract_ebay_item_id(product_url),
            'ipn': 'psmain',
            'icep_vectorid': '229466',
            'kwid': '902099',
            'mtid': '824',
            'kw': 'lg',
            'srcrot': '711-53200-19255-0',
            'rvr_id': '2348474186',
            'rvr_ts': str(int(time.time()))
        }
        
        affiliate_url = f"{base_url}?{urlencode(params)}&mpre={quote(product_url)}"
        return affiliate_url
    
    def generate_aliexpress_link(self, product_url: str, product_id: str = None) -> str:
        """Generate AliExpress affiliate link"""
        if not hasattr(Config, 'ALIEXPRESS_TRACKING_ID') or not Config.ALIEXPRESS_TRACKING_ID:
            logger.warning("AliExpress Tracking ID not configured")
            return product_url
        
        # AliExpress affiliate parameters
        separator = "&" if "?" in product_url else "?"
        affiliate_params = f"aff_trace_key={Config.ALIEXPRESS_TRACKING_ID}&terminal_id=d4c0d3b6c8a44e6b9c8f2e1a3b5d7f9e"
        
        return f"{product_url}{separator}{affiliate_params}"
    
    def generate_walmart_link(self, product_url: str, product_id: str = None) -> str:
        """Generate Walmart affiliate link"""
        if not hasattr(Config, 'WALMART_PUBLISHER_ID') or not Config.WALMART_PUBLISHER_ID:
            return product_url
        
        # Walmart Impact Radius affiliate link
        base_url = "https://goto.walmart.com/c/2003851/565706/9383"
        separator = "&" if "?" in product_url else "?"
        
        return f"{base_url}?veh=aff&sourceid={Config.WALMART_PUBLISHER_ID}&u={quote(product_url)}"
    
    def generate_target_link(self, product_url: str, product_id: str = None) -> str:
        """Generate Target affiliate link"""
        if not hasattr(Config, 'TARGET_PUBLISHER_ID') or not Config.TARGET_PUBLISHER_ID:
            return product_url
        
        # Target affiliate link via Impact Radius
        base_url = "https://goto.target.com/c/2003851/81938/2092"
        return f"{base_url}?veh=aff&sourceid={Config.TARGET_PUBLISHER_ID}&u={quote(product_url)}"
    
    def generate_bestbuy_link(self, product_url: str, product_id: str = None) -> str:
        """Generate Best Buy affiliate link"""
        if not hasattr(Config, 'BESTBUY_PUBLISHER_ID') or not Config.BESTBUY_PUBLISHER_ID:
            return product_url
        
        # Best Buy affiliate link
        base_url = "https://bestbuy.7tiv.net/c/2003851/633495/10014"
        return f"{base_url}?veh=aff&sourceid={Config.BESTBUY_PUBLISHER_ID}&u={quote(product_url)}"
    
    def generate_generic_tracking_link(self, product_url: str, store_name: str) -> str:
        """Generate generic tracking link with UTM parameters"""
        separator = "&" if "?" in product_url else "?"
        utm_params = {
            'utm_source': 'telegram_bot',
            'utm_medium': 'affiliate',
            'utm_campaign': 'deals_bot',
            'utm_content': store_name.lower().replace(' ', '_')
        }
        
        return f"{product_url}{separator}{urlencode(utm_params)}"
    
    def extract_amazon_asin(self, url: str) -> str:
        """Extract ASIN from Amazon URL"""
        patterns = [
            r'/dp/([A-Z0-9]{10})',
            r'/gp/product/([A-Z0-9]{10})',
            r'/product/([A-Z0-9]{10})',
            r'asin=([A-Z0-9]{10})',
            r'/([A-Z0-9]{10})(?:[/?]|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def extract_ebay_item_id(self, url: str) -> str:
        """Extract item ID from eBay URL"""
        patterns = [
            r'/itm/([0-9]+)',
            r'item=([0-9]+)',
            r'/([0-9]{12,})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def update_product_affiliate_links(self, product_id: int = None):
        """Update affiliate links for products in database"""
        session = self.db.get_session()
        try:
            if product_id:
                products = session.query(Product).filter(Product.id == product_id).all()
            else:
                products = session.query(Product).all()
            
            updated_count = 0
            for product in products:
                if product.original_url and product.store:
                    new_affiliate_url = self.generate_affiliate_link(
                        product.original_url, 
                        product.store.name,
                        str(product.id)
                    )
                    
                    if new_affiliate_url != product.affiliate_url:
                        product.affiliate_url = new_affiliate_url
                        updated_count += 1
            
            session.commit()
            logger.info(f"Updated affiliate links for {updated_count} products")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error updating affiliate links: {e}")
            session.rollback()
            return 0
        finally:
            session.close()

class AffiliateNetworkIntegration:
    """Integration with major affiliate networks APIs"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def search_amazon_products(self, keywords: str, category: str = None) -> list:
        """Search Amazon products using Product Advertising API"""
        if not all([Config.AMAZON_ACCESS_KEY, Config.AMAZON_SECRET_KEY, Config.AMAZON_ASSOCIATE_TAG]):
            logger.warning("Amazon API credentials not configured")
            return []
        
        try:
            # Amazon Product Advertising API 5.0 implementation
            # This requires proper AWS signature and request formatting
            endpoint = "https://webservices.amazon.com/paapi5/searchitems"
            
            # Simplified example - real implementation needs proper AWS signing
            headers = {
                'Content-Type': 'application/json; charset=utf-8',
                'X-Amz-Target': 'com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems'
            }
            
            payload = {
                "Keywords": keywords,
                "SearchIndex": category or "All",
                "ItemCount": 10,
                "PartnerTag": Config.AMAZON_ASSOCIATE_TAG,
                "PartnerType": "Associates",
                "Resources": [
                    "Images.Primary.Medium",
                    "ItemInfo.Title",
                    "ItemInfo.Features",
                    "Offers.Listings.Price"
                ]
            }
            
            # Note: This is a simplified example
            # Real implementation requires AWS4 signature
            logger.info(f"Would search Amazon for: {keywords}")
            return []
            
        except Exception as e:
            logger.error(f"Error searching Amazon products: {e}")
            return []
    
    def get_clickbank_products(self, category: str = None) -> list:
        """Get products from ClickBank"""
        if not Config.CLICKBANK_API_KEY:
            logger.warning("ClickBank API key not configured")
            return []
        
        try:
            url = "https://api.clickbank.com/rest/1.3/products"
            headers = {
                'Authorization': f'Bearer {Config.CLICKBANK_API_KEY}',
                'Accept': 'application/json'
            }
            
            params = {
                'category': category or 'all',
                'limit': 50
            }
            
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json().get('products', [])
            else:
                logger.error(f"ClickBank API error: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching ClickBank products: {e}")
            return []

# Usage examples and configuration guide
AFFILIATE_SETUP_GUIDE = """
# Affiliate Network Setup Guide

## 1. Amazon Associates
1. Sign up at: https://affiliate-program.amazon.com/
2. Get your Associate Tag (e.g., 'yourtag-20')
3. Add to .env: AMAZON_ASSOCIATE_TAG=yourtag-20

## 2. eBay Partner Network
1. Sign up at: https://partnernetwork.ebay.com/
2. Get Campaign ID from your account
3. Add to .env: EBAY_CAMPAIGN_ID=your_campaign_id

## 3. AliExpress Affiliate
1. Sign up at: https://portals.aliexpress.com/
2. Get Tracking ID from your dashboard
3. Add to .env: ALIEXPRESS_TRACKING_ID=your_tracking_id

## 4. Walmart Affiliate
1. Apply via Impact Radius: https://impact.com/
2. Get Publisher ID after approval
3. Add to .env: WALMART_PUBLISHER_ID=your_publisher_id

## 5. Target Affiliate
1. Apply via Impact Radius: https://impact.com/
2. Get Publisher ID after approval
3. Add to .env: TARGET_PUBLISHER_ID=your_publisher_id

## 6. Best Buy Affiliate
1. Apply via Commission Junction
2. Get Publisher ID after approval
3. Add to .env: BESTBUY_PUBLISHER_ID=your_publisher_id

## Example .env Configuration:
AMAZON_ASSOCIATE_TAG=yourbot-20
EBAY_CAMPAIGN_ID=5338452986
ALIEXPRESS_TRACKING_ID=your_tracking_id
WALMART_PUBLISHER_ID=your_publisher_id
TARGET_PUBLISHER_ID=your_publisher_id
BESTBUY_PUBLISHER_ID=your_publisher_id
"""
