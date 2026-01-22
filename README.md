# 🤖 Telegram API Seller Bot

## Features

### For Users:
- 🆓 **Free Plan** (7 days trial)
- 💎 **Basic Plan** (₹99/month)
- ⭐ **Pro Plan** (₹299/month)
- 🎁 **Gift Card Redemption**
- 📊 **Multiple API Keys** (Free + Premium)
- 📈 **Usage Statistics**

### For Admin (ID: 5451167865):

#### 👑 Unlimited Powers
- ✅ **All APIs FREE** for admin
- ✅ **Unlimited API Key Creation** (any plan)
- ✅ **Delete Any API Key**
- ✅ **View All Users & Keys**
- ✅ **System Statistics**

#### 🎁 Gift Card System
- **Generate Gift Cards**
  - Choose plan (Free/Basic/Pro)
  - Set max uses (1-1000 users)
  - Set expiry (optional)
  - Add custom note
- **Manage Gift Cards**
  - View all gift cards
  - Track redemptions
  - Deactivate/Delete cards
- **Gift Card Format**: `GIFT-XXXX-XXXX-XXXX`

#### 🔧 Admin Tools
- **Create API Keys**
  - For any user (by Telegram ID)
  - Any plan
  - Custom expiry
  - Unlimited creation
- **Delete API Keys**
  - By API key
  - By user + plan
  - Bulk operations
- **Expiry Management**
  - Set/extend expiry
  - Make permanent
  - Auto-cleanup expired

#### 📊 Analytics
- Total users/keys/requests
- Plan distribution
- Gift card statistics
- Revenue tracking (coming soon)

---

## Commands

### User Commands:
```
/start - Start the bot
/buy - Buy API access
/myapi - View API keys
/usage - Check usage stats
/redeem - Redeem gift card
/features - View all features
/help - Get help
```

### Admin Commands:
```
/admin - Admin panel
/createkey - Create API key for user
/deletekey - Delete API key
/gift - Generate gift card
/gifts - View all gift cards
/stats - System statistics
```

---

## Setup

### 1. Environment Variables

```env
TELEGRAM_BOT_TOKEN=your_bot_token
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
DB_NAME=api_seller
API_BASE_URL=https://your-gateway.onrender.com
```

### 2. Deploy on Render

**Bot Service:**
```
Build: pip install -r requirements.txt
Start: python telegram_bot.py
```

**Gateway Service:**
```
Build: pip install -r requirements.txt
Start: gunicorn api_gateway:app
```

---

## Gift Card System

### How It Works:

1. **Admin Creates Gift Card**
   ```
   /gift
   → Select plan
   → Enter max uses
   → Generated: GIFT-ABCD-1234-WXYZ
   ```

2. **User Redeems**
   ```
   /redeem GIFT-ABCD-1234-WXYZ
   → API key created instantly
   → Gift card use count updated
   ```

3. **Admin Monitors**
   ```
   /gifts
   → See all gift cards
   → Track redemptions
   → Manage active/inactive
   ```

### Gift Card Features:
- ✅ Multi-use (1-1000 redemptions)
- ✅ Expiry dates
- ✅ Plan-specific (Free/Basic/Pro)
- ✅ Usage tracking
- ✅ User redemption history

---

## API Plans

| Feature | Free | Basic | Pro |
|---------|------|-------|-----|
| Price | ₹0 | ₹99/mo | ₹299/mo |
| Validity | 7 days | Monthly | Monthly |
| Requests | 100/hr | Unlimited | Unlimited |
| Languages | 1 | 8+ | 8+ |
| Tone Control | ❌ | ✅ | ✅ |
| Context | ❌ | ✅ | ✅ |
| Analysis | ❌ | ✅ | ✅ |
| Summarization | ❌ | ❌ | ✅ |
| Streaming | ❌ | ❌ | ✅ |
| Support | Community | Email | Priority |

---

## Database Structure

### Collections:

1. **users** - Basic user info
2. **api_keys** - All API keys (multiple per user)
3. **gift_cards** - Gift cards and redemptions

### Indexes:
- `users.telegram_id` (unique)
- `api_keys.api_key` (unique)
- `api_keys.telegram_id`
- `gift_cards.code` (unique)

---

## Security

- ✅ Admin-only access control
- ✅ API key validation
- ✅ Expiry checking
- ✅ Rate limiting (planned)
- ✅ Gift card validation
- ✅ Usage tracking

---

## Roadmap

- [ ] Payment gateway integration (Razorpay)
- [ ] Automated expiry notifications
- [ ] Broadcast messages
- [ ] Revenue analytics
- [ ] CSV export
- [ ] Email notifications
- [ ] Referral system
- [ ] Usage alerts

---

## Support

Contact Admin: Telegram ID `5451167865`

---

## License

MIT License - Feel free to modify and use!
