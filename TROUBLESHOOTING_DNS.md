# Troubleshooting DNS Error for Supabase

## Error: DNS resolution failed for Supabase URL

If you're getting `[Errno 11001] getaddrinfo failed` or "DNS resolution failed", follow these steps:

## Step 1: Check if Supabase Project is Active

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Log in to your account
3. Check if your project `ufrqkstmhislcjjzbxai` is:
   - ✅ **Active** (green status)
   - ❌ **Paused** (free tier projects pause after 7 days of inactivity)
   - ❌ **Deleted** (project no longer exists)

### If Project is Paused:
- Click "Restore" or "Resume" button
- Wait 1-2 minutes for project to restart
- Try the connection again

### If Project is Deleted:
- You need to create a new project
- Update your `.env` file with the new project URL

## Step 2: Verify Project ID

1. In Supabase Dashboard, go to **Settings** → **API**
2. Check the **Project URL** - it should match:
   ```
   https://ufrqkstmhislcjjzbxai.supabase.co
   ```
3. If the project ID is different, update your `.env` file

## Step 3: Test DNS Resolution

### Windows:
```powershell
# Test DNS resolution
nslookup ufrqkstmhislcjjzbxai.supabase.co

# If that fails, try with Google DNS
nslookup ufrqkstmhislcjjzbxai.supabase.co 8.8.8.8

# Flush DNS cache
ipconfig /flushdns
```

### Linux/Mac:
```bash
# Test DNS resolution
dig ufrqkstmhislcjjzbxai.supabase.co

# Or
nslookup ufrqkstmhislcjjzbxai.supabase.co
```

## Step 4: Test in Browser

Try opening this URL in your browser:
```
https://ufrqkstmhislcjjzbxai.supabase.co
```

- ✅ If it loads → DNS works, issue is with Python/network config
- ❌ If it doesn't load → DNS/project issue

## Step 5: Check Network/Firewall

1. **Check Internet Connection**: Ensure you're connected to the internet
2. **Check Firewall**: Windows Firewall or antivirus might be blocking
3. **Check Proxy**: If behind a corporate proxy, configure it
4. **Try Different Network**: Test on mobile hotspot to rule out network issues

## Step 6: Verify .env File

Check your `.env` file in the project root:

```env
# Should be exactly like this (no spaces, correct format)
SUPABASE_URL=https://ufrqkstmhislcjjzbxai.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here
```

Common mistakes:
- ❌ `SUPABASE_URL = https://...` (space around =)
- ❌ `SUPABASE_URL=https://... ` (trailing space)
- ❌ `SUPABASE_URL=ufrqkstmhislcjjzbxai.supabase.co` (missing https://)

## Step 7: Alternative: Use IP Address (Not Recommended)

If DNS continues to fail, you can try using the IP address (temporary workaround):

1. Find the IP address:
   ```powershell
   nslookup ufrqkstmhislcjjzbxai.supabase.co 8.8.8.8
   ```

2. Update `.env`:
   ```env
   SUPABASE_URL=https://[IP_ADDRESS]
   ```

**Note**: This is not recommended as IP addresses can change.

## Step 8: Contact Supabase Support

If none of the above works:
1. Check [Supabase Status Page](https://status.supabase.com/)
2. Contact Supabase Support via dashboard
3. Check Supabase Discord/Community for known issues

## Quick Fix Checklist

- [ ] Project is active in Supabase Dashboard
- [ ] Project ID matches in `.env` file
- [ ] URL starts with `https://`
- [ ] No spaces in `.env` file
- [ ] Internet connection is working
- [ ] DNS resolution works (`nslookup` command)
- [ ] URL loads in browser
- [ ] Firewall/antivirus not blocking
- [ ] Tried flushing DNS cache

## Most Common Solution

**90% of the time**, the issue is:
- **Project is paused** → Go to Supabase Dashboard and resume it
- **Wrong project ID** → Check Settings → API in Supabase Dashboard
