# Quick Start - Using Existing Login

Since you're already logged into Google, use this simpler version!

## Steps

### 1. Close ALL Chrome Windows
```
Close every Chrome window/tab first!
```

### 2. Run the Script
```bash
cd automation
node pinpoint-logged-in.js
```

That's it! No credentials needed.

## What It Does

1. Opens Chrome using your existing profile (already logged in)
2. Goes to Pinpoint collection
3. Downloads all PDFs
4. Uploads to Vault
5. Done!

## How It Works

Uses `--user-data-dir` to launch Chrome with your existing login session. Since you're already logged into Google, it skips the login step entirely.

## Troubleshooting

**"Data directory in use"**
- Close ALL Chrome windows (check system tray)
- Make sure no Chrome processes are running

**"Not logged in"**
- The script uses Chrome's Default profile
- Make sure you're logged into Google in Chrome (not Edge/Firefox)

## Manual Fallback

If auto-download doesn't work:
1. Script will pause for 10 minutes
2. Manually download PDFs while browser is open
3. They'll still save to `automation/downloads/`
4. Script will auto-upload them when you're done!
