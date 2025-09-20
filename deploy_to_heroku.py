"""
Heroku Deployment Script for Telegram Affiliate Bot
Deploy your bot to run 24/7 in the cloud
"""

import os
import subprocess
import sys

def create_heroku_files():
    """Create necessary files for Heroku deployment"""
    
    # Create Procfile
    with open('Procfile', 'w') as f:
        f.write('web: python integrated_bot.py\n')
    
    # Create runtime.txt
    with open('runtime.txt', 'w') as f:
        f.write('python-3.12.0\n')
    
    # Create app.json for Heroku deployment
    app_json = {
        "name": "telegram-affiliate-bot",
        "description": "Professional Telegram Affiliate Marketing Bot",
        "keywords": ["telegram", "bot", "affiliate", "marketing"],
        "website": "https://github.com/yourusername/telegram-affiliate-bot",
        "repository": "https://github.com/yourusername/telegram-affiliate-bot",
        "env": {
            "TELEGRAM_BOT_TOKEN": {
                "description": "Your Telegram Bot Token from @BotFather",
                "required": True
            },
            "TELEGRAM_ADMIN_ID": {
                "description": "Your Telegram User ID (admin)",
                "required": True
            },
            "AMAZON_ASSOCIATE_TAG": {
                "description": "Your Amazon Associates Tag",
                "required": False
            },
            "EBAY_CAMPAIGN_ID": {
                "description": "Your eBay Partner Network Campaign ID",
                "required": False
            }
        },
        "buildpacks": [
            {
                "url": "heroku/python"
            }
        ],
        "formation": {
            "web": {
                "quantity": 1,
                "size": "basic"
            }
        }
    }
    
    import json
    with open('app.json', 'w') as f:
        json.dump(app_json, f, indent=2)
    
    print("✅ Created Heroku deployment files")

def deploy_to_heroku():
    """Deploy bot to Heroku"""
    print("🚀 Deploying to Heroku...")
    
    try:
        # Initialize git if not exists
        if not os.path.exists('.git'):
            subprocess.run(['git', 'init'], check=True)
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], check=True)
        
        # Create Heroku app
        app_name = input("Enter your Heroku app name (or press Enter for auto-generated): ").strip()
        if app_name:
            subprocess.run(['heroku', 'create', app_name], check=True)
        else:
            subprocess.run(['heroku', 'create'], check=True)
        
        # Set environment variables
        bot_token = input("Enter your TELEGRAM_BOT_TOKEN: ").strip()
        admin_id = input("Enter your TELEGRAM_ADMIN_ID: ").strip()
        
        subprocess.run(['heroku', 'config:set', f'TELEGRAM_BOT_TOKEN={bot_token}'], check=True)
        subprocess.run(['heroku', 'config:set', f'TELEGRAM_ADMIN_ID={admin_id}'], check=True)
        
        # Optional affiliate credentials
        amazon_tag = input("Enter AMAZON_ASSOCIATE_TAG (optional, press Enter to skip): ").strip()
        if amazon_tag:
            subprocess.run(['heroku', 'config:set', f'AMAZON_ASSOCIATE_TAG={amazon_tag}'], check=True)
        
        # Deploy
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Deploy to Heroku'], check=True)
        subprocess.run(['git', 'push', 'heroku', 'main'], check=True)
        
        print("🎉 Successfully deployed to Heroku!")
        print("Your bot is now running 24/7 in the cloud!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Deployment failed: {e}")
        print("Make sure you have Heroku CLI installed and are logged in")

if __name__ == "__main__":
    print("🌐 Heroku Deployment for Telegram Affiliate Bot")
    print("=" * 50)
    
    choice = input("\n1. Create deployment files\n2. Deploy to Heroku\n3. Both\nChoose (1-3): ")
    
    if choice in ['1', '3']:
        create_heroku_files()
    
    if choice in ['2', '3']:
        deploy_to_heroku()
    
    print("\n✅ Deployment process complete!")
    print("💡 Your bot will run 24/7 on Heroku's servers")
