# 🚀 Telegram Affiliate Bot - Render Deployment Guide

## ✅ Fixed Issues
- **Removed aiohttp dependency** that was causing Python 3.13 build failures
- **Downgraded to Python 3.11** for better compatibility
- **All deployment files ready** for 24/7 cloud hosting

## 📋 Prerequisites
1. GitHub account
2. Render account (free tier available)
3. Telegram Bot Token from @BotFather
4. Your Telegram Admin User ID

## 🔧 Step-by-Step Deployment

### 1. Upload to GitHub
```bash
# Initialize git repository
git init
git add .
git commit -m "Initial commit - Telegram Affiliate Bot"

# Create GitHub repository and push
git remote add origin https://github.com/yourusername/telegram-affiliate-bot.git
git branch -M main
git push -u origin main
```

### 2. Deploy on Render
1. Go to [render.com](https://render.com) and sign up/login
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `telegram-affiliate-bot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python integrated_bot.py`

### 3. Set Environment Variables
In Render dashboard, add these environment variables:

**Required:**
- `TELEGRAM_BOT_TOKEN`: Your bot token from @BotFather
- `TELEGRAM_ADMIN_ID`: Your Telegram user ID (get from @userinfobot)

**Optional (for affiliate networks):**
- `AMAZON_ASSOCIATE_TAG`: Your Amazon Associates tag
- `EBAY_CAMPAIGN_ID`: Your eBay Partner Network campaign ID
- `ALIEXPRESS_TRACKING_ID`: Your AliExpress affiliate tracking ID
- `WALMART_PUBLISHER_ID`: Your Walmart affiliate publisher ID
- `TARGET_PUBLISHER_ID`: Your Target affiliate publisher ID
- `BESTBUY_PUBLISHER_ID`: Your Best Buy affiliate publisher ID

### 4. Deploy & Monitor
1. Click "Create Web Service"
2. Wait for deployment (5-10 minutes)
3. Check logs for any errors
4. Test your bot on Telegram

## 🎯 What's Included
- ✅ **24/7 Bot Operation** - No need to keep your computer on
- ✅ **Health Check Endpoint** - Automatic uptime monitoring
- ✅ **Group Management** - Share deals directly in Telegram groups
- ✅ **Mini App Integration** - Web interface accessible via bot
- ✅ **Analytics Tracking** - User interaction analytics
- ✅ **Price Monitoring** - Automated price updates
- ✅ **Notification System** - Daily deals and price alerts
- ✅ **Admin Panel** - Product management commands

## 🔍 Troubleshooting

### Bot Not Responding
1. Check Render logs for errors
2. Verify `TELEGRAM_BOT_TOKEN` is correct
3. Ensure bot is not running elsewhere

### Database Issues
- SQLite database is automatically created
- Database persists between deployments

### Performance
- Free tier includes 750 hours/month
- Bot will sleep after 15 minutes of inactivity
- Wakes up instantly when receiving messages

## 📱 Bot Commands
- `/start` - Welcome message and main menu
- `/deals` - View daily deals
- `/categories` - Browse product categories
- `/search` - Search for products
- `/help` - Get help

## 👨‍💼 Admin Commands (Admin only)
- `/admin` - Access admin panel
- `/add_product` - Add new product
- `/stats` - View bot statistics
- `/authorize_group` - Authorize group for deals
- `/post_deals` - Post deals to groups

## 🎉 Success!
Your Telegram Affiliate Bot is now running 24/7 on Render! Users can interact with it anytime, and it will automatically handle:
- Product recommendations
- Deal notifications
- Group management
- Analytics tracking
- Price monitoring

The bot will continue running even when your computer is off, providing continuous service to your users.
