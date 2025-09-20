#!/usr/bin/env python3
"""
Sample data population script for Affiliate Bot
Adds realistic product data to test bot functionality
"""

from database import DatabaseManager, Product, Category, Store
from datetime import datetime
import random

def populate_sample_data():
    """Populate database with sample products, categories, and stores"""
    db = DatabaseManager()
    session = db.get_session()
    
    # Sample stores data
    stores_data = [
        {"name": "Amazon", "website_url": "https://amazon.com", "affiliate_network": "Amazon Associates", "commission_rate": 4.0},
        {"name": "eBay", "website_url": "https://ebay.com", "affiliate_network": "eBay Partner Network", "commission_rate": 3.5},
        {"name": "AliExpress", "website_url": "https://aliexpress.com", "affiliate_network": "AliExpress Affiliate", "commission_rate": 5.0},
        {"name": "Best Buy", "website_url": "https://bestbuy.com", "affiliate_network": "Best Buy Affiliate", "commission_rate": 2.5},
        {"name": "Target", "website_url": "https://target.com", "affiliate_network": "Target Affiliate", "commission_rate": 3.0},
        {"name": "Walmart", "website_url": "https://walmart.com", "affiliate_network": "Walmart Affiliate", "commission_rate": 2.0},
        {"name": "Nike", "website_url": "https://nike.com", "affiliate_network": "Nike Affiliate", "commission_rate": 6.0},
        {"name": "Adidas", "website_url": "https://adidas.com", "affiliate_network": "Adidas Partner", "commission_rate": 5.5},
    ]
    
    # Sample categories data
    categories_data = [
        {"name": "electronics", "display_name": "Electronics", "emoji": "📱", "description": "Smartphones, laptops, gadgets"},
        {"name": "clothing", "display_name": "Clothing", "emoji": "👔", "description": "Fashion and apparel"},
        {"name": "beauty", "display_name": "Beauty", "emoji": "💄", "description": "Cosmetics and skincare"},
        {"name": "household", "display_name": "Household", "emoji": "🏠", "description": "Home and kitchen items"},
        {"name": "sports", "display_name": "Sports", "emoji": "⚽", "description": "Sports and fitness equipment"},
        {"name": "books", "display_name": "Books", "emoji": "📚", "description": "Books and educational materials"},
        {"name": "toys", "display_name": "Toys", "emoji": "🧸", "description": "Toys and games"},
        {"name": "automotive", "display_name": "Automotive", "emoji": "🚗", "description": "Car accessories and parts"},
    ]
    
    # Add stores if they don't exist
    for store_data in stores_data:
        existing_store = session.query(Store).filter_by(name=store_data["name"]).first()
        if not existing_store:
            store = Store(**store_data)
            session.add(store)
    
    # Add categories if they don't exist
    for cat_data in categories_data:
        existing_cat = session.query(Category).filter_by(name=cat_data["name"]).first()
        if not existing_cat:
            category = Category(**cat_data)
            session.add(category)
    
    session.commit()
    
    # Get all stores and categories for product creation
    stores = session.query(Store).all()
    categories = session.query(Category).all()
    
    # Sample products data
    products_data = [
        # Electronics
        {
            "title": "iPhone 15 Pro Max 256GB - Natural Titanium",
            "description": "Latest iPhone with A17 Pro chip, titanium design, and advanced camera system",
            "price": 1199.99,
            "original_price": 1299.99,
            "category": "electronics",
            "store": "Amazon",
            "image_url": "https://example.com/iphone15.jpg",
            "is_daily_deal": True
        },
        {
            "title": "Samsung Galaxy S24 Ultra 512GB",
            "description": "Premium Android smartphone with S Pen and AI features",
            "price": 1099.99,
            "original_price": 1199.99,
            "category": "electronics",
            "store": "Best Buy",
            "image_url": "https://example.com/galaxy-s24.jpg",
            "is_featured": True
        },
        {
            "title": "MacBook Air M3 15-inch 512GB",
            "description": "Ultra-thin laptop with M3 chip and all-day battery life",
            "price": 1699.99,
            "original_price": 1799.99,
            "category": "electronics",
            "store": "Amazon",
            "image_url": "https://example.com/macbook-air.jpg",
            "is_daily_deal": True
        },
        {
            "title": "Sony WH-1000XM5 Wireless Headphones",
            "description": "Industry-leading noise canceling headphones",
            "price": 299.99,
            "original_price": 399.99,
            "category": "electronics",
            "store": "Target",
            "image_url": "https://example.com/sony-headphones.jpg"
        },
        {
            "title": "iPad Pro 12.9-inch M2 WiFi 256GB",
            "description": "Professional tablet with M2 chip and Liquid Retina display",
            "price": 1099.99,
            "original_price": 1199.99,
            "category": "electronics",
            "store": "Amazon",
            "image_url": "https://example.com/ipad-pro.jpg"
        },
        
        # Clothing
        {
            "title": "Nike Air Force 1 '07 White Sneakers",
            "description": "Classic white leather sneakers for everyday wear",
            "price": 89.99,
            "original_price": 110.00,
            "category": "clothing",
            "store": "Nike",
            "image_url": "https://example.com/air-force-1.jpg",
            "is_daily_deal": True
        },
        {
            "title": "Adidas Ultraboost 23 Running Shoes",
            "description": "Premium running shoes with Boost midsole technology",
            "price": 179.99,
            "original_price": 190.00,
            "category": "clothing",
            "store": "Adidas",
            "image_url": "https://example.com/ultraboost.jpg"
        },
        {
            "title": "Levi's 501 Original Fit Jeans",
            "description": "Classic straight leg jeans in vintage wash",
            "price": 59.99,
            "original_price": 79.99,
            "category": "clothing",
            "store": "Target",
            "image_url": "https://example.com/levis-501.jpg"
        },
        {
            "title": "Champion Reverse Weave Hoodie",
            "description": "Premium cotton hoodie with iconic logo",
            "price": 49.99,
            "original_price": 65.00,
            "category": "clothing",
            "store": "Amazon",
            "image_url": "https://example.com/champion-hoodie.jpg"
        },
        
        # Beauty
        {
            "title": "Fenty Beauty Gloss Bomb Universal Lip Luminizer",
            "description": "High-shine lip gloss that flatters all skin tones",
            "price": 19.99,
            "original_price": 22.00,
            "category": "beauty",
            "store": "Target",
            "image_url": "https://example.com/fenty-gloss.jpg"
        },
        {
            "title": "The Ordinary Hyaluronic Acid 2% + B5",
            "description": "Hydrating serum for plump, smooth skin",
            "price": 8.99,
            "original_price": 12.00,
            "category": "beauty",
            "store": "Amazon",
            "image_url": "https://example.com/ordinary-serum.jpg",
            "is_daily_deal": True
        },
        {
            "title": "Rare Beauty Soft Pinch Liquid Blush",
            "description": "Long-lasting liquid blush with buildable coverage",
            "price": 22.99,
            "original_price": 25.00,
            "category": "beauty",
            "store": "Target",
            "image_url": "https://example.com/rare-beauty-blush.jpg"
        },
        
        # Household
        {
            "title": "Instant Pot Duo 7-in-1 Electric Pressure Cooker",
            "description": "Multi-functional kitchen appliance for quick cooking",
            "price": 79.99,
            "original_price": 119.99,
            "category": "household",
            "store": "Amazon",
            "image_url": "https://example.com/instant-pot.jpg",
            "is_daily_deal": True
        },
        {
            "title": "Dyson V15 Detect Cordless Vacuum",
            "description": "Powerful cordless vacuum with laser dust detection",
            "price": 649.99,
            "original_price": 749.99,
            "category": "household",
            "store": "Best Buy",
            "image_url": "https://example.com/dyson-v15.jpg"
        },
        {
            "title": "Ninja Foodi Personal Blender",
            "description": "Compact blender perfect for smoothies and shakes",
            "price": 39.99,
            "original_price": 59.99,
            "category": "household",
            "store": "Walmart",
            "image_url": "https://example.com/ninja-blender.jpg"
        },
        
        # Sports
        {
            "title": "Bowflex SelectTech 552 Adjustable Dumbbells",
            "description": "Space-saving dumbbells that adjust from 5 to 52.5 lbs",
            "price": 349.99,
            "original_price": 429.99,
            "category": "sports",
            "store": "Amazon",
            "image_url": "https://example.com/bowflex-dumbbells.jpg"
        },
        {
            "title": "Yoga Mat Premium 6mm Thick",
            "description": "Non-slip yoga mat with excellent cushioning",
            "price": 29.99,
            "original_price": 39.99,
            "category": "sports",
            "store": "Target",
            "image_url": "https://example.com/yoga-mat.jpg",
            "is_daily_deal": True
        },
        
        # Books
        {
            "title": "Atomic Habits by James Clear",
            "description": "Life-changing guide to building good habits",
            "price": 13.99,
            "original_price": 18.00,
            "category": "books",
            "store": "Amazon",
            "image_url": "https://example.com/atomic-habits.jpg"
        },
        {
            "title": "The 7 Habits of Highly Effective People",
            "description": "Classic self-improvement book by Stephen Covey",
            "price": 11.99,
            "original_price": 16.99,
            "category": "books",
            "store": "Target",
            "image_url": "https://example.com/7-habits.jpg"
        },
        
        # Toys
        {
            "title": "LEGO Creator 3-in-1 Deep Sea Creatures",
            "description": "Build a shark, squid, or angler fish with this set",
            "price": 15.99,
            "original_price": 19.99,
            "category": "toys",
            "store": "Target",
            "image_url": "https://example.com/lego-sea.jpg"
        },
        {
            "title": "Nintendo Switch OLED Console",
            "description": "Gaming console with vibrant OLED screen",
            "price": 349.99,
            "original_price": 399.99,
            "category": "toys",
            "store": "Best Buy",
            "image_url": "https://example.com/switch-oled.jpg",
            "is_featured": True
        }
    ]
    
    # Add products
    for product_data in products_data:
        # Find category and store
        category = next((c for c in categories if c.name == product_data["category"]), None)
        store = next((s for s in stores if s.name == product_data["store"]), None)
        
        if category and store:
            # Calculate discount percentage
            discount_pct = 0
            if product_data.get("original_price"):
                discount_pct = ((product_data["original_price"] - product_data["price"]) / product_data["original_price"]) * 100
            
            # Generate affiliate URL (mock)
            base_url = store.website_url or f"https://{store.name.lower()}.com"
            affiliate_url = f"https://affiliate.{base_url.replace('https://', '')}/product/{random.randint(100000, 999999)}"
            product_url = f"{base_url}/product/{random.randint(100000, 999999)}"
            
            product = Product(
                title=product_data["title"],
                description=product_data["description"],
                price=product_data["price"],
                original_price=product_data.get("original_price"),
                discount_percentage=discount_pct if discount_pct > 0 else None,
                image_url=product_data["image_url"],
                product_url=product_url,
                affiliate_url=affiliate_url,
                category_id=category.id,
                store_id=store.id,
                is_daily_deal=product_data.get("is_daily_deal", False),
                is_featured=product_data.get("is_featured", False),
                is_active=True,
                rating=round(random.uniform(3.5, 5.0), 1),
                review_count=random.randint(50, 5000),
                created_at=datetime.utcnow()
            )
            session.add(product)
    
    session.commit()
    session.close()
    
    print("Sample data populated successfully!")
    print("Database now contains:")
    
    # Print summary
    db = DatabaseManager()
    session = db.get_session()
    product_count = session.query(Product).count()
    category_count = session.query(Category).count()
    store_count = session.query(Store).count()
    daily_deals = session.query(Product).filter_by(is_daily_deal=True).count()
    
    print(f"   - {product_count} products")
    print(f"   - {category_count} categories")
    print(f"   - {store_count} stores")
    print(f"   - {daily_deals} daily deals")
    
    session.close()

if __name__ == "__main__":
    populate_sample_data()
