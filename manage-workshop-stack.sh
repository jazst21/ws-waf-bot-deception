#!/bin/bash

STACK_OPERATION=$1

# Function to detect OS and set package manager
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
    elif [ -f /etc/lsb-release ]; then
        . /etc/lsb-release
        OS=$DISTRIB_ID
        VER=$DISTRIB_RELEASE
    elif [ -f /etc/debian_version ]; then
        OS=Debian
        VER=$(cat /etc/debian_version)
    elif [ -f /etc/SuSe-release ]; then
        OS=openSUSE
    elif [ -f /etc/redhat-release ]; then
        OS=RedHat
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
}

# Function to install packages based on OS
install_packages() {
    detect_os
    
    if [[ "$OS" == *"Amazon Linux"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"CentOS"* ]]; then
        # Amazon Linux 2 / RHEL / CentOS
        echo "Detected Amazon Linux/RHEL/CentOS - using yum"
        sudo yum update -y
        sudo yum install -y wget unzip
    elif [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        # Ubuntu / Debian
        echo "Detected Ubuntu/Debian - using apt"
        sudo apt-get update -y
        sudo apt-get install -y wget unzip gnupg software-properties-common
    elif [[ "$OS" == *"Alpine"* ]]; then
        # Alpine Linux
        echo "Detected Alpine Linux - using apk"
        apk update
        apk add --no-cache wget unzip
    else
        echo "Unsupported OS: $OS"
        exit 1
    fi
}

# Function to install Terraform
install_terraform() {
    detect_os
    
    if [[ "$OS" == *"Amazon Linux"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"CentOS"* ]]; then
        # Amazon Linux 2 / RHEL / CentOS
        echo "Installing Terraform for Amazon Linux/RHEL..."
        sudo yum install -y yum-utils
        sudo yum-config-manager --add-repo https://rpm.releases.hashicorp.com/AmazonLinux/hashicorp.repo
        sudo yum -y install terraform
    elif [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        # Ubuntu / Debian
        echo "Installing Terraform for Ubuntu/Debian..."
        wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg > /dev/null
        echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
        sudo apt-get update -y
        sudo apt-get install -y terraform
    else
        # Generic installation via direct download
        echo "Installing Terraform via direct download..."
        TERRAFORM_VERSION="1.5.7"
        
        # Detect architecture
        ARCH=$(uname -m)
        if [[ "$ARCH" == "x86_64" ]]; then
            TERRAFORM_ARCH="amd64"
        elif [[ "$ARCH" == "aarch64" ]] || [[ "$ARCH" == "arm64" ]]; then
            TERRAFORM_ARCH="arm64"
        else
            echo "Unsupported architecture for Terraform: $ARCH"
            exit 1
        fi
        
        TMP_DIR=$(mktemp -d)
        cd $TMP_DIR
        wget "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_${TERRAFORM_ARCH}.zip"
        unzip "terraform_${TERRAFORM_VERSION}_linux_${TERRAFORM_ARCH}.zip"
        sudo mv terraform /usr/local/bin/
        cd -
        rm -rf $TMP_DIR
    fi
}

# Function to install Node.js
install_nodejs() {
    detect_os
    
    if [[ "$OS" == *"Amazon Linux"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"CentOS"* ]]; then
        # Amazon Linux 2 / RHEL / CentOS
        echo "Installing Node.js for Amazon Linux/RHEL..."
        # Try NodeSource repository first
        if curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash - 2>/dev/null; then
            sudo yum install -y nodejs
        else
            # Fallback: Use EPEL repository
            echo "NodeSource failed, trying EPEL repository..."
            sudo yum install -y epel-release
            sudo yum install -y nodejs npm
        fi
    elif [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        # Ubuntu / Debian
        echo "Installing Node.js for Ubuntu/Debian..."
        # Try NodeSource repository first
        if curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - 2>/dev/null; then
            sudo apt-get install -y nodejs
        else
            # Fallback: Use default repository
            echo "NodeSource failed, trying default repository..."
            sudo apt-get update -y
            sudo apt-get install -y nodejs npm
        fi
    elif [[ "$OS" == *"Alpine"* ]]; then
        # Alpine Linux
        echo "Installing Node.js for Alpine..."
        apk add --no-cache nodejs npm
    else
        # Generic installation via binary download (includes npm)
        echo "Installing Node.js via binary download..."
        NODE_VERSION="18.17.0"
        
        # Detect architecture
        ARCH=$(uname -m)
        if [[ "$ARCH" == "x86_64" ]]; then
            NODE_ARCH="x64"
        elif [[ "$ARCH" == "aarch64" ]] || [[ "$ARCH" == "arm64" ]]; then
            NODE_ARCH="arm64"
        else
            echo "Unsupported architecture for Node.js: $ARCH"
            exit 1
        fi
        
        TMP_DIR=$(mktemp -d)
        cd $TMP_DIR
        wget "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-${NODE_ARCH}.tar.xz"
        tar -xf "node-v${NODE_VERSION}-linux-${NODE_ARCH}.tar.xz"
        sudo cp -r "node-v${NODE_VERSION}-linux-${NODE_ARCH}"/* /usr/local/
        cd -
        rm -rf $TMP_DIR
    fi
    
    # Verify both node and npm are installed
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js installation failed"
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        echo "❌ npm installation failed"
        exit 1
    fi
    
    echo "✅ Node.js and npm installed successfully"
}

# Function to handle existing resources
handle_existing_resources() {
    echo "🔍 Checking for existing resources..."
    
    # Use the comprehensive import script
    if [ -f "./import-existing-resources.sh" ]; then
        echo "📥 Running comprehensive resource import..."
        ./import-existing-resources.sh
    else
        echo "⚠️  Import script not found, using basic import logic..."
        
        # Fallback to basic import logic
        FRONTEND_OAC=$(aws cloudfront list-origin-access-controls --query "OriginAccessControlList.Items[?Name=='bot-deception-dev-frontend-oac'].Id" --output text 2>/dev/null)
        if [ ! -z "$FRONTEND_OAC" ] && [ "$FRONTEND_OAC" != "None" ]; then
            echo "Found existing frontend OAC: $FRONTEND_OAC"
            terraform import aws_cloudfront_origin_access_control.frontend $FRONTEND_OAC 2>/dev/null || true
        fi
        
        FAKE_PAGES_OAC=$(aws cloudfront list-origin-access-controls --query "OriginAccessControlList.Items[?Name=='bot-deception-dev-fake-webpages-oac'].Id" --output text 2>/dev/null)
        if [ ! -z "$FAKE_PAGES_OAC" ] && [ "$FAKE_PAGES_OAC" != "None" ]; then
            echo "Found existing fake pages OAC: $FAKE_PAGES_OAC"
            terraform import aws_cloudfront_origin_access_control.fake_webpages $FAKE_PAGES_OAC 2>/dev/null || true
        fi
        
        DISTRIBUTION_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?Comment=='Bot Deception Demo Distribution'].Id" --output text 2>/dev/null)
        if [ ! -z "$DISTRIBUTION_ID" ] && [ "$DISTRIBUTION_ID" != "None" ]; then
            echo "Found existing CloudFront distribution: $DISTRIBUTION_ID"
            terraform import aws_cloudfront_distribution.main $DISTRIBUTION_ID 2>/dev/null || true
        fi
    fi
    
    echo "✅ Resource import completed."
}

# Function to clean up failed state
cleanup_failed_state() {
    echo "Cleaning up potentially corrupted state..."
    
    # Remove any resources that might be in a bad state
    terraform state list 2>/dev/null | grep -E "(cloudfront_origin_access_control|cloudfront_distribution)" | while read resource; do
        echo "Checking resource: $resource"
        terraform state show "$resource" >/dev/null 2>&1 || {
            echo "Removing invalid state for: $resource"
            terraform state rm "$resource" 2>/dev/null || true
        }
    done
}

if [[ "$STACK_OPERATION" == "create" || "$STACK_OPERATION" == "Create" || "$STACK_OPERATION" == "update" ]]; then
    # deploy / update workshop resources
    
    # Install required packages
    install_packages
    
    # Check if terraform is installed, if not, install it
    if ! command -v terraform &> /dev/null; then
        echo "Terraform not found. Installing Terraform..."
        install_terraform
        echo "Terraform installed successfully."
    else
        echo "Terraform is already installed."
        terraform version
    fi
    
    # Check if AWS CLI v2 is installed, if not, install it
    if ! command -v aws &> /dev/null; then
        echo "AWS CLI not found. Installing AWS CLI v2..."
        TMP_DIR=$(mktemp -d)
        cd $TMP_DIR
        
        # Detect architecture
        ARCH=$(uname -m)
        if [[ "$ARCH" == "x86_64" ]]; then
            curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
        elif [[ "$ARCH" == "aarch64" ]]; then
            curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip"
        else
            echo "Unsupported architecture: $ARCH"
            exit 1
        fi
        
        unzip awscliv2.zip
        sudo ./aws/install
        cd -
        rm -rf $TMP_DIR
        echo "AWS CLI v2 installed successfully."
    else
        echo "AWS CLI is already installed."
        aws --version
    fi
    
    # Check if Node.js is installed, if not, install it
    if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
        echo "Node.js/npm not found. Installing Node.js..."
        install_nodejs
        echo "Node.js installed successfully."
        node --version
        npm --version
    else
        echo "Node.js is already installed."
        node --version
        npm --version
    fi
    
    cd terraform
    echo "Deploying workshop resources..."
    
    # Initialize Terraform
    terraform init
    
    # Clean up conflicting resources first
    echo "🧹 Cleaning up conflicting resources..."
    if [ -f "./cleanup-conflicts.sh" ]; then
        ./cleanup-conflicts.sh
    else
        echo "⚠️  Cleanup script not found, proceeding with deployment..."
    fi
    
    # Check if we should do a clean deployment (useful for CodeBuild retries)
    if [ "$CLEAN_DEPLOY" == "true" ] || [ "$2" == "clean" ]; then
        echo "🧹 Clean deployment requested..."
        if [ -f "./clean-deploy.sh" ]; then
            ./clean-deploy.sh clean
        else
            echo "⚠️  Clean deploy script not found, using standard deployment"
            terraform destroy -auto-approve 2>/dev/null || true
            sleep 5
            terraform apply -auto-approve
        fi
    else
        # Standard deployment with resource import
        # Handle existing resources to prevent conflicts
        handle_existing_resources
        
        # Clean up any corrupted state
        cleanup_failed_state
        
        # Plan with detailed output
        echo "Running terraform plan..."
        terraform plan -detailed-exitcode
        PLAN_EXIT_CODE=$?
        
        if [ $PLAN_EXIT_CODE -eq 0 ]; then
            echo "No changes needed."
        elif [ $PLAN_EXIT_CODE -eq 2 ]; then
            echo "Changes detected, applying..."
            terraform apply -auto-approve
        else
            echo "Terraform plan failed with exit code: $PLAN_EXIT_CODE"
            
            # Check if the error is related to subnet conflicts
            if terraform plan 2>&1 | grep -q "InvalidSubnet.Conflict\|CIDR.*conflicts"; then
                echo "🌐 Detected subnet CIDR conflicts, running VPC cleanup..."
                if [ -f "./cleanup-vpc.sh" ]; then
                    ./cleanup-vpc.sh
                    sleep 10  # Wait for AWS eventual consistency
                    echo "🚀 Retrying deployment after VPC cleanup..."
                    terraform apply -auto-approve
                else
                    echo "⚠️  VPC cleanup script not found, attempting clean deployment..."
                    if [ -f "./clean-deploy.sh" ]; then
                        ./clean-deploy.sh clean
                    else
                        terraform destroy -auto-approve 2>/dev/null || true
                        sleep 10
                        terraform apply -auto-approve
                    fi
                fi
            else
                echo "🧹 Attempting clean deployment as fallback..."
                if [ -f "./clean-deploy.sh" ]; then
                    ./clean-deploy.sh clean
                else
                    terraform destroy -auto-approve 2>/dev/null || true
                    sleep 5
                    terraform apply -auto-approve
                fi
            fi
        fi
    fi
    
elif [ "$STACK_OPERATION" == "cleanup-vpc" ]; then
    # Clean up VPC resources specifically
    cd terraform
    echo "🌐 Cleaning up VPC resources to resolve subnet conflicts..."
    if [ -f "./cleanup-vpc.sh" ]; then
        ./cleanup-vpc.sh
    else
        echo "❌ VPC cleanup script not found"
        exit 1
    fi
    
elif [ "$STACK_OPERATION" == "delete" ] || [ "$STACK_OPERATION" == "Delete" ]; then
    # delete workshop resources
    cd terraform
    echo "Deleting workshop resources..."
    terraform init
    terraform destroy -auto-approve
    
else
    echo "Usage: $0 {create|update|delete|cleanup-vpc} [clean]"
    echo "  create/update - Deploy or update workshop resources"
    echo "  delete        - Delete workshop resources"
    echo "  cleanup-vpc   - Clean up VPC resources to resolve subnet conflicts"
    echo "  clean         - Force clean deployment (destroy then create)"
    echo ""
    echo "Examples:"
    echo "  $0 create         # Standard deployment with resource import"
    echo "  $0 create clean   # Clean deployment (destroy existing first)"
    echo "  $0 cleanup-vpc    # Clean up VPC to resolve subnet CIDR conflicts"
    echo "  $0 delete         # Destroy all resources"
    echo ""
    echo "Environment variables:"
    echo "  CLEAN_DEPLOY=true  # Force clean deployment"
    exit 1
fi
