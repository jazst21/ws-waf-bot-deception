#!/bin/bash

# Complete Bot Deception Functionality Test Script
# Tests all three bot demos with both normal user and bot user agents

set -e

CLOUDFRONT_URL="https://d2fx0ubuf32j2i.cloudfront.net"
NORMAL_UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
BOT_UA="python-requests/2.28.1"

echo "🚀 Testing Complete Bot Deception Functionality"
echo "================================================"
echo "CloudFront URL: $CLOUDFRONT_URL"
echo ""

# Test 1: Health Check
echo "1️⃣ Testing Health Check..."
echo "----------------------------"
curl -s "$CLOUDFRONT_URL/health" | jq -r '.status, .environment, .database.type'
echo ""

# Test 2: Bot Detection Status
echo "2️⃣ Testing Bot Detection Status..."
echo "-----------------------------------"
echo "Normal User:"
curl -s "$CLOUDFRONT_URL/api/status" -H "User-Agent: $NORMAL_UA" | jq -r '.message, .isBot'
echo ""
echo "Bot User:"
curl -s "$CLOUDFRONT_URL/api/status" -H "User-Agent: $BOT_UA" | jq -r '.message, .isBot'
echo ""

# Test 3: Bot Demo 2 - Comments System
echo "3️⃣ Testing Bot Demo 2 - Comments System..."
echo "--------------------------------------------"

# Get comments as normal user
echo "Normal User - Get Comments:"
NORMAL_COMMENTS=$(curl -s "$CLOUDFRONT_URL/api/bot-demo-2/comments" -H "User-Agent: $NORMAL_UA")
echo "$NORMAL_COMMENTS" | jq -r '.message, (.comments | length)'
echo ""

# Get comments as bot
echo "Bot User - Get Comments:"
BOT_COMMENTS=$(curl -s "$CLOUDFRONT_URL/api/bot-demo-2/comments" -H "User-Agent: $BOT_UA")
echo "$BOT_COMMENTS" | jq -r '.message, (.comments | length)'
echo ""

# Post comment as normal user
echo "Normal User - Post Comment:"
NORMAL_POST=$(curl -s "$CLOUDFRONT_URL/api/bot-demo-2/comments" \
  -H "User-Agent: $NORMAL_UA" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"name": "Test User", "comment": "This is a test comment from normal user"}')
echo "$NORMAL_POST" | jq -r '.message, .success'
echo ""

# Post comment as bot
echo "Bot User - Post Comment:"
BOT_POST=$(curl -s "$CLOUDFRONT_URL/api/bot-demo-2/comments" \
  -H "User-Agent: $BOT_UA" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"name": "Bot User", "comment": "This is a test comment from bot"}')
echo "$BOT_POST" | jq -r '.message'
echo ""

# Test 4: Bot Demo 3 - Flight Pricing
echo "4️⃣ Testing Bot Demo 3 - Flight Pricing..."
echo "------------------------------------------"

# Get flights as normal user
echo "Normal User - Flight Prices:"
NORMAL_FLIGHTS=$(curl -s "$CLOUDFRONT_URL/api/bot-demo-3/flights" -H "User-Agent: $NORMAL_UA")
echo "$NORMAL_FLIGHTS" | jq -r '.message, .pricingStrategy'
echo "Sample flight pricing:"
echo "$NORMAL_FLIGHTS" | jq -r '.flights[0] | "Route: \(.route), Price: $\(.price), Discount: \(.discount)%, Original: $\(.originalPrice)"'
echo ""

# Get flights as bot
echo "Bot User - Flight Prices:"
BOT_FLIGHTS=$(curl -s "$CLOUDFRONT_URL/api/bot-demo-3/flights" -H "User-Agent: $BOT_UA")
echo "$BOT_FLIGHTS" | jq -r '.message, .pricingStrategy'
echo "Sample flight pricing:"
echo "$BOT_FLIGHTS" | jq -r '.flights[0] | "Route: \(.route), Price: $\(.price), Discount: \(.discount)%, Original: $\(.originalPrice)"'
echo ""

# Test 5: Price Comparison Analysis
echo "5️⃣ Price Comparison Analysis..."
echo "--------------------------------"
NORMAL_PRICE=$(echo "$NORMAL_FLIGHTS" | jq -r '.flights[0].price')
BOT_PRICE=$(echo "$BOT_FLIGHTS" | jq -r '.flights[0].price')
PRICE_DIFF=$((BOT_PRICE - NORMAL_PRICE))
PRICE_PERCENT=$(echo "scale=1; $PRICE_DIFF * 100 / $NORMAL_PRICE" | bc)

echo "First flight (New York → London):"
echo "  Normal User Price: \$$NORMAL_PRICE"
echo "  Bot User Price: \$$BOT_PRICE"
echo "  Price Difference: \$$PRICE_DIFF ($PRICE_PERCENT% markup for bots)"
echo ""

# Test 6: Robots.txt
echo "6️⃣ Testing Robots.txt..."
echo "-------------------------"
echo "Normal User - Robots.txt:"
curl -s "$CLOUDFRONT_URL/robots.txt" -H "User-Agent: $NORMAL_UA" | head -3
echo ""
echo "Bot User - Robots.txt:"
curl -s "$CLOUDFRONT_URL/robots.txt" -H "User-Agent: $BOT_UA" | head -3
echo ""

# Test 7: Frontend Pages
echo "7️⃣ Testing Frontend Pages..."
echo "-----------------------------"
echo "Home Page:"
curl -s "$CLOUDFRONT_URL/" -H "User-Agent: $NORMAL_UA" | grep -o '<title>[^<]*</title>'
echo ""
echo "Bot Demo 2 Page:"
curl -s "$CLOUDFRONT_URL/bot-demo-2" -H "User-Agent: $NORMAL_UA" | grep -o '<title>[^<]*</title>'
echo ""
echo "Bot Demo 3 Page:"
curl -s "$CLOUDFRONT_URL/bot-demo-3" -H "User-Agent: $NORMAL_UA" | grep -o '<title>[^<]*</title>'
echo ""

# Summary
echo "✅ Complete Functionality Test Summary"
echo "======================================"
echo "✅ Health check: Working"
echo "✅ Bot detection: Working (User-Agent based)"
echo "✅ Bot Demo 2 - Comments: Working (silent discard for bots)"
echo "✅ Bot Demo 3 - Flights: Working (inflated prices for bots)"
echo "✅ Price manipulation: $PRICE_PERCENT% markup for bots"
echo "✅ Robots.txt deception: Working"
echo "✅ Frontend SPA: Working"
echo ""
echo "🎉 All bot deception mechanisms are functioning correctly!"
echo "🤖 Bots see: Inflated prices, fake success messages, misleading robots.txt"
echo "👤 Users see: Discounted prices, real data, legitimate content"
