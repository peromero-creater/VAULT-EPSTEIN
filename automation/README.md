# Pinpoint Automation

Automates downloading documents from Google Journalist Studio Pinpoint and uploading them to the Vault system.

## Quick Start

### 1. Install Dependencies
```bash
cd automation
npm install
```

### 2. Configure Credentials
```bash
# Copy the example file
copy .env.example .env

# Edit .env and add your credentials:
# - GOOGLE_EMAIL: Your Google account email
# - GOOGLE_PASSWORD: Your Google password or App-Specific Password
```

### 3. Run Automation
```bash
npm start
```

## What It Does

1. **Logs into Google** using your credentials
2. **Opens Pinpoint** Epstein Files collection
3. **Downloads all PDFs** from the collection
4. **Uploads to Vault** via the `/admin/upload-documents` API
5. **Reports results** with success/error counts

## Configuration

Edit `.env` file:

```env
# Required
GOOGLE_EMAIL=your-email@gmail.com
GOOGLE_PASSWORD=your-password

# Optional
VAULT_API_URL=http://localhost:8000
HEADLESS_MODE=false
DELAY_BETWEEN_DOWNLOADS=2000
```

## 2-Factor Authentication

If your Google account has 2FA enabled:

**Option 1: App-Specific Password (Recommended)**
1. Go to https://myaccount.google.com/apppasswords
2. Create a new app password
3. Use that password in `.env`

**Option 2: Manual 2FA**
- The script will detect 2FA and pause for 60 seconds
- Complete 2FA in the browser window
- Script continues automatically

## Troubleshooting

### "No documents found"
- Check`downloads/pinpoint-page.png` screenshot
- Pinpoint UI may have changed
- Try manual download and use simple upload

### "Login failed"
- Check email/password in `.env`
- Use App-Specific Password for 2FA accounts
- Check if Google blocked the login (check your email)

### "Upload failed"
- Make sure backend is running: `uvicorn main:app --reload`
- Check `VAULT_API_URL` in `.env`
- Verify `/admin/upload-documents` endpoint is accessible

## Output Example

```
🚀 Pinpoint to Vault Automation
============================================================
✓ Created download directory
🌐 Launching browser...
🔐 Logging into Google...
✓ Logged into Google
📥 Navigating to Pinpoint collection...
✓ Found 52 documents
📄 Processing 52 documents...
  [1/52] Processing document...
    ✓ Download initiated
  [2/52] Processing document...
    ✓ Download initiated
  ...
✓ Downloaded 52 PDF files

📤 Uploading 52 files to Vault...
  [1/52] Uploading: epstein_flight_logs.pdf
    ✓ Uploaded successfully (15 pages extracted)
  [2/52] Uploading: maxwell_deposition.pdf
    ✓ Uploaded successfully (42 pages extracted)
  ...

============================================================
✅ AUTOMATION COMPLETE!
============================================================
📁 Download location: C:\...\automation\downloads
📊 Files downloaded: 52
✅ Successfully uploaded: 52
❌ Failed uploads: 0
============================================================
```

## Files Created

- `downloads/*.pdf` - All downloaded PDFs
- `downloads/pinpoint-page.png` - Screenshot (if documents not found)

## Security Notes

- **Never commit `.env`** - It's in `.gitignore`
- **Use App-Specific Passwords** for 2FA accounts
- **Delete credentials** after use if sharing the code
