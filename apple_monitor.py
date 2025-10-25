#!/usr/bin/env python3
"""
Apple Store Monitor with Selenium - Uses real browser to avoid anti-bot protection

First, get app specific password from google account settings: https://myaccount.google.com/apppasswords

Then run:
export EMAIL_USER="your_email@gmail.com"
export EMAIL_PASSWORD="16 characters app specific password"
pip install -r requirements.txt
python apple_monitor.py

Check the product id using bestbuy or other retailers website.
Check the store id here https://github.com/worthbak/apple-store-inventory-checker/blob/main/apple-store-numbers.md
"""

import time
import logging
import smtplib
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('apple_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AppleMonitorSelenium:
    def __init__(self, email: str, product_id: str, store_id: str):
        self.email = email
        self.api_url = "https://www.apple.com/shop/fulfillment-messages"
        self.params = {
            "parts.0": product_id, # MFXG4LL/A promax 256 silver; MG7K4LL/A pro 256 silver;
            "store": store_id, # R232 is natick, R354 is nashua
            "searchNearby": "false"
        }
        self.product_url = f"https://www.apple.com/shop/product/{product_id}"
        self.last_response = None
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver with realistic options."""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Run in headless mode (comment out to see browser)
        chrome_options.add_argument("--headless")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Chrome driver initialized successfully")
        except WebDriverException as e:
            logger.error(f"Error setting up Chrome driver: {e}")
            logger.error("Make sure ChromeDriver is installed and in PATH")
            raise
    
    def check_availability(self) -> Optional[Dict[str, Any]]:
        """Check Apple fulfillment API using Selenium."""
        try:
            if not self.driver:
                self.setup_driver()
            
            logger.info("Checking Apple fulfillment API with Selenium...")
            
            # Step 1: Visit Apple homepage
            logger.info("Step 1: Visiting Apple homepage...")
            self.driver.get("https://www.apple.com")
            time.sleep(2)
            
            # Step 2: Visit product page
            logger.info("Step 2: Visiting product page...")
            self.driver.get(self.product_url)
            time.sleep(3)
            
            # Step 3: Make API call using JavaScript
            logger.info("Step 3: Making API call...")
            # Build URL with dynamic parameters
            params_str = "&".join([f"{k}={v}" for k, v in self.params.items()])
            api_url_with_params = f"{self.api_url}?{params_str}"
            
            # Execute JavaScript to make the API call
            result = self.driver.execute_async_script(f"""
                var callback = arguments[arguments.length - 1];
                fetch('{api_url_with_params}', {{
                    method: 'GET',
                    headers: {{
                        'Accept': 'application/json, text/plain, */*',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache',
                        'Referer': '{self.product_url}',
                        'Origin': 'https://www.apple.com'
                    }},
                    credentials: 'include'
                }})
                .then(response => response.json())
                .then(data => callback(data))
                .catch(error => callback({{error: error.toString()}}));
            """)
            
            if isinstance(result, dict):
                if 'error' in result:
                    logger.error(f"JavaScript error: {result['error']}")
                    return None
                logger.info(f"API response received: {len(result.get('body', {}).get('content', {}).get('pickupMessage', {}).get('stores', []))} stores")
                return result
            else:
                logger.error(f"Unexpected API response: {result}")
                return None
                
        except TimeoutException:
            logger.error("Timeout waiting for API response")
            return None
        except WebDriverException as e:
            logger.error(f"WebDriver error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    def parse_availability(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the API response to extract availability information."""
        try:
            stores = data.get('body', {}).get('content', {}).get('pickupMessage', {}).get('stores', [])
            
            availability_info = {
                'timestamp': datetime.now().isoformat(),
                'stores': [],
                'has_availability': False
            }
            
            for store in stores:
                store_info = {
                    'storeName': store.get('storeName', 'Unknown'),
                    'storeNumber': store.get('storeNumber', 'Unknown'),
                    'partsAvailability': {}
                }
                
                parts = store.get('partsAvailability', {})
                for part_number, part_info in parts.items():
                    availability = part_info.get('pickupDisplay', 'Unknown')
                    store_info['partsAvailability'][part_number] = availability
                    
                    if availability == 'available':
                        availability_info['has_availability'] = True
                
                availability_info['stores'].append(store_info)
            
            return availability_info
            
        except Exception as e:
            logger.error(f"Error parsing availability data: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def send_email(self, subject: str, body: str) -> bool:
        """Send email notification."""
        try:
            # Get credentials from environment variables
            email_user = os.getenv('EMAIL_USER', 'test@gmail.com')
            email_password = os.getenv('EMAIL_PASSWORD', 'test')
            
            msg = MIMEMultipart()
            msg['From'] = email_user
            msg['To'] = self.email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Gmail SMTP configuration
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(email_user, email_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent to {self.email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def format_email_body(self, availability_info: Dict[str, Any]) -> str:
        """Format the availability information for email."""
        body = f"Apple Store Availability Check - {availability_info['timestamp']}\n\n"
        
        if availability_info.get('has_availability'):
            body += "🎉 PRODUCT AVAILABLE!\n\n"
        else:
            body += "❌ Product not available\n\n"
        
        body += "Store Details:\n"
        body += "=" * 50 + "\n"
        
        for store in availability_info.get('stores', []):
            body += f"Store: {store['storeName']} (#{store['storeNumber']})\n"
            for part, status in store['partsAvailability'].items():
                body += f"  {part}: {status}\n"
            body += "\n"
        
        return body
    
    def run_check(self):
        """Run a single availability check."""
        data = self.check_availability()
        if not data:
            return
        
        availability_info = self.parse_availability(data)
        
        # Check if availability has changed
        if self.last_response != availability_info:
            self.last_response = availability_info
            
            # Only send email when product becomes available
            if availability_info.get('has_availability'):
                subject = "🎉 Apple Product Available!"
                body = self.format_email_body(availability_info)
                
                # Send email notification
                self.send_email(subject, body)
                
                logger.info(f"Product available! Email sent to {self.email}")
                print(f"\n{body}")
            else:
                logger.info("Product not available - no email sent")
                print(f"\nProduct not available at {availability_info['timestamp']}")
        else:
            logger.info("No changes in availability")
    
    def start_monitoring(self, interval_minutes: int = 30):
        """Start monitoring with specified interval."""
        logger.info(f"Starting Apple Store monitoring with Selenium (checking every {interval_minutes} minutes)")
        logger.info(f"Monitoring product: {self.params['parts.0']}")
        logger.info(f"Target store: {self.params['store']}")
        logger.info(f"Email notifications to: {self.email}")
        
        try:
            while True:
                self.run_check()
                self.cleanup()  # Clean up after each check
                logger.info(f"Waiting {interval_minutes} minutes until next check...")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        finally:
            self.cleanup()  # Final cleanup
    
    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("Chrome driver cleaned up")

def main():
    """Main function to start the monitor."""

    email =os.getenv('EMAIL_USER', 'test@gmail.com')
    product_id = os.getenv('PRODUCT_ID', 'MFXG4LL/A')
    store_id = os.getenv('STORE_ID', 'R354')
    interval_minutes = int(os.getenv('INTERVAL_MINUTES', 30))
    # MFXG4LL/A promax 256 silver; MG7K4LL/A pro 256 silver;
    # R232 is natick,ma; R354 is nashua,nh

    monitor = AppleMonitorSelenium(email, product_id, store_id)
    
    print("Apple Store Monitor")
    print("=" * 50)
    print(f"Monitoring: {monitor.params['parts.0']}")
    print(f"Store: {monitor.params['store']}")
    print(f"Email: {email}")
    print(f"Interval: {interval_minutes} minutes")
    print("=" * 50)
    print("Make sure ChromeDriver is installed:")
    print("brew install chromedriver")
    print("\nStarting monitoring... (Press Ctrl+C to stop)")
    
    try:
        monitor.start_monitoring(interval_minutes)
    finally:
        monitor.cleanup()

if __name__ == "__main__":
    main()
