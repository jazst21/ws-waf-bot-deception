#!/bin/bash

STACK_OPERATION=$1

if [[ "$STACK_OPERATION" == "create" || "$STACK_OPERATION" == "Create" || "$STACK_OPERATION" == "update" ]]; then
    # deploy / update workshop resources
    # Check if terraform is installed, if not, install it
    if ! command -v terraform &> /dev/null; then
        echo "Terraform not found. Installing Terraform..."
        # Download and install Terraform (latest version)
        sudo apt-get update -y
        sudo apt-get install -y wget unzip gnupg software-properties-common
        wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg > /dev/null
        echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
        sudo apt-get update -y
        sudo apt-get install -y terraform
        echo "Terraform installed successfully."
    else
        echo "Terraform is already installed."
    fi
    # Check if AWS CLI v2 is installed, if not, install it
    if ! command -v aws &> /dev/null; then
        echo "AWS CLI not found. Installing AWS CLI v2..."
        TMP_DIR=$(mktemp -d)
        cd $TMP_DIR
        curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
        unzip awscliv2.zip
        sudo ./aws/install
        cd -
        rm -rf $TMP_DIR
        echo "AWS CLI v2 installed successfully."
    else
        echo "AWS CLI is already installed."
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
    echo "Invalid stack operation!"
    exit 1
fi