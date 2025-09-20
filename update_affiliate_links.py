"""
Script to update existing products with real affiliate links
Run this after configuring your affiliate network credentials
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from affiliate_link_generator import RealAffiliateGenerator
from database import DatabaseManager, Product, Store
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_all_affiliate_links():
    """Update all products with real affiliate links"""
    generator = RealAffiliateGenerator()
    db = DatabaseManager()
    
    session = db.get_session()
    try:
        products = session.query(Product).all()
        updated_count = 0
        
        print(f"Found {len(products)} products to update...")
        
        for product in products:
            if product.store and product.original_url:
                print(f"Updating: {product.name} from {product.store.name}")
                
                # Generate real affiliate link
                new_affiliate_url = generator.generate_affiliate_link(
                    product.original_url,
                    product.store.name,
                    str(product.id)
                )
                
                # Update if different
                if new_affiliate_url != product.affiliate_url:
                    old_url = product.affiliate_url
                    product.affiliate_url = new_affiliate_url
                    updated_count += 1
                    
                    print(f"  ✅ Updated affiliate link")
                    print(f"  Old: {old_url[:80]}...")
                    print(f"  New: {new_affiliate_url[:80]}...")
                else:
                    print(f"  ⏭️  No change needed")
        
        session.commit()
        print(f"\n🎉 Successfully updated {updated_count} affiliate links!")
        
        return updated_count
        
    except Exception as e:
        logger.error(f"Error updating affiliate links: {e}")
        session.rollback()
        return 0
    finally:
        session.close()

def add_sample_real_products():
    """Add some real products with proper affiliate links"""
    generator = RealAffiliateGenerator()
    db = DatabaseManager()
    
    # Sample real products with original URLs
    sample_products = [
        {
            'name': 'Apple iPhone 15 Pro',
            'original_url': 'https://www.amazon.com/dp/B0CHX1W1XY',
            'store_name': 'Amazon',
            'category': 'Electronics',
            'price': 999.99,
            'rating': 4.5,
            'reviews_count': 1250
        },
        {
            'name': 'Samsung Galaxy S24 Ultra',
            'original_url': 'https://www.amazon.com/dp/B0CMDRCZBZ',
            'store_name': 'Amazon', 
            'category': 'Electronics',
            'price': 1199.99,
            'rating': 4.4,
            'reviews_count': 890
        },
        {
            'name': 'Sony WH-1000XM5 Headphones',
            'original_url': 'https://www.amazon.com/dp/B09XS7JWHH',
            'store_name': 'Amazon',
            'category': 'Electronics', 
            'price': 349.99,
            'rating': 4.6,
            'reviews_count': 2100
        },
        {
            'name': 'Nike Air Max 270',
            'original_url': 'https://www.nike.com/t/air-max-270-mens-shoes-KkLcGR',
            'store_name': 'Nike',
            'category': 'Clothing',
            'price': 150.00,
            'rating': 4.3,
            'reviews_count': 567
        },
        {
            'name': 'MacBook Air M3',
            'original_url': 'https://www.amazon.com/dp/B0CX23V2ZK',
            'store_name': 'Amazon',
            'category': 'Electronics',
            'price': 1099.99,
            'rating': 4.7,
            'reviews_count': 445
        }
    ]
    
    session = db.get_session()
    try:
        from database import Category, Store
        
        added_count = 0
        for product_data in sample_products:
            # Get or create store
            store = session.query(Store).filter(Store.name == product_data['store_name']).first()
            if not store:
                store = Store(name=product_data['store_name'], website=f"https://{product_data['store_name'].lower()}.com")
                session.add(store)
                session.flush()
            
            # Get or create category
            category = session.query(Category).filter(Category.name == product_data['category']).first()
            if not category:
                category = Category(name=product_data['category'])
                session.add(category)
                session.flush()
            
            # Generate affiliate link
            affiliate_url = generator.generate_affiliate_link(
                product_data['original_url'],
                product_data['store_name']
            )
            
            # Create product
            product = Product(
                name=product_data['name'],
                price=product_data['price'],
                original_url=product_data['original_url'],
                affiliate_url=affiliate_url,
                rating=product_data['rating'],
                reviews_count=product_data['reviews_count'],
                discount_percentage=0,
                store_id=store.id,
                category_id=category.id
            )
            
            session.add(product)
            added_count += 1
            
            print(f"✅ Added: {product_data['name']}")
            print(f"   Affiliate URL: {affiliate_url[:80]}...")
        
        session.commit()
        print(f"\n🎉 Added {added_count} real products with affiliate links!")
        
    except Exception as e:
        logger.error(f"Error adding sample products: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    print("🔗 Affiliate Link Updater")
    print("=" * 50)
    
    choice = input("\nChoose an option:\n1. Update existing products\n2. Add sample real products\n3. Both\nEnter choice (1-3): ")
    
    if choice in ['1', '3']:
        print("\n📝 Updating existing products...")
        update_all_affiliate_links()
    
    if choice in ['2', '3']:
        print("\n➕ Adding sample real products...")
        add_sample_real_products()
    
    print("\n✅ Done! Your products now have real affiliate links.")
    print("💡 Make sure to configure your affiliate network credentials in .env file")
