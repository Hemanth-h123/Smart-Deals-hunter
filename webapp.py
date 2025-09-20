from flask import Flask, render_template, jsonify, request
import json
from database import DatabaseManager, Product, Category, Store
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

class WebAppManager:
    def __init__(self):
        self.db = DatabaseManager()
    
    def get_daily_deals(self, limit=10):
        """Get daily deals for display"""
        session = self.db.get_session()
        
        today = datetime.now().date()
        deals = session.query(Product).filter(
            or_(
                Product.is_daily_deal == True,
                Product.created_at >= today
            )
        ).filter(Product.is_active == True).order_by(Product.discount_percentage.desc()).limit(limit).all()
        
        return [self._product_to_dict(product) for product in deals]
    
    def get_products_by_category(self, category_name=None, limit=50):
        """Get products by category"""
        session = self.db.get_session()
        
        query = session.query(Product).filter(Product.is_active == True)
        
        if category_name:
            category = session.query(Category).filter_by(name=category_name).first()
            if category:
                query = query.filter(Product.category_id == category.id)
        
        products = query.order_by(Product.created_at.desc()).limit(limit).all()
        return [self._product_to_dict(product) for product in products]
    
    def get_categories(self):
        """Get all categories"""
        session = self.db.get_session()
        categories = session.query(Category).all()
        
        return [{
            'id': cat.id,
            'name': cat.name,
            'display_name': cat.display_name,
            'emoji': cat.emoji or '📦'
        } for cat in categories]
    
    def search_products(self, query_text, limit=30):
        """Search products"""
        session = self.db.get_session()
        
        products = session.query(Product).filter(
            and_(
                or_(
                    Product.title.ilike(f'%{query_text}%'),
                    Product.description.ilike(f'%{query_text}%')
                ),
                Product.is_active == True
            )
        ).limit(limit).all()
        
        return [self._product_to_dict(product) for product in products]
    
    def _product_to_dict(self, product):
        """Convert product to dictionary"""
        return {
            'id': product.id,
            'title': product.title,
            'description': product.description or '',
            'price': float(product.price) if product.price else 0,
            'original_price': float(product.original_price) if product.original_price else None,
            'discount_percentage': float(product.discount_percentage) if product.discount_percentage else None,
            'image_url': product.image_url or '',
            'affiliate_url': product.affiliate_url,
            'product_url': product.product_url,
            'store_name': product.store.name if product.store else 'Unknown',
            'category_name': product.category.display_name if product.category else 'General',
            'category_emoji': product.category.emoji if product.category else '📦',
            'rating': float(product.rating) if product.rating else None,
            'review_count': product.review_count or 0,
            'is_daily_deal': product.is_daily_deal,
            'created_at': product.created_at.isoformat() if product.created_at else None
        }

webapp_manager = WebAppManager()

@app.route('/')
def index():
    """Main mini app page"""
    return render_template('index.html')

@app.route('/api/daily-deals')
def api_daily_deals():
    """API endpoint for daily deals"""
    limit = request.args.get('limit', 10, type=int)
    deals = webapp_manager.get_daily_deals(limit)
    return jsonify(deals)

@app.route('/api/categories')
def api_categories():
    """API endpoint for categories"""
    categories = webapp_manager.get_categories()
    return jsonify(categories)

@app.route('/api/products')
def api_products():
    """API endpoint for products"""
    category = request.args.get('category')
    limit = request.args.get('limit', 50, type=int)
    products = webapp_manager.get_products_by_category(category, limit)
    return jsonify(products)

@app.route('/api/search')
def api_search():
    """API endpoint for search"""
    query = request.args.get('q', '')
    limit = request.args.get('limit', 30, type=int)
    
    if not query:
        return jsonify([])
    
    products = webapp_manager.search_products(query, limit)
    return jsonify(products)

@app.route('/deals')
def deals_page():
    """Deals page for mini app"""
    return render_template('deals.html')

@app.route('/categories')
def categories_page():
    """Categories page for mini app"""
    return render_template('categories.html')

@app.route('/search')
def search_page():
    """Search page for mini app"""
    return render_template('search.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
