# Apple Inventory Checker

A Python-based monitoring tool that automatically checks Apple Store inventory for specific products and sends email notifications when items become available. Uses Selenium with Chrome WebDriver to bypass anti-bot protection.

## Features

- 🔍 **Real-time monitoring** of Apple Store inventory
- 📧 **Email notifications** when products become available
- 🤖 **Anti-bot protection bypass** using Selenium with realistic browser behavior
- ⚙️ **Configurable** product IDs, store locations, and check intervals
- 📝 **Comprehensive logging** with both file and console output
- 🛡️ **Error handling** with automatic retry and cleanup

## Prerequisites

- Python 3.7+
- Chrome browser installed
- ChromeDriver installed
- Gmail account with app-specific password

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/liyupeng111/apple_inventory_checker.git
   cd apple_inventory_checker
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install ChromeDriver:**
   ```bash
   # macOS
   brew install chromedriver
   
   # Ubuntu/Debian
   sudo apt-get install chromium-chromedriver
   
   # Or download from: https://chromedriver.chromium.org/
   ```

4. **Set up Gmail app-specific password:**
   - Go to [Google Account Settings](https://myaccount.google.com/apppasswords)
   - Generate an app-specific password for this application
   - Save the 16-character password

## Configuration

### Environment Variables

Set the following environment variables before running:

```bash
export EMAIL_USER="your_email@gmail.com"
export EMAIL_PASSWORD="your_16_character_app_password"
export PRODUCT_ID="MFXG4LL/A"  # Product SKU
export STORE_ID="R354"         # Store location code
export INTERVAL_MINUTES=30     # Check interval in minutes
```

### Product IDs

Find product IDs from Bestbuy website or other retailers:
- iPhone 17 Pro Max 256GB Silver: `MFXG4LL/A`
- iPhone 17 Pro 256GB Silver: `MG7K4LL/A`

### Store IDs

Find store codes in the [Apple Store Numbers](https://github.com/worthbak/apple-store-inventory-checker/blob/main/apple-store-numbers.md) reference:
- Natick, MA: `R232`
- Nashua, NH: `R354`

## Usage

**Run the monitor:**
   ```bash
   python apple_monitor.py
   ```

## License

MIT License

This project is for educational and personal use only. Please respect Apple's terms of service and rate limits.

## Disclaimer

This tool is not affiliated with Apple Inc. Use responsibly and in accordance with Apple's terms of service. The authors are not responsible for any misuse of this software.
