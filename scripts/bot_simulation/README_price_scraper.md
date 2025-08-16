# Flight Price Scraping Bot

The `4_price_scraping_bot.py` script simulates competitive price monitoring by scraping flight pricing data from the pricing-demo-3 page using API interception with beautiful CLI table visualization.

## Features

- 🕷️ **API Response Interception** - Captures flight data from API calls
- ✈️ **Comprehensive flight data collection** (routes, airlines, prices, discounts)
- 🤖 **Bot detection analysis** to understand pricing manipulation
- 📊 **Beautiful CLI table visualization** with formatted output
- 📈 **Statistical analysis** and competitive intelligence
- 💾 **JSON output format** with detailed flight information
- 🔄 **Multiple scraping iterations** for data consistency
- ⚡ **Reliable data extraction** via direct API calls
- 🎯 **Realistic browser simulation** with bot User-Agent

## Usage

### Basic Usage
```bash
# Scrape flight prices with default settings
./4_price_scraping_bot.py

# Scrape with multiple iterations
./4_price_scraping_bot.py --iterations 3

# Run in visible browser mode
./4_price_scraping_bot.py --headless false
```

### Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--url` | From .env | Base website URL |
| `--headless` | true | Run browser in headless mode |
| `--iterations` | 2 | Number of scraping iterations |
| `--delay` | 2.0 | Delay between actions (seconds) |

### Environment Variables (.env)

```bash
URL=https://d3mx9cjq6wwawz.cloudfront.net
```

## CLI Table Visualization

The bot now displays results in beautifully formatted CLI tables:

### Flight Data Table
```
📊 Flight Data (6 unique flights)
========================================================================================================================
│ Route                     │ Airline            │ Departure    │ Arrival      │ Duration   │ Price    │ Discount │
├───────────────────────────┼────────────────────┼──────────────┼──────────────┼────────────┼──────────┼──────────┤
│ New York → London         │ SkyWings           │ 10:30 AM     │ 10:30 PM     │ 7h 0m      │ $1299    │ None     │
│ Los Angeles → Tokyo       │ PacificAir         │ 2:15 PM      │ 5:30 PM (ne  │ 11h 15m    │ $1899    │ None     │
│ Chicago → Paris           │ EuroConnect        │ 8:45 PM      │ 11:20 AM (n  │ 8h 35m     │ $1499    │ None     │
│ Miami → Barcelona         │ Mediterranean Air  │ 11:20 AM     │ 5:45 AM (ne  │ 9h 25m     │ $1699    │ None     │
│ Seattle → Sydney          │ Pacific Rim        │ 10:00 PM     │ 6:30 AM (2   │ 16h 30m    │ $2499    │ None     │
│ Boston → Rome             │ Italian Wings      │ 6:30 PM      │ 9:15 AM (ne  │ 8h 45m     │ $1599    │ None     │
└───────────────────────────┴────────────────────┴──────────────┴──────────────┴────────────┴──────────┴──────────┘
```

### Summary Statistics Table
```
📈 Scraping Summary
============================================================
┌─────────────────────────┬──────────────────────────────┐
│ Metric                  │ Value                        │
├─────────────────────────┼──────────────────────────────┤
│ Total Flights Scraped   │ 18                           │
│ Unique Routes           │ 6                            │
│ Average Price           │ $1749.00                     │
│ Price Range             │ $1299 - $2499                │
│ Bot Detection           │ NOT DETECTED                 │
│ Pricing Strategy        │ UNKNOWN                      │
│ Data Sources            │ API Response Interception    │
│ Success Rate            │ 100%                         │
└─────────────────────────┴──────────────────────────────┘
```

### Route Analysis Table
```
🛫 Route Price Analysis
================================================================================
┌─────────────────────────────┬──────────────┬──────────────┐
│ Route                       │ Avg Price    │ Occurrences  │
├─────────────────────────────┼──────────────┼──────────────┤
│ Boston → Rome               │ $   1599.00 │          3x │
│ Chicago → Paris             │ $   1499.00 │          3x │
│ Los Angeles → Tokyo         │ $   1899.00 │          3x │
│ Miami → Barcelona           │ $   1699.00 │          3x │
│ New York → London           │ $   1299.00 │          3x │
│ Seattle → Sydney            │ $   2499.00 │          3x │
└─────────────────────────────┴──────────────┴──────────────┘
```

## How It Works

### 1. API Response Interception
- **Monitors** network traffic for `/api/pricing-demo-3/flights` calls
- **Captures** JSON responses automatically
- **Extracts** complete flight data with pricing strategy

### 2. Active API Triggering
- **Clicks** refresh button to trigger API calls
- **Makes** direct API requests to flight endpoint
- **Ensures** data collection even if page doesn't load properly

### 3. Bot Detection Analysis
- **Identifies** if bot detection is active
- **Analyzes** pricing strategy (inflated vs discounted)
- **Compares** bot prices vs user prices

## Scraped Data Structure

```json
{
  "timestamp": "2025-08-13T07:32:47.123456",
  "total_flights": 18,
  "unique_flights": 6,
  "bot_detected": false,
  "flights": [
    {
      "timestamp": "2025-08-13T07:32:47.123456",
      "route": "New York → London",
      "airline": "SkyWings",
      "departure": "10:30 AM",
      "arrival": "10:30 PM",
      "duration": "7h 0m",
      "price": 1299,
      "original_price": 1299,
      "discount": 0,
      "bot_price": null,
      "user_price": null,
      "pricing_strategy": "unknown",
      "is_bot_detected": false,
      "api_message": "Flight data retrieved successfully"
    }
  ]
}
```

## Bot Detection Results

### **Current Status (After Security Fix)**
```
🤖 Bot detection: NOT DETECTED
💰 Average price: $1,749.00
💡 Pricing strategy: UNKNOWN
```

### **Key Findings**
- ❌ **No Detection Revealed**: Bot cannot determine if it was detected
- 💰 **Price Data Collected**: Still captures inflated pricing ($1,749 avg)
- 🚫 **No Strategy Exposed**: Pricing manipulation method hidden
- 📊 **Clean API Responses**: No bot-related metadata leaked

## Flight Routes Monitored

1. **New York → London** (SkyWings) - $1,299
2. **Los Angeles → Tokyo** (PacificAir) - $1,899  
3. **Chicago → Paris** (EuroConnect) - $1,499
4. **Miami → Barcelona** (Mediterranean Air) - $1,699
5. **Seattle → Sydney** (Pacific Rim) - $2,499
6. **Boston → Rome** (Italian Wings) - $1,599

## Business Intelligence Analysis

### **Competitive Pricing Strategy**
- **Bot Deterrent**: Higher prices discourage automated price comparison
- **User Incentive**: Real users see discounted rates to encourage booking
- **Market Protection**: Prevents competitors from easily scraping real prices

### **Anti-Bot Effectiveness**
- **Detection Rate**: Unknown to bot (security through obscurity)
- **Price Manipulation**: Successfully shows inflated prices to bots
- **Revenue Protection**: Maintains competitive advantage

## Example Output

```
🤖 Starting simple flight price scraper...
📍 Target: https://d3mx9cjq6wwawz.cloudfront.net/pricing-demo-3
🔄 Iterations: 1
--------------------------------------------------

🔄 Iteration 1/1
------------------------------
🌐 Navigating to https://d3mx9cjq6wwawz.cloudfront.net/pricing-demo-3...
📡 Captured API response: /api/pricing-demo-3/flights (Status: 200)
🔄 Clicking refresh button to trigger API call...
📡 Captured API response: /api/pricing-demo-3/flights (Status: 200)
🔗 Making direct API call...
✅ Direct API call successful: 200
✅ Found 6 flights in API response
✅ Collected 18 flight records
📊 Sample: New York → London - $1299 (unknown)

[Beautiful CLI Tables Display Here]

💾 Detailed data saved to: flight_prices_20250813_073247.json
📊 Scraped 18 total records (6 unique flights)
```

## Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

## Testing Bot Protection

This scraper validates that:
- ✅ **Anti-bot system** operates in stealth mode (no detection revealed)
- ✅ **Price inflation** successfully deters competitive scraping
- ✅ **API responses** provide no bot-related metadata
- ✅ **Security through obscurity** prevents reverse engineering

The scraper demonstrates effective bot protection by showing inflated prices ($1,749 average) while completely hiding the detection and manipulation mechanisms from potential attackers.
