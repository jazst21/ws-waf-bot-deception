#!/bin/bash
set -e

# Detect OS and architecture
OS=$(grep -E '^ID=' /etc/os-release | cut -d'=' -f2 | tr -d '"')
# Check if running on Ubuntu (including in containers)
if uname -a | grep -i ubuntu || grep -qi ubuntu /etc/os-release /proc/version 2>/dev/null; then
    OS="ubuntu"
fi
ARCH=$(uname -m)

echo "Detected OS: $OS, Architecture: $ARCH"

# Update package manager and install dependencies
case "$OS" in
    ubuntu|debian)
        echo "Updating apt packages..."
        sudo apt update && sudo apt upgrade -y
        sudo apt install -y python3 python3-pip python3-venv curl wget git
        
        # Install essential packages for Playwright
        echo "Installing essential packages for Playwright..."
        if [[ "$OS" == "ubuntu" ]]; then
            # Ubuntu 24.04 package names
            sudo apt install -y \
                libcups2 \
                libxfixes3 \
                libpango-1.0-0 \
                libcairo2 \
                libdrm2 \
                libxkbcommon0 \
                libxcomposite1 \
                libxdamage1 \
                libxrandr2 \
                libgbm1 \
                libxss1 \
                xvfb \
                libasound2t64 \
                libatk-bridge2.0-0t64 \
                libatk1.0-0t64 \
                libatspi2.0-0t64 \
                libglib2.0-0t64 \
                libgtk-3-0t64 || echo "Some packages may not be available"
        else
            # Debian package names
            sudo apt install -y \
                libcups2 \
                libxfixes3 \
                libpango-1.0-0 \
                libcairo2 \
                libdrm2 \
                libxkbcommon0 \
                libxcomposite1 \
                libxdamage1 \
                libxrandr2 \
                libgbm1 \
                libxss1 \
                xvfb \
                libasound2 \
                libatk-bridge2.0-0 \
                libatk1.0-0 \
                libatspi2.0-0 \
                libglib2.0-0 \
                libgtk-3-0 || echo "Some packages may not be available"
        fi
        ;;
    amzn)
        echo "Updating yum packages..."
        sudo yum update -y
        sudo yum install -y python3 python3-pip curl wget git
        # Install python3-venv separately as it may not be available in all Amazon Linux versions
        sudo yum install -y python3-venv || echo "python3-venv not available, using python3 -m venv"
        ;;
    *)
        echo "Unsupported OS: $OS"
        exit 1
        ;;
esac

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install Playwright system dependencies manually for Debian/Ubuntu
echo "Installing Playwright system dependencies manually..."
case "$OS" in
    ubuntu|debian)
        echo "Skipping 'playwright install-deps' due to compatibility issues"
        ;;
    *)
        playwright install-deps || echo "Warning: Some system dependencies may have failed to install"
        ;;
esac

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install

# Install Chromium specifically
echo "Installing Chromium specifically..."
playwright install chromium

# Create .env file from sample
echo "Creating .env file from sample..."
if [ ! -f .env ]; then
    if [ -f .env.sample ]; then
        cp .env.sample .env
        echo "✓ Created .env file. Edit it to customize your settings."
    else
        echo "✓ Creating default .env file..."
        cat > .env << EOF
# Bot Simulation Configuration
TARGET_URL=https://your-domain.com
HEADLESS=true
DELAY_MIN=1
DELAY_MAX=3
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
REQUESTS_PER_SESSION=10
EOF
    fi
else
    echo "✓ .env file already exists."
fi

echo ""
echo "Setup complete! Virtual environment is now activated."
echo "You can now run scripts directly:"
echo "python 1_auto_browser.py"
echo ""
echo "Or use the run scripts that handle venv activation automatically."

# Create a script to activate venv and start new shell
cat > activate_and_shell.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
exec bash --rcfile <(echo "PS1='(venv) \u@\h:\w\$ '")
EOF

chmod +x activate_and_shell.sh

# Start new shell with venv activated
exec bash -c "source venv/bin/activate && exec bash --rcfile <(echo \"PS1='(venv) \u@\h:\w\$ '\")"
