#!/bin/bash

# Delete ALL comments (both real and fake) via Lambda function
# Usage: ./delete-comments.sh [comment_id]

set -e

LAMBDA_FUNCTION="bot-deception-dev-api"

if [ $# -eq 0 ]; then
    # Delete all comments (both real and fake)
    PAYLOAD='{"httpMethod":"DELETE","path":"/api/comments","headers":{}}'
    echo "Deleting all comments (both real and fake)..."
else
    # Delete specific comment
    COMMENT_ID="$1"
    PAYLOAD="{\"httpMethod\":\"DELETE\",\"path\":\"/api/comments/${COMMENT_ID}\",\"headers\":{}}"
    echo "Deleting comment ID: $COMMENT_ID"
fi

aws lambda invoke \
    --function-name "$LAMBDA_FUNCTION" \
    --payload "$PAYLOAD" \
    --cli-binary-format raw-in-base64-out \
    response.json

echo "Response:"
cat response.json
rm -f response.json
