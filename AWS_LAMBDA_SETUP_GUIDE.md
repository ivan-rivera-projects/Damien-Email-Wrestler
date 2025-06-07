# AWS Lambda Enhancement Setup Guide

## 🎯 Overview

The Damien MCP server can automatically enhance AI analysis using AWS Lambda functions when properly configured. This guide explains how to set up and verify the enhancement.

## 🔧 Configuration Methods

### Method 1: Environment Variables (Recommended for Development)

```bash
# Add to your shell profile (~/.zshrc, ~/.bashrc, etc.)
export AWS_ACCESS_KEY_ID=your_access_key_here
export AWS_SECRET_ACCESS_KEY=your_secret_key_here  
export AWS_DEFAULT_REGION=us-east-1

# Reload your shell or run:
source ~/.zshrc  # or ~/.bashrc
```

### Method 2: AWS Credentials File (Recommended for Production)

```bash
# Create AWS credentials directory
mkdir -p ~/.aws

# Create credentials file
cat > ~/.aws/credentials << EOF
[default]
aws_access_key_id = your_access_key_here
aws_secret_access_key = your_secret_key_here
EOF

# Create config file
cat > ~/.aws/config << EOF
[default]
region = us-east-1
output = json
EOF
```

### Method 3: AWS CLI Configuration

```bash
# Install AWS CLI if not available
# macOS: brew install awscli
# Ubuntu: sudo apt install awscli

# Configure credentials
aws configure
# Enter when prompted:
# AWS Access Key ID: your_access_key_here
# AWS Secret Access Key: your_secret_key_here
# Default region name: us-east-1
# Default output format: json
```

## 🔑 Getting AWS Credentials

### If You Have AWS Account Access:
1. Go to AWS Console → IAM → Users → Your User
2. Security credentials tab → Create access key
3. Choose "Command Line Interface (CLI)"
4. Copy the Access Key ID and Secret Access Key

### Required Permissions:
Your AWS user needs these permissions:
- `lambda:InvokeFunction` (for calling Lambda functions)
- `dynamodb:PutItem`, `dynamodb:Query` (for data storage)
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` (for logging)

## 🧪 Testing Configuration

### 1. Test AWS Credentials
```bash
# Test if AWS credentials work
aws sts get-caller-identity

# Expected output:
{
    "UserId": "AIDACKCEVSQ6C2EXAMPLE",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

### 2. Test Lambda Functions
```bash
# Test individual Lambda functions
aws lambda invoke --function-name damien-email-processor \
  --payload '{"user_id":"test","email_data":{"id":"test123"}}' \
  --region us-east-1 response.json

# Check response
cat response.json
```

### 3. Test MCP Integration
```bash
# Run the integration test
cd /Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler
python3 test_mcp_lambda_integration.py
```

## 🔄 How It Works

### Startup Sequence
1. **MCP Server Starts** → AI Intelligence tools initialize
2. **Lambda Client Init** → Attempts to create boto3 Lambda client
3. **Credential Check** → boto3 automatically detects AWS credentials
4. **Success/Failure** → Sets `self.lambda_client` to LambdaClient or None

### Runtime Behavior

#### ✅ **When AWS Configured (Lambda Enhancement Active)**
```
AI Analysis Request → Standard CLI Analysis → Lambda Enhancement → Merged Results
                                              ↑
                                    85%+ confidence classification
                                    Privacy-safe metadata processing
                                    Real-time insights
```

#### ⚠️ **When AWS Not Configured (Standard Analysis Only)**
```
AI Analysis Request → Standard CLI Analysis → Standard Results
                                              ↑
                                    Pattern detection
                                    Business insights
                                    Rule suggestions
```

### Enhancement Triggers

**Lambda enhancement automatically runs for:**
- `damien_ai_analyze_emails` 
- `damien_ai_analyze_emails_large_scale`
- `damien_ai_analyze_emails_async`

**Lambda enhancement does NOT run for:**
- Basic email operations (list, trash, label)
- Draft management
- Settings operations
- Rule management (unless AI-powered)

## 📊 Monitoring Lambda Enhancement

### Check MCP Server Logs
```bash
# Check if Lambda client initialized successfully
tail -f /Users/ivanrivera/Downloads/AWS/DamienPlatform/damien-email-wrestler/logs/mcp-server.log | grep -i lambda

# Look for these messages:
# ✅ "AWS Lambda client initialized for AI processing"
# ⚠️  "AWS Lambda client not available: [error]"
```

### Check Analysis Results
When Lambda enhancement is active, AI analysis results will include:
```json
{
  "insights": {
    "lambda_enhancement": {
      "enhanced_ai_analysis": true,
      "lambda_processed_emails": 5,
      "average_confidence": 0.85,
      "high_confidence_classifications": 3,
      "processing_method": "hybrid_cli_lambda"
    }
  }
}
```

## 🚨 Troubleshooting

### Common Issues

#### 1. "AWS Lambda client not available"
**Solution:** Check AWS credentials configuration
```bash
aws sts get-caller-identity  # Should return your AWS identity
```

#### 2. "Unable to locate credentials"
**Solution:** Set up credentials using one of the methods above

#### 3. "AccessDenied" errors
**Solution:** Ensure your AWS user has Lambda invoke permissions

#### 4. Lambda functions not found
**Solution:** Verify Lambda functions are deployed in us-east-1:
```bash
aws lambda list-functions --region us-east-1 | grep damien
```

### Debug Mode
To enable detailed logging:
```bash
# Set debug environment variable
export DAMIEN_DEBUG=true

# Restart MCP server
./scripts/stop-all.sh
./scripts/start-all.sh
```

## 💡 Best Practices

### For Development
- Use environment variables for quick testing
- Enable debug logging
- Test with small email samples first

### For Production  
- Use AWS credentials file or IAM roles
- Monitor CloudWatch logs
- Set up CloudWatch alarms for Lambda errors

### Cost Management
- Lambda enhancement only runs on-demand
- No idle costs - pay per request only
- Monitor usage via AWS Cost Explorer

## 🎯 Expected Behavior

### With Lambda Enhancement:
- **Response Time:** 2-4 seconds (includes Lambda processing)
- **Accuracy:** 85%+ confidence for pattern detection
- **Features:** Enhanced classification, rule suggestions, privacy-safe processing
- **Logs:** "Enhanced AI analysis completed with X emails"

### Without Lambda Enhancement:
- **Response Time:** 1-2 seconds (standard CLI analysis)
- **Accuracy:** Standard heuristic-based pattern detection  
- **Features:** All standard AI capabilities
- **Logs:** "Using standard analysis (AWS Lambda not available)"

Both modes provide full functionality - Lambda enhancement simply adds enterprise-grade AI capabilities on top of the existing system.