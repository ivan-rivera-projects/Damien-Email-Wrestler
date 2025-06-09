"""Test script for DynamoDB operations.

This script tests direct interaction with the DynamoDB table
without going through the FastAPI server.
"""

import boto3
import json
import time
from datetime import datetime, timezone # Added timezone
from decimal import Decimal

# Custom JSON encoder to handle Decimal
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)

# Set up table info
TABLE_NAME = "DamienMCPSessions"
USER_ID = "test_direct_user"
SESSION_ID = "test_direct_session"
REGION = "us-east-1"

# Create test data
context_data = {
    "test": True,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "message": "This is a direct test from the test script"
}

# Create DynamoDB resource
print(f"Creating DynamoDB resource for region {REGION}")
dynamodb = boto3.resource('dynamodb', region_name=REGION)

# Get table reference
print(f"Getting table reference for {TABLE_NAME}")
table = dynamodb.Table(TABLE_NAME)

# Create item
item = {
    'user_id': USER_ID,
    'session_id': SESSION_ID,
    'context_data': context_data,
    'last_updated': datetime.now(timezone.utc).isoformat() + 'Z',
    'ttl': int(time.time()) + 86400  # 24 hours TTL
}

# Write to table
print(f"Writing item to table: {json.dumps(item, indent=2)}")
try:
    response = table.put_item(Item=item)
    print(f"Put item succeeded with response: {response}")
except Exception as e:
    print(f"Error writing to DynamoDB: {e}")
    raise

# Read from table
print(f"Reading item from table with key: user_id={USER_ID}, session_id={SESSION_ID}")
try:
    response = table.get_item(
        Key={
            'user_id': USER_ID,
            'session_id': SESSION_ID
        }
    )
    
    if 'Item' in response:
        print(f"Item found: {json.dumps(response['Item'], indent=2, cls=DecimalEncoder)}")
    else:
        print("Item not found")
except Exception as e:
    print(f"Error reading from DynamoDB: {e}")
    raise

print("Test complete!")
