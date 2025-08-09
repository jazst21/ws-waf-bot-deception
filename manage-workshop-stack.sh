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
        TMP_DIR=$(mktemp -d)
        cd $TMP_DIR
        wget "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip"
        unzip "terraform_${TERRAFORM_VERSION}_linux_amd64.zip"
        sudo mv terraform /usr/local/bin/
        cd -
        rm -rf $TMP_DIR
    fi
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
    
    cd terraform
    echo "Deploying workshop resources..."
    terraform init
    terraform plan
    terraform apply -auto-approve
    
elif [ "$STACK_OPERATION" == "delete" ]; then
    # delete workshop resources
    cd terraform
    echo "Deleting workshop resources..."
    terraform destroy -auto-approve
    
else
    echo "Usage: $0 {create|update|delete}"
    echo "  create/update - Deploy or update workshop resources"
    echo "  delete        - Delete workshop resources"
    exit 1
fi
