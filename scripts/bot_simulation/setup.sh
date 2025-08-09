#!/bin/bash
# Setup script for Playwright Python

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Installing Playwright browsers..."
playwright install chromium

echo "Creating .env file from sample..."
if [ ! -f .env ]; then
    cp .env.sample .env
    echo "✓ Created .env file. Edit it to customize your settings."
else
    echo "✓ .env file already exists."
fi

echo ""
echo "Setup complete! You can now run:"
echo "python auto_browser.py"
echo ""
echo "Or customize settings in .env file and run with overrides:"
echo "python auto_browser.py --url https://your-custom-url.com --headless true"
