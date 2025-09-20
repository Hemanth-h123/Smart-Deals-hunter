#!/usr/bin/env python3
"""
Price monitoring and automated product updates system
"""

import asyncio
import schedule
import time
import threading
import logging
from datetime import datetime, timedelta
from database import DatabaseManager, Product, Store, User
from affiliate_manager import AffiliateManager
from product_scraper import WebsiteScraper
from notifications import NotificationManager
import random

logger = logging.getLogger(__name__)

class PriceMonitor:
    def __init__(self):
        self.db = DatabaseManager()
        self.affiliate_manager = AffiliateManager()
        self.scraper = WebsiteScraper()
        self.notification_manager = NotificationManager()
        self.running = False
        
    def start_monitoring(self):
        """Start the price monitoring system"""
        logger.info("Starting price monitoring system...")
        
        # Schedule tasks
        schedule.every(30).minutes.do(self.update_product_prices)
        schedule.every(1).hours.do(self.check_price_alerts)
        schedule.every(6).hours.do(self.refresh_daily_deals)
        schedule.every(1).days.do(self.cleanup_old_data)
        
        self.running = True
        
        # Run scheduler in background thread
        monitor_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        monitor_thread.start()
        
        logger.info("Price monitoring system started")
        return monitor_thread
    
    def stop_monitoring(self):
        """Stop the price monitoring system"""
        self.running = False
        logger.info("Price monitoring system stopped")
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def update_product_prices(self):
        """Update prices for all active products"""
        logger.info("Starting product price update...")
        session = self.db.get_session()
        
        try:
            # Get active products that haven't been updated recently
            cutoff_time = datetime.utcnow() - timedelta(hours=2)
            products = session.query(Product).filter(
                Product.is_active == True,
                Product.updated_at < cutoff_time
            ).limit(50).all()  # Update 50 products at a time
            
            updated_count = 0
            price_drops = []
            
            for product in products:
                try:
                    # Simulate price update (in real implementation, scrape actual prices)
                    old_price = product.price
                    new_price = self._simulate_price_change(old_price)
                    
                    if new_price != old_price:
                        # Calculate new discount percentage
                        if product.original_price:
                            discount_pct = ((product.original_price - new_price) / product.original_price) * 100
                            product.discount_percentage = discount_pct if discount_pct > 0 else None
                        
                        product.price = new_price
                        product.updated_at = datetime.utcnow()
                        updated_count += 1
                        
                        # Check for significant price drops
                        if old_price and new_price < old_price * 0.9:  # 10% or more drop
                            price_drops.append({
                                'product': product,
                                'old_price': old_price,
                                'new_price': new_price,
                                'discount': ((old_price - new_price) / old_price) * 100
                            })
                        
                        logger.debug(f"Updated price for {product.title}: ${old_price:.2f} -> ${new_price:.2f}")
                
                except Exception as e:
                    logger.error(f"Error updating price for product {product.id}: {e}")
            
            session.commit()
            logger.info(f"Updated prices for {updated_count} products")
            
            # Send price drop notifications
            if price_drops:
                asyncio.create_task(self._notify_price_drops(price_drops))
                
        except Exception as e:
            logger.error(f"Error in price update: {e}")
            session.rollback()
        finally:
            session.close()
    
    def _simulate_price_change(self, current_price):
        """Simulate realistic price changes"""
        if not current_price:
            return current_price
            
        # 70% chance no change, 20% small change, 10% significant change
        change_type = random.choices(['none', 'small', 'big'], weights=[70, 20, 10])[0]
        
        if change_type == 'none':
            return current_price
        elif change_type == 'small':
            # ±5% change
            factor = random.uniform(0.95, 1.05)
        else:
            # ±15% change
            factor = random.uniform(0.85, 1.15)
        
        new_price = round(current_price * factor, 2)
        return max(new_price, 0.99)  # Minimum price $0.99
    
    async def _notify_price_drops(self, price_drops):
        """Send notifications for significant price drops"""
        for drop in price_drops:
            try:
                await self.notification_manager.send_price_drop_alert(
                    drop['product'],
                    drop['old_price'],
                    drop['new_price'],
                    drop['discount']
                )
            except Exception as e:
                logger.error(f"Error sending price drop notification: {e}")
    
    def check_price_alerts(self):
        """Check user price alerts and send notifications"""
        logger.info("Checking price alerts...")
        # This would check user-set price targets and notify when reached
        # Implementation depends on price alert data structure
        pass
    
    def refresh_daily_deals(self):
        """Refresh daily deals selection"""
        logger.info("Refreshing daily deals...")
        session = self.db.get_session()
        
        try:
            # Clear current daily deals
            session.query(Product).filter(Product.is_daily_deal == True).update({
                'is_daily_deal': False
            })
            
            # Select new daily deals based on criteria
            # 1. High discount percentage
            # 2. Good ratings
            # 3. Recent price drops
            candidates = session.query(Product).filter(
                Product.is_active == True,
                Product.discount_percentage >= 15,  # At least 15% off
                Product.rating >= 4.0  # Good ratings
            ).order_by(Product.discount_percentage.desc()).limit(20).all()
            
            # Select 8-12 random products from candidates
            num_deals = random.randint(8, 12)
            daily_deals = random.sample(candidates, min(num_deals, len(candidates)))
            
            for product in daily_deals:
                product.is_daily_deal = True
                product.updated_at = datetime.utcnow()
            
            session.commit()
            logger.info(f"Selected {len(daily_deals)} new daily deals")
            
        except Exception as e:
            logger.error(f"Error refreshing daily deals: {e}")
            session.rollback()
        finally:
            session.close()
    
    def cleanup_old_data(self):
        """Clean up old tracking data and logs"""
        logger.info("Cleaning up old data...")
        session = self.db.get_session()
        
        try:
            # Delete old click tracking data (older than 90 days)
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            from database import ClickTracking
            
            deleted_clicks = session.query(ClickTracking).filter(
                ClickTracking.clicked_at < cutoff_date
            ).delete()
            
            session.commit()
            logger.info(f"Cleaned up {deleted_clicks} old click tracking records")
            
        except Exception as e:
            logger.error(f"Error cleaning up data: {e}")
            session.rollback()
        finally:
            session.close()
    
    def get_monitoring_stats(self):
        """Get monitoring system statistics"""
        session = self.db.get_session()
        
        try:
            stats = {
                'total_products': session.query(Product).count(),
                'active_products': session.query(Product).filter(Product.is_active == True).count(),
                'daily_deals': session.query(Product).filter(Product.is_daily_deal == True).count(),
                'last_update': session.query(Product).filter(Product.updated_at.isnot(None)).order_by(Product.updated_at.desc()).first()
            }
            
            if stats['last_update']:
                stats['last_update'] = stats['last_update'].updated_at
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting monitoring stats: {e}")
            return {}
        finally:
            session.close()

# Background task runner
class BackgroundTaskManager:
    def __init__(self):
        self.price_monitor = PriceMonitor()
        self.tasks = []
    
    def start_all_tasks(self):
        """Start all background tasks"""
        logger.info("Starting background task manager...")
        
        # Start price monitoring
        monitor_thread = self.price_monitor.start_monitoring()
        self.tasks.append(monitor_thread)
        
        logger.info("All background tasks started")
        return self.tasks
    
    def stop_all_tasks(self):
        """Stop all background tasks"""
        logger.info("Stopping background tasks...")
        self.price_monitor.stop_monitoring()
        
        for task in self.tasks:
            if task.is_alive():
                task.join(timeout=5)
        
        logger.info("Background tasks stopped")

if __name__ == "__main__":
    # Test the price monitor
    logging.basicConfig(level=logging.INFO)
    
    monitor = PriceMonitor()
    
    # Run one-time updates for testing
    print("Testing price updates...")
    monitor.update_product_prices()
    
    print("Testing daily deals refresh...")
    monitor.refresh_daily_deals()
    
    print("Getting monitoring stats...")
    stats = monitor.get_monitoring_stats()
    print(f"Stats: {stats}")
