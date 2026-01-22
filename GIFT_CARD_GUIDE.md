# 🎁 Gift Card System - Complete Guide

## Overview

Gift cards allow users to redeem API keys without payment. Admin has full control over:
- ✅ Plan type (Free/Basic/Pro)
- ✅ Number of redemptions (1-1000 users)
- ✅ Gift card expiry (when card becomes invalid)
- ✅ **API key expiry** (how long generated keys last)

---

## 🎯 Gift Card Creation (Admin)

### Method 1: Using Bot Command

```
/gift
```

**Bot will ask:**

1. **Select Plan:**
   - 🆓 Free
   - 💎 Basic  
   - ⭐ Pro

2. **Max Uses:**
   - How many people can redeem?
   - Example: `10` = 10 users
   - Range: 1-1000

3. **Gift Card Expiry (Days):**
   - How long is the gift card valid?
   - Example: `30` = card expires in 30 days
   - `0` = Never expires

4. **API Key Expiry (Days):**
   - **NEW!** How long will generated API keys last?
   - Example: `60` = API keys valid for 60 days
   - `0` = Permanent (no expiry)
   - Press Enter = Use default:
     - Free: 7 days
     - Basic/Pro: Permanent

---

## 📝 Examples

### Example 1: Free Trial Gift Card

**Use Case:** Give 100 users a 7-day free trial

```
Admin: /gift

Bot: Select Plan
Admin: Free

Bot: How many users can redeem?
Admin: 100

Bot: Gift card expiry (days, 0=never)?
Admin: 30

Bot: API key expiry (days, 0=permanent, Enter=default)?
Admin: 7

Bot: ✅ Gift Card Created!
     Code: GIFT-AB12-CD34-EF56
     Plan: FREE
     Max Uses: 100
     Card Expires: 30 days
     API Keys Valid: 7 days
```

**Result:**
- Gift card valid for 30 days
- 100 people can redeem
- Each person gets FREE API key valid for 7 days

---

### Example 2: Premium Promo Code

**Use Case:** Marketing campaign - 50 PRO plans for 3 months

```
Admin: /gift
Plan: Pro
Max Uses: 50
Card Expiry: 90 days
API Expiry: 90 days

Result:
Code: GIFT-XY78-ZQ91-MN45
- 50 redemptions
- Card valid 90 days
- Pro API keys valid 90 days
```

---

### Example 3: Lifetime Access Gift

**Use Case:** Reward top 10 contributors with permanent Basic access

```
Admin: /gift
Plan: Basic
Max Uses: 10
Card Expiry: 0 (never expires)
API Expiry: 0 (permanent)

Result:
Code: GIFT-LT99-PM77-VV33
- 10 redemptions
- Card never expires
- Generated API keys are PERMANENT
```

---

### Example 4: Limited Time Offer

**Use Case:** Weekend sale - Unlimited redemptions for 48 hours

```
Admin: /gift
Plan: Basic
Max Uses: 1000
Card Expiry: 2 days
API Expiry: 30 days

Result:
Code: GIFT-WE48-HR72-SL99
- 1000 redemptions
- Card expires in 2 days
- Each key valid 30 days
```

---

## 📊 Gift Card Display Format

### Admin View (`/gifts`):

```
🎁 Gift Card #1
Code: GIFT-AB12-CD34-EF56
Plan: 💎 BASIC
Status: ✅ Active

Usage: 45/100 (45% used)
Card Expiry: ✅ 15 days left
API Key Validity: 30 days

Created: 2026-01-15
Note: Marketing Campaign Q1

[Deactivate] [Delete] [Details]
```

### User View (After Redemption):

```
✅ Gift Redeemed Successfully!

🔑 Your API Key:
sk-xxxxxxxxxxxxxxxxxxxxx

💎 Plan: BASIC
⏰ Valid for: 30 days
📅 Expires: 2026-02-22

Use this key in your API requests!
```

---

## 🎯 Use Cases

### 1. **Free Trials**
```
Plan: Free
Max Uses: Unlimited (1000)
Card Expiry: 90 days
API Expiry: 7 days

Use: Public trial code for marketing
```

### 2. **Contest Winners**
```
Plan: Pro
Max Uses: 3
Card Expiry: Never (0)
API Expiry: 180 days (6 months)

Use: Reward top 3 contest winners
```

### 3. **Partner Codes**
```
Plan: Basic
Max Uses: 50
Card Expiry: 30 days
API Expiry: Permanent (0)

Use: Partnership with another service
```

### 4. **Referral Program**
```
Plan: Basic
Max Uses: 1
Card Expiry: Never
API Expiry: 90 days

Use: Generate unique codes for referrals
```

### 5. **Flash Sales**
```
Plan: Pro
Max Uses: 500
Card Expiry: 24 hours
API Expiry: 30 days

Use: Limited time promotional offer
```

---

## 🔧 Admin Management

### View All Gift Cards
```
/gifts
```

Shows:
- ✅ Active cards
- ❌ Inactive cards
- ⏰ Expired cards
- 📊 Usage statistics

### Deactivate Gift Card
```
Bot: /gifts → [Deactivate] button
```

- Immediately stops redemptions
- Already redeemed keys remain active
- Card shows as ❌ Inactive

### Delete Gift Card
```
Bot: /gifts → [Delete] button
```

- Permanently removes card
- Cannot be recovered
- Already redeemed keys unaffected

### Update API Expiry (Advanced)
```python
# Via database function
db.update_gift_card_api_expiry('GIFT-XXXX-XXXX-XXXX', 60)
# Changes future redemptions to 60-day expiry
```

---

## 📋 Database Structure

### Gift Card Document:

```json
{
  "code": "GIFT-AB12-CD34-EF56",
  "plan": "basic",
  "max_uses": 100,
  "used_count": 45,
  "used_by": [123456, 789012, ...],
  "is_active": true,
  
  "card_expiry": "2026-03-01T00:00:00",  // Gift card expires
  "api_expiry_days": 30,  // Generated API keys valid for 30 days (null = permanent)
  
  "created_by": 5451167865,
  "note": "Marketing Campaign Q1",
  "created_at": "2026-01-15T10:30:00",
  "updated_at": "2026-01-22T15:45:00"
}
```

---

## 🔄 Gift Card Lifecycle

```
1. CREATED
   ↓
   Admin generates gift card
   Code: GIFT-XXXX-XXXX-XXXX
   
2. ACTIVE
   ↓
   Users can redeem
   Usage: 0/100
   
3. IN USE
   ↓
   Users redeeming
   Usage: 45/100
   
4. EXPIRED / FULL / DEACTIVATED
   ↓
   ⏰ Card expiry reached
   ✅ Max uses reached (100/100)
   ❌ Admin deactivated
   
5. ARCHIVED (optional)
   ↓
   Admin deletes permanently
```

---

## ⚡ Advanced Features

### 1. **Bulk Gift Card Generation**

```python
# Generate 100 unique codes for referral program
for i in range(100):
    code = db.create_gift_card(
        plan='basic',
        max_uses=1,
        card_expiry_days=None,  # Never expires
        api_expiry_days=90,     # 90-day keys
        created_by=ADMIN_ID,
        note=f'Referral Code #{i+1}'
    )
    print(code)
```

### 2. **Dynamic Expiry Based on Plan**

```python
expiry_map = {
    'free': 7,      # 7 days
    'basic': 30,    # 30 days
    'pro': None     # Permanent
}

code = db.create_gift_card(
    plan='basic',
    max_uses=50,
    api_expiry_days=expiry_map['basic']
)
```

### 3. **Seasonal Campaigns**

```python
# Black Friday Sale
black_friday = db.create_gift_card(
    plan='pro',
    max_uses=500,
    card_expiry_days=1,     # 24 hours only
    api_expiry_days=365,    # 1 year access
    note='Black Friday 2026'
)

print(f"Black Friday Code: {black_friday}")
```

---

## 📊 Analytics

### Track Gift Card Performance:

```
/gifts → [View Stats]

Gift Card: GIFT-AB12-CD34-EF56

📈 Performance:
- Redemptions: 87/100 (87%)
- Days Active: 15/30
- Avg Redemption: 5.8 per day
- Most Active Day: 2026-01-20 (23 redemptions)

👥 Top Users:
1. @user1 - 150 requests
2. @user2 - 98 requests
3. @user3 - 67 requests

⏰ Expiry Breakdown:
- Active Keys: 62
- Expired Keys: 25
- Avg Key Lifetime: 28 days
```

---

## ❓ FAQ

### Q: Can I change API expiry after creating gift card?
**A:** Yes! Use `db.update_gift_card_api_expiry('CODE', days)`. Only affects future redemptions.

### Q: What happens to redeemed keys if I deactivate gift card?
**A:** Already redeemed API keys remain active. Only new redemptions are blocked.

### Q: Can users redeem multiple gift cards?
**A:** Yes! But they can't have multiple keys of same plan. Free + Basic + Pro = OK.

### Q: What if card expiry passes?
**A:** Card can no longer be redeemed. Already redeemed keys continue working.

### Q: Difference between card expiry and API expiry?
**A:** 
- **Card Expiry**: When gift code stops working
- **API Expiry**: How long generated keys last after redemption

### Q: Can I make API keys permanent?
**A:** Yes! Set `api_expiry_days=0` or `None` when creating gift card.

### Q: How to give someone lifetime access?
**A:** 
```
Card Expiry: 0 (never)
API Expiry: 0 (permanent)
Max Uses: 1
```

---

## 🚀 Quick Reference

| Setting | Value | Result |
|---------|-------|--------|
| `api_expiry_days=7` | 7 | Keys expire in 7 days |
| `api_expiry_days=30` | 30 | Keys expire in 30 days |
| `api_expiry_days=0` | 0 | Keys never expire (permanent) |
| `api_expiry_days=None` | None | Default (7 for free, permanent for premium) |
| `card_expiry_days=30` | 30 | Gift card valid 30 days |
| `card_expiry_days=0` | 0 | Gift card never expires |
| `max_uses=1` | 1 | Single use code |
| `max_uses=1000` | 1000 | Unlimited (practically) |

---

## 🎨 Best Practices

1. **Short Card Expiry, Long API Expiry**
   - Creates urgency to redeem
   - Users get long-term access
   - Example: 7-day card, 90-day keys

2. **Track Campaign Performance**
   - Add descriptive notes
   - Monitor redemption rates
   - Adjust strategy based on data

3. **Limited Redemptions for Premium**
   - Prevents abuse
   - Creates exclusivity
   - Example: Max 10 for Pro plans

4. **Permanent Keys for Loyalty**
   - Reward long-term users
   - No expiry = best perk
   - Use sparingly

5. **Seasonal Codes**
   - Holiday campaigns
   - Limited time boosts engagement
   - Clear expiry dates

---

## 📞 Support

For issues or questions:
- Admin Telegram: `5451167865`
- Command: `/admin`
- Documentation: This guide!

---

**Happy Gift Carding! 🎁**
