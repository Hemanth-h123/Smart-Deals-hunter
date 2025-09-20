"""
Setup HTTPS tunnel for Telegram Mini App development
"""

import subprocess
import time
import requests
import json
import logging

logger = logging.getLogger(__name__)

class TunnelManager:
    def __init__(self):
        self.tunnel_url = None
        self.ngrok_process = None
    
    def start_ngrok_tunnel(self, port=5000):
        """Start ngrok tunnel for the Flask app"""
        try:
            # Start ngrok tunnel
            cmd = f"ngrok http {port} --log=stdout"
            self.ngrok_process = subprocess.Popen(
                cmd, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            
            # Wait for ngrok to start
            time.sleep(3)
            
            # Get the public URL
            try:
                response = requests.get("http://localhost:4040/api/tunnels")
                tunnels = response.json()
                
                for tunnel in tunnels.get('tunnels', []):
                    if tunnel.get('proto') == 'https':
                        self.tunnel_url = tunnel['public_url']
                        logger.info(f"Ngrok tunnel started: {self.tunnel_url}")
                        return self.tunnel_url
                        
            except Exception as e:
                logger.error(f"Failed to get ngrok URL: {e}")
                
        except Exception as e:
            logger.error(f"Failed to start ngrok: {e}")
            
        return None
    
    def get_tunnel_url(self):
        """Get the current tunnel URL"""
        return self.tunnel_url
    
    def stop_tunnel(self):
        """Stop the ngrok tunnel"""
        if self.ngrok_process:
            self.ngrok_process.terminate()
            logger.info("Ngrok tunnel stopped")

# Alternative: Use pyngrok for easier management
def setup_ngrok_tunnel(port=5000):
    """Setup ngrok tunnel using pyngrok library"""
    try:
        from pyngrok import ngrok
        import time
        
        # Kill any existing ngrok processes
        try:
            ngrok.kill()
            time.sleep(2)  # Wait for processes to terminate
        except:
            pass
        
        # Start tunnel
        tunnel = ngrok.connect(port, "http")
        tunnel_url = tunnel.public_url
        
        # Ensure HTTPS URL
        if tunnel_url.startswith('http://'):
            tunnel_url = tunnel_url.replace('http://', 'https://')
        
        # Save clean tunnel URL
        with open('webapp_url.txt', 'w') as f:
            f.write(tunnel_url)
        
        logger.info(f"Ngrok tunnel created: {tunnel_url}")
        return tunnel_url
        
    except Exception as e:
        logger.error(f"Failed to setup ngrok tunnel: {e}")
        return None
