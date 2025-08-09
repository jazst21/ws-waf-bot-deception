# Single File Terraform Deployment

This approach builds the SPA, deploys to S3, and provisions all infrastructure with a single `main.tf` file - **no external scripts required**.

## Prerequisites

- ✅ **Terraform** >= 1.0
- ✅ **AWS CLI** configured with credentials
- ✅ **Node.js** >= 18 and **npm** (for frontend build)

## Quick Start

### 1. Use the Enhanced Configuration

```bash
# Copy the enhanced main.tf
cp main-with-spa-build.tf main.tf
cp variables-enhanced.tf variables.tf
cp terraform.tfvars.enhanced terraform.tfvars
```

### 2. Deploy Everything

```bash
# Initialize Terraform
terraform init

# Plan deployment
terraform plan

# Deploy everything (builds SPA + provisions infrastructure)
terraform apply
```

### 3. Access Your Application

```bash
# Get the CloudFront URL
terraform output deployment_urls
```

## What This Does

### 🏗️ **Build Process**
1. **Checks Node.js availability** automatically
2. **Installs npm dependencies** (`npm install`)
3. **Creates production environment** with correct API endpoints
4. **Builds the SPA** (`npm run build`)
5. **Uploads all files to S3** with proper content types and cache headers

### 🚀 **Infrastructure Deployment**
1. **S3 buckets** for frontend and fake pages
2. **Lambda function** for API backend
3. **Application Load Balancer** (internal)
4. **CloudFront distribution** with multiple origins
5. **WAF with bot control** rules
6. **Proper IAM roles and policies**

### 🔄 **Automatic Updates**
- **Frontend rebuilds** when source files change
- **Lambda updates** when handler code changes
- **CloudFront invalidation** after frontend updates
- **Dependency tracking** ensures correct order

## Key Features

### ✅ **Zero External Scripts**
- Everything handled by Terraform
- No bash scripts required
- Cross-platform compatible

### ✅ **Smart Rebuilding**
- Only rebuilds when source files change
- Uses file hashes for change detection
- Efficient incremental updates

### ✅ **Proper Content Types**
- Automatic MIME type detection
- Optimized cache headers
- Immutable assets for performance

### ✅ **Environment Configuration**
- Dynamic API endpoint configuration
- Production-optimized settings
- Template-based environment files

## File Structure

```
terraform/
├── main-with-spa-build.tf     # Enhanced main configuration
├── variables-enhanced.tf       # Variable definitions
├── terraform.tfvars.enhanced  # Example values
├── frontend-env.tpl           # Environment template
└── SINGLE_FILE_DEPLOYMENT.md  # This guide

source/
├── frontend/                  # Vue.js SPA source
│   ├── src/                  # Source files
│   ├── package.json          # Dependencies
│   └── vite.config.js        # Build configuration
└── backend/
    └── lambda-handler.js     # Lambda function code
```

## Deployment Commands

### Full Deployment
```bash
terraform apply
```

### Frontend Only Update
```bash
# Terraform detects changes automatically
terraform apply -target=aws_s3_object.frontend_files
terraform apply -target=null_resource.cloudfront_invalidation
```

### Backend Only Update
```bash
terraform apply -target=aws_lambda_function.api
```

### Check Build Status
```bash
terraform output nodejs_info
```

## Customization

### Custom Domain
```hcl
# In terraform.tfvars
domain_names = ["example.com"]
acm_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/..."
```

### Performance Tuning
```hcl
# In terraform.tfvars
lambda_memory_size = 1024
lambda_timeout = 60
cloudfront_price_class = "PriceClass_All"
```

### Environment Variables
```hcl
# Modify frontend-env.tpl for additional variables
VITE_CUSTOM_API_KEY=${custom_api_key}
VITE_FEATURE_FLAG=${feature_flag}
```

## Troubleshooting

### Node.js Not Found
```bash
# Check Node.js availability
terraform output nodejs_info

# Install Node.js if needed
# macOS: brew install node
# Ubuntu: sudo apt install nodejs npm
```

### Build Failures
```bash
# Check frontend directory
ls -la ../source/frontend/

# Manual build test
cd ../source/frontend
npm install
npm run build
```

### Permission Issues
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify IAM permissions for:
# - S3 bucket operations
# - CloudFront management
# - Lambda deployment
# - WAF configuration
```

## Advantages Over Script-Based Approach

| Feature | Script Approach | Single File Approach |
|---------|----------------|---------------------|
| **Dependencies** | Bash, AWS CLI, Node.js | Terraform + Node.js |
| **Cross-Platform** | Unix/Linux only | Windows/Mac/Linux |
| **State Management** | Manual coordination | Terraform state |
| **Rollback** | Manual process | `terraform apply` previous |
| **Change Detection** | Time-based | Content hash-based |
| **Parallel Execution** | Sequential | Terraform dependency graph |
| **Error Handling** | Custom bash logic | Terraform built-in |

## Migration from Script Approach

1. **Backup current state**:
   ```bash
   terraform state pull > backup.tfstate
   ```

2. **Import existing resources** (if needed):
   ```bash
   terraform import aws_s3_bucket.frontend your-bucket-name
   terraform import aws_cloudfront_distribution.main DISTRIBUTION_ID
   ```

3. **Switch to enhanced configuration**:
   ```bash
   cp main-with-spa-build.tf main.tf
   terraform plan  # Review changes
   terraform apply
   ```

This approach provides a **production-ready, maintainable, and scalable** deployment solution that eliminates external script dependencies while providing all the same functionality.
