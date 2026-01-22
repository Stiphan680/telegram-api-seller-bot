# Telegram API Seller Bot

एक complete system जो Telegram के through API keys बेचता है और manage करता है।

## Features

✅ **API Key Generation** - Instant unique API keys
✅ **Usage Tracking** - हर request count होता है
✅ **Multiple Plans** - Free, Basic, Pro plans
✅ **Telegram Integration** - User-friendly bot interface
✅ **MongoDB Database** - Secure data storage
✅ **API Gateway** - Key validation and rate limiting
✅ **Easy Deployment** - Render ready

## System Architecture

```
User → Telegram Bot → Database (MongoDB)
                         ↓
User → API Gateway → Validate Key → Main Chatbot API
```

## Components

### 1. API Gateway (`api_gateway.py`)
- API key validation
- Usage tracking
- Request forwarding to main chatbot
- Rate limiting (optional)

### 2. Telegram Bot (`telegram_bot.py`)
- User onboarding
- API key generation
- Payment handling
- Usage statistics

### 3. Database (`database.py`)
- MongoDB integration
- User management
- API key storage

## Quick Setup

### Prerequisites

1. **MongoDB Database**
   - Create free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
   - Get connection string

2. **Telegram Bot**
   - Create bot with [@BotFather](https://t.me/BotFather)
   - Get bot token

3. **Render Account**
   - Sign up at [Render](https://render.com)

### Installation Steps

#### 1. Clone Repository
```bash
git clone https://github.com/Stiphan680/telegram-api-seller-bot.git
cd telegram-api-seller-bot
```

#### 2. Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
TELEGRAM_BOT_TOKEN=your_bot_token_here
MONGODB_URI=your_mongodb_uri_here
DB_NAME=api_seller
API_BASE_URL=http://localhost:5000
EOF

# Run API Gateway (Terminal 1)
python api_gateway.py

# Run Telegram Bot (Terminal 2)
python telegram_bot.py
```

#### 3. Deploy API Gateway to Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect this GitHub repository
4. Configure:
   - **Name:** `api-seller-gateway`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn api_gateway:app`
   - **Instance Type:** Free

5. Add Environment Variables:
   ```
   MONGODB_URI = your_mongodb_connection_string
   DB_NAME = api_seller
   ```

6. Click **"Create Web Service"**
7. Copy your API URL (e.g., `https://api-seller-gateway.onrender.com`)

#### 4. Deploy Telegram Bot to Render

1. Create another Web Service
2. Same repository
3. Configure:
   - **Name:** `api-seller-bot`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python telegram_bot.py`
   - **Instance Type:** Free

4. Add Environment Variables:
   ```
   TELEGRAM_BOT_TOKEN = your_bot_token
   MONGODB_URI = your_mongodb_connection_string
   DB_NAME = api_seller
   API_BASE_URL = https://api-seller-gateway.onrender.com
   ```

5. Deploy!

## Usage

### For Users (Telegram)

1. Start bot: `/start`
2. Click "Buy API Access"
3. Choose plan (Free/Basic/Pro)
4. Get instant API key
5. Use API key in your applications

### For Developers (API)

**Endpoint:** `POST https://your-api.onrender.com/chat`

**Headers:**
```
Content-Type: application/json
X-API-Key: sk-your-api-key-here
```

**Body:**
```json
{
  "question": "What is artificial intelligence?"
}
```

**Response:**
```json
{
  "success": true,
  "response": "Artificial intelligence is...",
  "usage": {
    "requests_used": 42,
    "plan": "free"
  }
}
```

### Python Example

```python
import requests

url = "https://your-api.onrender.com/chat"
headers = {
    "X-API-Key": "sk-your-api-key",
    "Content-Type": "application/json"
}
data = {"question": "Explain quantum computing"}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

### cURL Example

```bash
curl -X POST https://your-api.onrender.com/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-your-api-key" \
  -d '{"question": "What is machine learning?"}'
```

## Bot Commands

- `/start` - Welcome message और menu
- `/buy` - API access purchase करें
- `/myapi` - अपनी API key देखें
- `/usage` - Usage statistics check करें
- `/plans` - सभी plans देखें
- `/help` - Help और documentation

## Plans

### Free Plan (₹0)
- Instant API key
- Basic support
- Perfect for testing

### Basic Plan (₹99/month)
- Unlimited requests
- Email support
- No rate limits

### Pro Plan (₹299/month)
- Everything in Basic
- Priority support
- Custom features
- Dedicated support

## Database Schema

```javascript
{
  telegram_id: Number,      // Unique Telegram user ID
  username: String,         // Telegram username
  api_key: String,         // Unique API key (sk-...)
  plan: String,            // free/basic/pro
  requests_used: Number,   // Total requests count
  is_active: Boolean,      // Active/Inactive status
  created_at: String,      // ISO timestamp
  updated_at: String       // ISO timestamp
}
```

## API Endpoints

### Gateway Endpoints

- `GET /` - API information
- `POST /chat` - Main chat endpoint (requires API key)
- `POST /validate` - Validate API key
- `GET /usage` - Get usage stats (requires API key)
- `GET /health` - Health check

## Environment Variables

```env
# Required
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=api_seller
API_BASE_URL=https://your-api.onrender.com

# Optional
ADMIN_IDS=123456789,987654321
RATE_LIMIT_FREE=10
RATE_LIMIT_BASIC=100
RATE_LIMIT_PRO=1000
```

## Security Features

- ✅ Unique API keys (32-byte secure tokens)
- ✅ Key validation on every request
- ✅ Usage tracking
- ✅ Plan-based access control
- ✅ Easy key deactivation

## Monetization

### Payment Integration (TODO)

1. **Razorpay** - भारत के लिए best
   ```python
   pip install razorpay
   ```

2. **Stripe** - International payments
   ```python
   pip install stripe
   ```

3. **PayPal** - Global option

## Troubleshooting

### Bot not responding
- Check `TELEGRAM_BOT_TOKEN` in environment variables
- Verify bot is running on Render
- Check Render logs

### API key not working
- Verify MongoDB connection
- Check API Gateway is running
- Validate API key format (starts with `sk-`)

### Database connection failed
- Verify MongoDB URI
- Check network access in MongoDB Atlas
- Whitelist `0.0.0.0/0` in MongoDB Network Access

## Monitoring

```python
# Get total users
users = db.get_all_users()
print(f"Total users: {len(users)}")

# Get usage stats
total_requests = sum(u['requests_used'] for u in users)
print(f"Total requests: {total_requests}")
```

## Future Enhancements

- [ ] Payment gateway integration
- [ ] Admin dashboard
- [ ] Usage analytics
- [ ] Rate limiting per plan
- [ ] Webhook support
- [ ] Custom API endpoints
- [ ] Referral system
- [ ] API key regeneration

## Support

For issues or questions:
- GitHub Issues: [Create Issue](https://github.com/Stiphan680/telegram-api-seller-bot/issues)
- Telegram: @YourUsername

## License

MIT License - Free to use and modify!

---

**Made with ❤️ by Stiphan680**

**Repository:** https://github.com/Stiphan680/telegram-api-seller-bot