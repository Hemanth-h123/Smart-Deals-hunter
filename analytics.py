#!/usr/bin/env python3
"""
User analytics and click tracking system
"""

import logging
from datetime import datetime, timedelta
from database import DatabaseManager, Product, User, ClickTracking
from sqlalchemy import func, and_, or_
import json

logger = logging.getLogger(__name__)

class AnalyticsManager:
    def __init__(self):
        self.db = DatabaseManager()
    
    def track_click(self, user_id, product_id, click_type='affiliate_link'):
        """Track user click on product"""
        session = self.db.get_session()
        
        try:
            click = ClickTracking(
                user_id=user_id,
                product_id=product_id,
                click_type=click_type,
                clicked_at=datetime.utcnow()
            )
            session.add(click)
            session.commit()
            
            logger.info(f"Tracked {click_type} click for user {user_id} on product {product_id}")
            
        except Exception as e:
            logger.error(f"Error tracking click: {e}")
            session.rollback()
        finally:
            session.close()
    
    def track_user_action(self, user_id, action, metadata=None):
        """Track general user actions"""
        session = self.db.get_session()
        
        try:
            # Store in click tracking with special action type
            click = ClickTracking(
                user_id=user_id,
                product_id=None,
                click_type=f"action_{action}",
                clicked_at=datetime.utcnow(),
                metadata=json.dumps(metadata) if metadata else None
            )
            session.add(click)
            session.commit()
            
            logger.debug(f"Tracked action '{action}' for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error tracking action: {e}")
            session.rollback()
        finally:
            session.close()
    
    def get_user_stats(self, user_id):
        """Get analytics for a specific user"""
        session = self.db.get_session()
        
        try:
            # Get user's click history
            total_clicks = session.query(ClickTracking).filter_by(user_id=user_id).count()
            
            # Clicks in last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_clicks = session.query(ClickTracking).filter(
                and_(
                    ClickTracking.user_id == user_id,
                    ClickTracking.clicked_at >= thirty_days_ago
                )
            ).count()
            
            # Most clicked categories
            category_clicks = session.query(
                Product.category_id,
                func.count(ClickTracking.id).label('click_count')
            ).join(
                ClickTracking, Product.id == ClickTracking.product_id
            ).filter(
                ClickTracking.user_id == user_id
            ).group_by(Product.category_id).order_by(
                func.count(ClickTracking.id).desc()
            ).limit(5).all()
            
            # Most clicked stores
            store_clicks = session.query(
                Product.store_id,
                func.count(ClickTracking.id).label('click_count')
            ).join(
                ClickTracking, Product.id == ClickTracking.product_id
            ).filter(
                ClickTracking.user_id == user_id
            ).group_by(Product.store_id).order_by(
                func.count(ClickTracking.id).desc()
            ).limit(5).all()
            
            return {
                'total_clicks': total_clicks,
                'recent_clicks': recent_clicks,
                'top_categories': category_clicks,
                'top_stores': store_clicks
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {}
        finally:
            session.close()
    
    def get_product_stats(self, product_id):
        """Get analytics for a specific product"""
        session = self.db.get_session()
        
        try:
            # Total clicks
            total_clicks = session.query(ClickTracking).filter_by(product_id=product_id).count()
            
            # Unique users who clicked
            unique_users = session.query(ClickTracking.user_id).filter_by(
                product_id=product_id
            ).distinct().count()
            
            # Clicks by type
            click_types = session.query(
                ClickTracking.click_type,
                func.count(ClickTracking.id).label('count')
            ).filter_by(product_id=product_id).group_by(
                ClickTracking.click_type
            ).all()
            
            # Recent activity (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_clicks = session.query(ClickTracking).filter(
                and_(
                    ClickTracking.product_id == product_id,
                    ClickTracking.clicked_at >= week_ago
                )
            ).count()
            
            return {
                'total_clicks': total_clicks,
                'unique_users': unique_users,
                'click_types': dict(click_types),
                'recent_clicks': recent_clicks
            }
            
        except Exception as e:
            logger.error(f"Error getting product stats: {e}")
            return {}
        finally:
            session.close()
    
    def get_global_stats(self):
        """Get global analytics"""
        session = self.db.get_session()
        
        try:
            # Total users
            total_users = session.query(User).count()
            
            # Active users (clicked in last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            active_users = session.query(ClickTracking.user_id).filter(
                ClickTracking.clicked_at >= thirty_days_ago
            ).distinct().count()
            
            # Total clicks
            total_clicks = session.query(ClickTracking).count()
            
            # Most popular products (by clicks)
            popular_products = session.query(
                Product.id,
                Product.title,
                func.count(ClickTracking.id).label('click_count')
            ).join(
                ClickTracking, Product.id == ClickTracking.product_id
            ).group_by(Product.id, Product.title).order_by(
                func.count(ClickTracking.id).desc()
            ).limit(10).all()
            
            # Most popular categories
            popular_categories = session.query(
                Product.category_id,
                func.count(ClickTracking.id).label('click_count')
            ).join(
                ClickTracking, Product.id == ClickTracking.product_id
            ).group_by(Product.category_id).order_by(
                func.count(ClickTracking.id).desc()
            ).limit(10).all()
            
            # Daily activity (last 7 days)
            daily_stats = []
            for i in range(7):
                day_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
                day_end = day_start + timedelta(days=1)
                
                day_clicks = session.query(ClickTracking).filter(
                    and_(
                        ClickTracking.clicked_at >= day_start,
                        ClickTracking.clicked_at < day_end
                    )
                ).count()
                
                daily_stats.append({
                    'date': day_start.strftime('%Y-%m-%d'),
                    'clicks': day_clicks
                })
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'total_clicks': total_clicks,
                'popular_products': popular_products,
                'popular_categories': popular_categories,
                'daily_activity': daily_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting global stats: {e}")
            return {}
        finally:
            session.close()
    
    def track_group_post(self, group_id: int, post_type: str, product_count: int):
        """Track group post analytics"""
        session = self.db.get_session()
        try:
            # Create a group action record
            action = UserAction(
                user_id=group_id,  # Use group_id as identifier
                action_type=f'group_{post_type}',
                details=f'Posted {product_count} products to group {group_id}',
                timestamp=datetime.now()
            )
            session.add(action)
            session.commit()
            logger.info(f"Tracked group post: {post_type} to group {group_id}")
        except Exception as e:
            logger.error(f"Error tracking group post: {e}")
            session.rollback()
        finally:
            session.close()
    
    def get_conversion_metrics(self):
        """Get conversion and engagement metrics"""
        session = self.db.get_session()
        
        try:
            # Click-through rates by category
            category_metrics = session.query(
                Product.category_id,
                func.count(ClickTracking.id).label('total_clicks'),
                func.count(func.distinct(ClickTracking.user_id)).label('unique_users')
            ).join(
                ClickTracking, Product.id == ClickTracking.product_id
            ).group_by(Product.category_id).all()
            
            # User engagement levels
            user_engagement = session.query(
                ClickTracking.user_id,
                func.count(ClickTracking.id).label('total_clicks'),
                func.max(ClickTracking.clicked_at).label('last_activity')
            ).group_by(ClickTracking.user_id).all()
            
            # Engagement categories
            engagement_levels = {
                'high': 0,    # 10+ clicks
                'medium': 0,  # 3-9 clicks
                'low': 0      # 1-2 clicks
            }
            
            for user_data in user_engagement:
                clicks = user_data.total_clicks
                if clicks >= 10:
                    engagement_levels['high'] += 1
                elif clicks >= 3:
                    engagement_levels['medium'] += 1
                else:
                    engagement_levels['low'] += 1
            
            return {
                'category_metrics': category_metrics,
                'engagement_levels': engagement_levels,
                'total_engaged_users': len(user_engagement)
            }
            
        except Exception as e:
            logger.error(f"Error getting conversion metrics: {e}")
            return {}
        finally:
            session.close()

class ClickTracker:
    """Enhanced click tracking with URL generation"""
    
    def __init__(self):
        self.analytics = AnalyticsManager()
    
    def generate_tracked_url(self, product_id, user_id, original_url, click_type='affiliate_link'):
        """Generate a tracked URL (in real implementation, would use URL shortener)"""
        # For now, return original URL and track click separately
        # In production, you'd create a redirect URL through your domain
        return original_url
    
    def track_and_redirect(self, product_id, user_id, click_type='affiliate_link'):
        """Track click and return redirect URL"""
        self.analytics.track_click(user_id, product_id, click_type)
        
        # In real implementation, this would redirect to the actual URL
        # For now, just return tracking confirmation
        return f"Click tracked for product {product_id}"

if __name__ == "__main__":
    # Test analytics
    logging.basicConfig(level=logging.INFO)
    
    analytics = AnalyticsManager()
    
    print("Testing analytics...")
    
    # Test tracking
    analytics.track_click(12345, 1, 'affiliate_link')
    analytics.track_user_action(12345, 'search', {'query': 'iPhone'})
    
    # Get stats
    global_stats = analytics.get_global_stats()
    print(f"Global stats: {global_stats}")
    
    user_stats = analytics.get_user_stats(12345)
    print(f"User stats: {user_stats}")
    
    print("Analytics test completed!")
