#!/bin/bash

# Workshop Stack Management Script with S3 Backend Support
# ========================================================
# 
# This script manages the deployment and deletion of workshop infrastructure
# using Terraform with automatic S3 backend configuration for CloudBuild environments.
#
# S3 Backend Features:
# - Automatically creates S3 bucket for state storage
# - Sets up DynamoDB table for state locking
# - Enables versioning and encryption on state bucket
# - Handles resource conflicts automatically through state management
# - Falls back to local state for local development
#
# Usage:
#   ./manage-workshop-stack.sh Create   # Deploy infrastructure
#   ./manage-workshop-stack.sh Delete   # Destroy infrastructure
#   ./manage-workshop-stack.sh create   # Deploy infrastructure (lowercase)
#   ./manage-workshop-stack.sh delete   # Destroy infrastructure (lowercase)
#
# Environment Variables:
#   IS_WORKSHOP_STUDIO_ENV - Set to "yes" to force S3 backend usage
#   CODEBUILD_BUILD_ID     - Automatically detected in CodeBuild
#   CLEANUP_BACKEND        - Set to "true" to cleanup S3 backend resources
#   CLEAN_DEPLOY          - Set to "true" for clean deployment

STACK_OPERATION=$1

# Configuration for S3 backend
TERRAFORM_STATE_BUCKET_PREFIX="terraform-state-workshop"
TERRAFORM_STATE_KEY="workshop/terraform.tfstate"
TERRAFORM_LOCK_TABLE="terraform-state-lock-workshop"

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

# Function to connect to existing S3 backend infrastructure for delete operations
connect_to_existing_backend() {
    echo "🔗 Connecting to existing Terraform S3 backend..."
    
    # Get AWS account ID and region
    local AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
    if [ -z "$AWS_ACCOUNT_ID" ]; then
        echo "❌ Failed to get AWS account ID. Check AWS credentials."
        return 1
    fi
    
    local AWS_REGION=$(aws configure get region 2>/dev/null || echo "us-east-1")
    
    # Create unique bucket name with account ID
    local STATE_BUCKET="${TERRAFORM_STATE_BUCKET_PREFIX}-${AWS_ACCOUNT_ID}-${AWS_REGION}"
    
    echo "📦 Checking for existing S3 backend: $STATE_BUCKET"
    
    # Check if S3 bucket exists
    if ! aws s3api head-bucket --bucket "$STATE_BUCKET" 2>/dev/null; then
        echo "❌ S3 backend bucket $STATE_BUCKET does not exist"
        echo "🔄 Cannot connect to backend, falling back to local state"
        return 1
    fi
    
    # Check if DynamoDB table exists
    if ! aws dynamodb describe-table --table-name "$TERRAFORM_LOCK_TABLE" --region "$AWS_REGION" >/dev/null 2>&1; then
        echo "⚠️  Warning: DynamoDB lock table $TERRAFORM_LOCK_TABLE does not exist"
        echo "🔄 Proceeding without state locking"
    fi
    
    # Export variables for use in backend configuration
    export TF_STATE_BUCKET="$STATE_BUCKET"
    export TF_STATE_KEY="$TERRAFORM_STATE_KEY"
    export TF_LOCK_TABLE="$TERRAFORM_LOCK_TABLE"
    export TF_REGION="$AWS_REGION"
    
    echo "✅ Connected to existing Terraform backend"
    echo "   Bucket: $STATE_BUCKET"
    echo "   Key: $TERRAFORM_STATE_KEY"
    echo "   Lock Table: $TERRAFORM_LOCK_TABLE"
    echo "   Region: $AWS_REGION"
    
    return 0
}

# Function to create S3 backend infrastructure for Terraform state
create_terraform_backend() {
    echo "🗂️  Setting up Terraform S3 backend infrastructure..."
    
    # Get AWS account ID and region
    local AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
    if [ -z "$AWS_ACCOUNT_ID" ]; then
        echo "❌ Failed to get AWS account ID. Check AWS credentials."
        return 1
    fi
    
    local AWS_REGION=$(aws configure get region 2>/dev/null || echo "us-east-1")
    
    # Create unique bucket name with account ID
    local STATE_BUCKET="${TERRAFORM_STATE_BUCKET_PREFIX}-${AWS_ACCOUNT_ID}-${AWS_REGION}"
    
    echo "📦 Creating S3 bucket for Terraform state: $STATE_BUCKET"
    
    # Create S3 bucket for state storage
    if aws s3api head-bucket --bucket "$STATE_BUCKET" 2>/dev/null; then
        echo "✅ S3 bucket $STATE_BUCKET already exists"
    else
        echo "🆕 Creating S3 bucket $STATE_BUCKET"
        if [ "$AWS_REGION" = "us-east-1" ]; then
            aws s3api create-bucket --bucket "$STATE_BUCKET" || {
                echo "❌ Failed to create S3 bucket"
                return 1
            }
        else
            aws s3api create-bucket --bucket "$STATE_BUCKET" --region "$AWS_REGION" \
                --create-bucket-configuration LocationConstraint="$AWS_REGION" || {
                echo "❌ Failed to create S3 bucket"
                return 1
            }
        fi
        
        # Enable versioning
        echo "🔄 Enabling versioning on S3 bucket..."
        aws s3api put-bucket-versioning --bucket "$STATE_BUCKET" \
            --versioning-configuration Status=Enabled || {
            echo "⚠️  Warning: Failed to enable versioning"
        }
        
        # Enable server-side encryption
        echo "🔐 Enabling encryption on S3 bucket..."
        aws s3api put-bucket-encryption --bucket "$STATE_BUCKET" \
            --server-side-encryption-configuration '{
                "Rules": [{
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }]
            }' || {
            echo "⚠️  Warning: Failed to enable encryption"
        }
        
        # Block public access
        echo "🚫 Blocking public access on S3 bucket..."
        aws s3api put-public-access-block --bucket "$STATE_BUCKET" \
            --public-access-block-configuration \
            BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true || {
            echo "⚠️  Warning: Failed to block public access"
        }
        
        echo "✅ S3 bucket $STATE_BUCKET created and configured"
    fi
    
    # Create DynamoDB table for state locking
    echo "🔒 Creating DynamoDB table for state locking: $TERRAFORM_LOCK_TABLE"
    
    if aws dynamodb describe-table --table-name "$TERRAFORM_LOCK_TABLE" --region "$AWS_REGION" 2>/dev/null >/dev/null; then
        echo "✅ DynamoDB table $TERRAFORM_LOCK_TABLE already exists"
    else
        echo "🆕 Creating DynamoDB table $TERRAFORM_LOCK_TABLE"
        aws dynamodb create-table \
            --table-name "$TERRAFORM_LOCK_TABLE" \
            --attribute-definitions AttributeName=LockID,AttributeType=S \
            --key-schema AttributeName=LockID,KeyType=HASH \
            --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
            --region "$AWS_REGION" || {
            echo "❌ Failed to create DynamoDB table"
            return 1
        }
        
        # Wait for table to be active
        echo "⏳ Waiting for DynamoDB table to be active..."
        aws dynamodb wait table-exists --table-name "$TERRAFORM_LOCK_TABLE" --region "$AWS_REGION" || {
            echo "⚠️  Warning: Timeout waiting for DynamoDB table"
        }
        echo "✅ DynamoDB table $TERRAFORM_LOCK_TABLE created"
    fi
    
    # Export variables for use in backend configuration
    export TF_STATE_BUCKET="$STATE_BUCKET"
    export TF_STATE_KEY="$TERRAFORM_STATE_KEY"
    export TF_LOCK_TABLE="$TERRAFORM_LOCK_TABLE"
    export TF_REGION="$AWS_REGION"
    
    echo "✅ Terraform backend infrastructure ready"
    echo "   Bucket: $STATE_BUCKET"
    echo "   Key: $TERRAFORM_STATE_KEY"
    echo "   Lock Table: $TERRAFORM_LOCK_TABLE"
    echo "   Region: $AWS_REGION"
    
    return 0
}

# Function to configure Terraform backend
configure_terraform_backend() {
    echo "⚙️  Configuring Terraform backend..."
    
    # Create backend configuration file
    # Note: dynamodb_table is the correct parameter for S3 backend state locking
    # The deprecation warning may be from a different context or Terraform version
    cat > backend.tf << EOF
terraform {
  backend "s3" {
    bucket         = "$TF_STATE_BUCKET"
    key            = "$TF_STATE_KEY"
    region         = "$TF_REGION"
    dynamodb_table = "$TF_LOCK_TABLE"
    encrypt        = true
  }
}
EOF
    
    echo "✅ Backend configuration created in backend.tf"
    cat backend.tf
}

# Function to initialize Terraform with backend
initialize_terraform_with_backend() {
    echo "🚀 Initializing Terraform with S3 backend..."
    
    # Validate required variables
    if [ -z "$TF_STATE_BUCKET" ] || [ -z "$TF_STATE_KEY" ] || [ -z "$TF_REGION" ] || [ -z "$TF_LOCK_TABLE" ]; then
        echo "❌ Missing required backend configuration variables:"
        echo "   TF_STATE_BUCKET: '$TF_STATE_BUCKET'"
        echo "   TF_STATE_KEY: '$TF_STATE_KEY'"
        echo "   TF_REGION: '$TF_REGION'"
        echo "   TF_LOCK_TABLE: '$TF_LOCK_TABLE'"
        echo "🔄 Falling back to local backend..."
        rm -f backend.tf
        terraform init
        return 1
    fi
    
    echo "📋 Backend configuration:"
    echo "   Bucket: $TF_STATE_BUCKET"
    echo "   Key: $TF_STATE_KEY"
    echo "   Region: $TF_REGION"
    echo "   DynamoDB Table: $TF_LOCK_TABLE"
    
    # Initialize with backend configuration
    terraform init -backend-config="bucket=$TF_STATE_BUCKET" \
                   -backend-config="key=$TF_STATE_KEY" \
                   -backend-config="region=$TF_REGION" \
                   -backend-config="dynamodb_table=$TF_LOCK_TABLE" \
                   -backend-config="encrypt=true"
    
    if [ $? -eq 0 ]; then
        echo "✅ Terraform initialized successfully with S3 backend"
    else
        echo "❌ Failed to initialize Terraform with S3 backend"
        echo "🔄 Falling back to local backend..."
        
        # Remove backend configuration and initialize locally
        rm -f backend.tf
        terraform init
    fi
}

# Function to clean up S3 backend resources (optional)
cleanup_terraform_backend() {
    echo "🧹 Cleaning up Terraform S3 backend resources..."
    
    local AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    local AWS_REGION=$(aws configure get region || echo "us-east-1")
    local STATE_BUCKET="${TERRAFORM_STATE_BUCKET_PREFIX}-${AWS_ACCOUNT_ID}-${AWS_REGION}"
    
    echo "⚠️  WARNING: This will delete the Terraform state bucket and lock table!"
    echo "   Bucket: $STATE_BUCKET"
    echo "   Lock Table: $TERRAFORM_LOCK_TABLE"
    
    # Only proceed if explicitly requested
    if [ "$CLEANUP_BACKEND" = "true" ]; then
        echo "🗑️  Deleting S3 bucket contents..."
        aws s3 rm "s3://$STATE_BUCKET" --recursive 2>/dev/null || true
        
        echo "🗑️  Deleting S3 bucket..."
        aws s3api delete-bucket --bucket "$STATE_BUCKET" --region "$AWS_REGION" 2>/dev/null || true
        
        echo "🗑️  Deleting DynamoDB lock table..."
        aws dynamodb delete-table --table-name "$TERRAFORM_LOCK_TABLE" --region "$AWS_REGION" 2>/dev/null || true
        
        echo "✅ Backend cleanup completed"
    else
        echo "ℹ️  To cleanup backend resources, set CLEANUP_BACKEND=true"
    fi
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

# Function to install all required binaries
install_required_binaries() {
    echo "🔧 Installing required binaries for operation: $STACK_OPERATION"
    
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
    
    # Check if AWS CLI is installed, if not, install it
    if ! command -v aws &> /dev/null; then
        echo "Installing AWS CLI v2..."
        TMP_DIR=$(mktemp -d)
        cd $TMP_DIR
        
        # Detect architecture and download appropriate version
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
    if ! command -v node &> /dev/null; then
        echo "Installing Node.js..."
        install_nodejs
        echo "Node.js installed successfully."
    else
        echo "Node.js is already installed."
        node --version
        npm --version
    fi
    
    echo "✅ All required binaries are ready"
}

# Main execution logic
echo "🚀 Starting workshop stack operation: $STACK_OPERATION"

# Install binaries for deployment operations only
if [[ "$STACK_OPERATION" == "create" || "$STACK_OPERATION" == "Create" || 
      "$STACK_OPERATION" == "update" || "$STACK_OPERATION" == "delete" || 
      "$STACK_OPERATION" == "Delete" ]]; then
    
    install_required_binaries
    
else
    echo "❌ Invalid operation: $STACK_OPERATION"
    echo "Usage: $0 {create|update|delete} [clean]"
    exit 1
fi

# Now handle specific operations
if [[ "$STACK_OPERATION" == "create" || "$STACK_OPERATION" == "Create" || "$STACK_OPERATION" == "update" ]]; then
    # deploy / update workshop resources
    
    cd terraform
    echo "Deploying workshop resources..."
    
    # For CloudBuild environments, set up S3 backend for state management
    if [ "$IS_WORKSHOP_STUDIO_ENV" = "yes" ] || [ ! -z "$CODEBUILD_BUILD_ID" ]; then
        echo "🏗️  CloudBuild environment detected - setting up S3 backend for Terraform state"
        
        # Create S3 backend infrastructure
        create_terraform_backend
        
        # Configure backend
        configure_terraform_backend
        
        # Initialize with S3 backend
        initialize_terraform_with_backend
    else
        echo "🖥️  Local environment detected - using local Terraform state"
        # Initialize Terraform locally
        terraform init
    fi
    
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
        # Standard deployment - S3 backend handles state conflicts automatically
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
    
elif [ "$STACK_OPERATION" == "delete" ] || [ "$STACK_OPERATION" == "Delete" ]; then
    # delete workshop resources
    cd terraform
    echo "Deleting workshop resources..."
    
    # For CloudBuild environments, connect to existing S3 backend for state management
    if [ "$IS_WORKSHOP_STUDIO_ENV" = "yes" ] || [ ! -z "$CODEBUILD_BUILD_ID" ]; then
        echo "🏗️  CloudBuild environment detected - connecting to existing S3 backend"
        
        # Connect to existing S3 backend infrastructure
        if connect_to_existing_backend; then
            # Configure backend
            configure_terraform_backend
            
            # Initialize with S3 backend
            initialize_terraform_with_backend
        else
            echo "⚠️  Could not connect to S3 backend, using local state"
            terraform init
        fi
    else
        echo "🖥️  Local environment detected - using local Terraform state"
        # Initialize Terraform locally
        terraform init
    fi
    
    terraform destroy -auto-approve
    
    # Optionally cleanup S3 backend resources
    if [ "$CLEANUP_BACKEND" = "true" ]; then
        echo ""
        echo "🧹 Cleaning up S3 backend resources..."
        cleanup_terraform_backend
    fi
    
else
    echo "Usage: $0 {create|update|delete} [clean]"
    echo "  create/update - Deploy or update workshop resources"
    echo "  delete        - Delete workshop resources"
    echo "  clean         - Force clean deployment (destroy then create)"
    echo ""
    echo "Examples:"
    echo "  $0 create         # Standard deployment with resource import"
    echo "  $0 create clean   # Clean deployment (destroy existing first)"
    echo "  $0 delete         # Destroy all resources"
    echo ""
    echo "S3 Backend (CloudBuild):"
    echo "  - Automatically enabled in CloudBuild environments"
    echo "  - Creates S3 bucket: terraform-state-workshop-{account-id}-{region}"
    echo "  - Creates DynamoDB table: terraform-state-lock-workshop"
    echo "  - Enables state locking and versioning"
    echo "  - Resolves resource conflicts automatically"
    echo ""
    echo "Environment variables:"
    echo "  CLEAN_DEPLOY=true           # Force clean deployment"
    echo "  IS_WORKSHOP_STUDIO_ENV=yes  # Force S3 backend usage"
    echo "  CLEANUP_BACKEND=true        # Cleanup S3 backend resources on delete"
    exit 1
fi
