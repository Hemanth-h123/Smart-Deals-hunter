"""
Render Deployment Script - Free 24/7 Cloud Hosting
Deploy your Telegram Affiliate Bot to Render (Free Tier)
"""

import os
import json
import yaml

def create_render_files():
    """Create necessary files for Render deployment"""
    
    # Create render.yaml for automatic deployment
    render_config = {
        'services': [
            {
                'type': 'web',
                'name': 'telegram-affiliate-bot',
                'env': 'python',
                'buildCommand': 'pip install -r requirements.txt',
                'startCommand': 'python integrated_bot.py',
                'plan': 'free',
                'healthCheckPath': '/health',
                'envVars': [
                    {
                        'key': 'TELEGRAM_BOT_TOKEN',
                        'sync': False
                    },
                    {
                        'key': 'TELEGRAM_ADMIN_ID',
                        'sync': False
                    },
                    {
                        'key': 'DATABASE_URL',
                        'value': 'sqlite:///affiliate_bot.db'
                    },
                    {
                        'key': 'AMAZON_ASSOCIATE_TAG',
                        'sync': False
                    },
                    {
                        'key': 'EBAY_CAMPAIGN_ID',
                        'sync': False
                    }
                ]
            }
        ]
    }
    
    with open('render.yaml', 'w') as f:
        yaml.dump(render_config, f, default_flow_style=False)
    
    # Create requirements.txt if it doesn't exist or update it
    requirements = """
python-telegram-bot==20.3
sqlalchemy==2.0.19
requests==2.31.0
beautifulsoup4==4.12.2
flask==2.3.2
pyngrok==7.0.0
schedule==1.2.0
python-dotenv==1.0.0
aiohttp==3.8.5
PyYAML==6.0.1
""".strip()
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements)
    
    print("Created Render deployment files")

def create_health_endpoint():
    """Create a simple health check endpoint for Render"""
    
    health_code = '''
# Add this to your integrated_bot.py for Render health checks
import threading
from flask import Flask

def start_health_server():
    """Start health check server for Render"""
    app = Flask(__name__)
    
    @app.route('/health')
    def health():
        return {"status": "healthy", "service": "telegram-affiliate-bot"}, 200
    
    @app.route('/')
    def home():
        return {"message": "Telegram Affiliate Bot is running!", "status": "active"}, 200
    
    # Run health server in background
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=False)

# Add this to your integrated_bot.py main function:
# threading.Thread(target=start_health_server, daemon=True).start()
'''
    
    with open('health_endpoint.py', 'w') as f:
        f.write(health_code)
    
    print("Created health endpoint code")

def show_render_deployment_steps():
    """Show step-by-step Render deployment instructions"""
    
    steps = """
RENDER DEPLOYMENT STEPS (5 minutes)

1. CREATE RENDER ACCOUNT
   - Go to: https://render.com
   - Sign up with GitHub (recommended)
   - FREE tier includes 750 hours/month

2. CONNECT GITHUB
   - Upload your bot code to GitHub repository
   - Connect your GitHub account to Render
   - Render will auto-detect your Python app

3. CREATE WEB SERVICE
   - Click "New +" -> "Web Service"
   - Select your GitHub repository
   - Render auto-fills most settings

4. CONFIGURE SERVICE
   Name: telegram-affiliate-bot
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python integrated_bot.py
   Plan: Free

5. SET ENVIRONMENT VARIABLES
   Add these in Render dashboard:
   
   TELEGRAM_BOT_TOKEN = 8008155121:AAHrZ-0vk5B36sgVMm4kunEuqiO8SZeLdqQ
   TELEGRAM_ADMIN_ID = 5648252199
   DATABASE_URL = sqlite:///affiliate_bot.db
   PORT = 10000
   
   Optional (add when you get affiliate accounts):
   AMAZON_ASSOCIATE_TAG = your_amazon_tag
   EBAY_CAMPAIGN_ID = your_ebay_id

6. DEPLOY
   - Click "Create Web Service"
   - Render builds and deploys automatically
   - Your bot will be live in 3-5 minutes
   - Runs 24/7 automatically!

7. VERIFY DEPLOYMENT
   - Check Render logs for "Bot is running"
   - Test your bot on Telegram
   - Bot auto-restarts if it crashes

COST: FREE
- 750 hours/month free (enough for 24/7)
- Automatic SSL certificates
- Global CDN included
- No credit card required
"""
    
    print(steps)

def create_dockerfile():
    """Create Dockerfile for containerized deployment (optional)"""
    
    dockerfile_content = """
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD ["python", "integrated_bot.py"]
"""
    
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile_content)
    
    print("Created Dockerfile for containerized deployment")

def update_integrated_bot_for_render():
    """Show how to update integrated_bot.py for Render"""
    
    render_updates = '''
# Add these imports to the top of integrated_bot.py
import threading
from flask import Flask
import os

# Add this function to integrated_bot.py
def start_health_server():
    """Start health check server for Render"""
    app = Flask(__name__)
    
    @app.route('/health')
    def health():
        return {"status": "healthy", "service": "telegram-affiliate-bot"}, 200
    
    @app.route('/')
    def home():
        return {"message": "Telegram Affiliate Bot is running!", "status": "active"}, 200
    
    # Run on the port Render provides
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

# Add this line in your main() function, before bot.run():
# threading.Thread(target=start_health_server, daemon=True).start()
'''
    
    with open('render_integration_guide.txt', 'w') as f:
        f.write(render_updates)
    
    print("Created integration guide for Render")

if __name__ == "__main__":
    print("Render Cloud Deployment Setup")
    print("=" * 50)
    
    create_render_files()
    create_health_endpoint()
    create_dockerfile()
    update_integrated_bot_for_render()
    show_render_deployment_steps()
    
    print("\nNEXT STEPS:")
    print("1. Upload your code to GitHub")
    print("2. Go to render.com and create account")
    print("3. Create Web Service from your GitHub repo")
    print("4. Add environment variables")
    print("5. Deploy - your bot runs 24/7 for FREE!")
    print("\nRender is perfect for Telegram bots - reliable and free!")
