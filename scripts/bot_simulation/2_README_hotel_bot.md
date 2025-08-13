# Malicious Hotel Review Bot Simulation

The `3_bot_comment.py` script simulates malicious bot behavior by submitting fake negative hotel reviews to the bot-demo-2 page.

## Features

- 🤖 **Malicious bot simulation** with consistently negative reviews
- ⭐ **Low star ratings only** (1-2 stars to damage reputation)
- 📝 **Fake negative content** designed to harm hotel reputation
- ✅ **Automated form filling** with realistic but harmful review data
- ✅ **Multiple negative review samples** with varied complaint content
- ✅ **Configurable submission count** and timing
- ✅ **Random or sequential** review selection
- ✅ **Environment variable configuration** via .env file
- ✅ **Detailed logging** and success/failure tracking

## Usage

### Basic Usage
```bash
# Submit 5 negative reviews with default settings
./3_bot_comment.py

# Submit 10 negative reviews with random selection
./3_bot_comment.py --iterations 10 --random-reviews

# Run in visible browser mode with slower timing
./3_bot_comment.py --headless false --delay 3
```

### Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--url` | From .env | Base website URL |
| `--headless` | true | Run browser in headless mode |
| `--iterations` | 5 | Number of negative reviews to submit |
| `--delay` | 2 | Delay between actions (seconds) |
| `--timeout` | 30 | Browser timeout (seconds) |
| `--random-reviews` | false | Use random reviews vs sequential |

### Environment Variables (.env)

```bash
URL=https://d3mx9cjq6wwawz.cloudfront.net
HEADLESS=true
ITERATIONS=5
DELAY=2
TIMEOUT=30
```

## Malicious Review Data

The script includes 15 realistic but negative hotel reviews with:
- **Fake names**: John Smith, Sarah Johnson, etc.
- **Low ratings**: Only 1-2 stars
- **Negative complaints**: Poor service, dirty rooms, broken amenities
- **Reputation damage**: Designed to harm hotel's online reputation

### Sample Review Content:
- "Terrible experience! Room was dirty and smelled bad..."
- "Worst hotel stay ever! Air conditioning broken..."
- "Disgusting conditions! Bathroom had mold..."
- "Complete scam! Hidden fees everywhere..."

## What the Malicious Bot Does

1. **Navigates** to `/bot-demo-2` page
2. **Fills name field** with fake reviewer name
3. **Selects low star rating** (1-2 stars only)
4. **Enters negative review text** designed to damage reputation
5. **Submits the form** and waits for response
6. **Repeats** for specified number of iterations
7. **Reports** success/failure statistics

## Expected Bot Detection Behavior

Since this simulates malicious bot activity:
- 🤖 **Form submissions appear successful** to the bot
- 🛡️ **Reviews should be blocked** by WAF bot protection
- 🚫 **Negative reviews filtered out** before reaching real users
- 📊 **Success rate tracking** shows submission attempts vs actual publication
- ✅ **Real users see only legitimate reviews**

## Testing Bot Protection

This script helps test:
- **Rate limiting** - Multiple rapid submissions
- **Content filtering** - Consistently negative sentiment
- **Pattern detection** - Similar review structures
- **Behavioral analysis** - Automated form filling patterns
- **IP reputation** - Repeated malicious activity

## Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

## Example Output

```
🤖 Starting malicious hotel review bot simulation...
📍 Target URL: https://d3mx9cjq6wwawz.cloudfront.net/bot-demo-2
🔄 Negative reviews to submit: 5
⏱️  Delay between actions: 2s
👁️  Headless mode: true
🎲 Random reviews: false
⭐ All reviews will be 1-2 stars with negative content
--------------------------------------------------
🌐 Navigating to https://d3mx9cjq6wwawz.cloudfront.net/bot-demo-2...
📄 Page loaded: TravelBooker - Hotel Reviews
✅ Review form found, starting submissions...
--------------------------------------------------

📝 Submission 1/5
Submitting review by John Smith with 1 stars...
✓ Review submitted successfully by John Smith

📝 Submission 2/5
Submitting review by Sarah Johnson with 2 stars...
✓ Review submitted successfully by Sarah Johnson

==================================================
🏁 Bot simulation completed!
✅ Successful submissions: 5
❌ Failed submissions: 0
📊 Success rate: 100.0%
==================================================
```

## Bot Detection Success Indicators

- **High submission success rate** but **low review publication rate**
- **WAF blocking patterns** in CloudFront logs
- **Rate limiting triggers** after multiple submissions
- **Content filtering** preventing negative reviews from appearing
- **Behavioral detection** identifying automated patterns

This malicious bot simulation helps test the effectiveness of bot detection and content filtering strategies to protect the hotel's online reputation from fake negative reviews.
