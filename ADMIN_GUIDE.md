# 👑 Admin Guide

## Admin Features

Admin Telegram ID: `5451167865`

### Commands

- `/admin` - Open admin panel
- `/start` - Admin welcome with special menu
- `/help` - Admin-specific help

### Admin Panel Features

#### 1. 📊 System Statistics

- Total users
- Total API keys
- Active/expired keys
- Total requests
- Plan distribution (Free/Basic/Pro)

#### 2. 🔑 View All API Keys

- Lists all API keys with:
  - User details
  - Plan type
  - Request count
  - Expiry status
  - Active/inactive status

#### 3. 🔄 Clean Expired Keys

- Automatically deactivates all expired API keys
- Shows count of deactivated keys
- Run periodically to keep database clean

#### 4. 📈 Detailed Statistics

- Per-plan request statistics
- User distribution percentages
- System health status

---

## Free Plan Expiry Management

### Current Settings

**Default Free Plan Expiry:** 7 days

To change this, edit `telegram_bot.py`:

```python
DEFAULT_FREE_EXPIRY_DAYS = 7  # Change this value
```

### How It Works

1. **User creates free API key**
   - Expiry date automatically set to current date + 7 days
   - User sees expiry info in `/myapi`

2. **Automatic expiry checking**
   - When API key is used, gateway automatically checks expiry
   - Expired keys are auto-deactivated
   - User gets "expired" error

3. **Admin cleanup**
   - Admin can manually clean expired keys via "🔄 Clean Expired" button
   - Deactivates all expired keys at once

### Expiry Display Format

- **Active:** `✅ 5 days left (expires 2026-01-29)`
- **Expiring soon:** `⚠️ 12 hours left`
- **Expired:** `⚠️ Expired`
- **No expiry:** `No expiry (Permanent)`

---

## Multiple API Keys Feature

### How It Works

**Users can have multiple API keys:**
- ✅ One Free + One Basic
- ✅ One Free + One Pro
- ✅ One Basic + One Pro
- ✅ All three at once

**Users CANNOT have:**
- ❌ Two Free keys
- ❌ Two Basic keys
- ❌ Two Pro keys

### Database Structure

**Collections:**

1. `users` - Basic user info
   ```json
   {
     "telegram_id": 123456,
     "username": "john",
     "created_at": "2026-01-22T10:00:00"
   }
   ```

2. `api_keys` - Separate API keys
   ```json
   {
     "telegram_id": 123456,
     "api_key": "sk-xxxxx",
     "plan": "free",
     "requests_used": 50,
     "is_active": true,
     "expiry_date": "2026-01-29T10:00:00",
     "created_at": "2026-01-22T10:00:00"
   }
   ```

### Benefits

1. **Flexible for users**
   - Test with free
   - Upgrade to premium without losing free key
   - Use different keys for different projects

2. **Better for business**
   - Users more likely to upgrade
   - Can compare plans side-by-side
   - Free trial doesn't block premium purchase

---

## Admin Tasks

### Daily Tasks

1. **Check system stats**
   ```
   /admin → View statistics
   ```

2. **Clean expired keys (optional)**
   ```
   /admin → Clean Expired
   ```

### Weekly Tasks

1. **Review user growth**
   - Check total users
   - Monitor plan distribution
   - Analyze conversion rate (free → premium)

2. **Monitor API usage**
   - Check total requests
   - Identify heavy users
   - Plan for scaling

### As Needed

1. **Extend/modify expiry** (coming soon)
   - Manually set expiry for specific key
   - Extend free trial for VIP users
   - Remove expiry (make permanent)

2. **Deactivate/activate keys** (coming soon)
   - Temporarily disable abusive users
   - Reactivate after payment issue resolved

---

## Troubleshooting

### User reports "API key expired"

1. Check in admin panel → View All Keys
2. Find user's key and check expiry date
3. Options:
   - Ask user to generate new free key
   - User can upgrade to premium (no expiry)
   - Admin can extend expiry (feature coming soon)

### User can't generate premium key

1. Check if user already has active premium key of that plan
2. If yes, they need to wait for current to expire or contact admin
3. If payment done, manually create key using database

### Too many expired keys cluttering database

1. Run cleanup: `/admin` → Clean Expired
2. Consider running cleanup daily via cron job
3. Set up automatic cleanup (feature coming soon)

---

## Future Admin Features (Roadmap)

- [ ] Manual expiry management for individual keys
- [ ] Broadcast messages to all users
- [ ] User-specific key activation/deactivation
- [ ] Revenue tracking (paid plans)
- [ ] Automated cleanup scheduling
- [ ] API usage analytics charts
- [ ] Export user/key data to CSV
- [ ] Email notifications for expiring keys

---

## Tips

1. **Keep free trial short** (7 days is good)
   - Encourages quick decision
   - Reduces server load
   - Higher conversion rate

2. **Monitor conversion rate**
   - Track how many free users upgrade
   - Optimize pricing based on data

3. **Regular cleanup**
   - Run expired key cleanup weekly
   - Keeps database lean
   - Better performance

4. **User communication**
   - Notify users before expiry
   - Clear upgrade path
   - Responsive support
