from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import Config

Base = declarative_base()

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    emoji = Column(String(10))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    products = relationship("Product", back_populates="category")

class Store(Base):
    __tablename__ = 'stores'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    website_url = Column(String(255))
    affiliate_network = Column(String(100))
    commission_rate = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    products = relationship("Product", back_populates="store")

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Float)
    original_price = Column(Float)
    discount_percentage = Column(Float)
    image_url = Column(String(500))
    product_url = Column(String(500), nullable=False)
    affiliate_url = Column(String(500), nullable=False)
    
    category_id = Column(Integer, ForeignKey('categories.id'))
    store_id = Column(Integer, ForeignKey('stores.id'))
    
    is_daily_deal = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    rating = Column(Float)
    review_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime)
    
    category = relationship("Category", back_populates="products")
    store = relationship("Store", back_populates="products")
    clicks = relationship("ClickTracking", back_populates="product")

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # User preferences
    preferred_categories = Column(Text)  # JSON string of category IDs
    max_price_filter = Column(Float)
    min_discount_filter = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    clicks = relationship("ClickTracking", back_populates="user")

class ClickTracking(Base):
    __tablename__ = 'click_tracking'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    clicked_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    user = relationship("User", back_populates="clicks")
    product = relationship("Product", back_populates="clicks")

class DatabaseManager:
    def __init__(self):
        self.engine = create_engine(Config.DATABASE_URL)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def add_default_categories(self):
        """Add default product categories"""
        for key, display_name in Config.CATEGORIES.items():
            emoji = display_name.split()[0] if display_name.split() else ''
            name_without_emoji = ' '.join(display_name.split()[1:]) if len(display_name.split()) > 1 else display_name
            
            existing = self.session.query(Category).filter_by(name=key).first()
            if not existing:
                category = Category(
                    name=key,
                    display_name=name_without_emoji,
                    emoji=emoji
                )
                self.session.add(category)
        
        self.session.commit()
    
    def add_default_stores(self):
        """Add default stores"""
        for store_name in Config.SUPPORTED_STORES:
            existing = self.session.query(Store).filter_by(name=store_name).first()
            if not existing:
                store = Store(name=store_name)
                self.session.add(store)
        
        self.session.commit()
    
    def get_session(self):
        return self.session
    
    def close(self):
        self.session.close()

# Initialize database
def init_database():
    db = DatabaseManager()
    db.add_default_categories()
    db.add_default_stores()
    return db
