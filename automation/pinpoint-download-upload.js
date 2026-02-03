/**
 * Pinpoint to Vault Automation Script
 * 
 * This script automates:
 * 1. Logging into Google Journalist Studio Pinpoint
 * 2. Downloading all documents from the Epstein Files collection
 * 3. Uploading them to Vault system via API
 * 
 * Requirements: Node.js 16+, Puppeteer
 * Install: npm install
 * Configure: Copy .env.example to .env and fill in credentials
 * Run: npm start
 */

require('dotenv').config();
const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs').promises;
const FormData = require('form-data');
const https = require('https');
const http = require('http');

// ============ CONFIGURATION ============
const CONFIG = {
    GOOGLE_EMAIL: process.env.GOOGLE_EMAIL,
    GOOGLE_PASSWORD: process.env.GOOGLE_PASSWORD,
    PINPOINT_URL: process.env.PINPOINT_URL || 'https://journaliststudio.google.com/pinpoint/search?collection=061ce61c9e70bdfd',
    VAULT_API_URL: process.env.VAULT_API_URL || 'http://localhost:8000',
    DOWNLOAD_DIR: path.resolve(__dirname, process.env.DOWNLOAD_DIR || 'downloads'),
    DELAY_BETWEEN_DOWNLOADS: parseInt(process.env.DELAY_BETWEEN_DOWNLOADS) || 2000,
    PAGE_LOAD_TIMEOUT: parseInt(process.env.PAGE_LOAD_TIMEOUT) || 30000,
    HEADLESS_MODE: process.env.HEADLESS_MODE === 'true'
};

// Validate configuration
if (!CONFIG.GOOGLE_EMAIL || !CONFIG.GOOGLE_PASSWORD) {
    console.error('❌ ERROR: GOOGLE_EMAIL and GOOGLE_PASSWORD must be set in .env file');
    console.error('💡 Copy .env.example to .env and fill in your credentials');
    process.exit(1);
}

// ============ HELPER FUNCTIONS ============

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function ensureDownloadDirectory() {
    try {
        await fs.access(CONFIG.DOWNLOAD_DIR);
    } catch {
        await fs.mkdir(CONFIG.DOWNLOAD_DIR, { recursive: true });
        console.log(`✓ Created download directory: ${CONFIG.DOWNLOAD_DIR}`);
    }
}

// ============ PINPOINT FUNCTIONS ============

async function loginToGoogle(page) {
    console.log('🔐 Logging into Google...');

    try {
        await page.goto('https://accounts.google.com/signin', {
            waitUntil: 'networkidle2',
            timeout: CONFIG.PAGE_LOAD_TIMEOUT
        });

        // Enter email
        await page.waitForSelector('input[type="email"]', { visible: true });
        await page.type('input[type="email"]', CONFIG.GOOGLE_EMAIL, { delay: 100 });
        await page.click('#identifierNext');

        // Wait for password field
        await sleep(2000);
        await page.waitForSelector('input[type="password"]', { visible: true, timeout: 10000 });
        await page.type('input[type="password"]', CONFIG.GOOGLE_PASSWORD, { delay: 100 });
        await page.click('#passwordNext');

        // Wait for login to complete
        await sleep(3000);

        // Check if 2FA is required
        const url = page.url();
        if (url.includes('challenge') || url.includes('verification')) {
            console.log('⚠️  2-Factor Authentication detected!');
            console.log('👉 Please complete 2FA in the browser window');
            console.log('⏰ Waiting 60 seconds for manual 2FA completion...');
            await sleep(60000);
        }

        console.log('✓ Logged into Google');
    } catch (error) {
        console.error('❌ Login failed:', error.message);
        throw error;
    }
}

async function downloadAllFromPinpoint(page) {
    console.log('\n📥 Navigating to Pinpoint collection...');

    await page.goto(CONFIG.PINPOINT_URL, {
        waitUntil: 'networkidle2',
        timeout: CONFIG.PAGE_LOAD_TIMEOUT
    });

    await sleep(5000);

    console.log('🔍 Scanning for documents...');

    // Try multiple selectors to find documents
    const documentSelectors = [
        'a[href*="/document/"]',
        '.document-item',
        '[data-document-id]',
        '.search-result-item',
        'div[role="listitem"]'
    ];

    let documents = [];
    let usedSelector = '';

    for (const selector of documentSelectors) {
        try {
            documents = await page.$$(selector);
            if (documents.length > 0) {
                usedSelector = selector;
                console.log(`✓ Found ${documents.length} documents using selector: ${selector}`);
                break;
            }
        } catch (e) {
            continue;
        }
    }

    if (documents.length === 0) {
        console.log('⚠️  No documents found automatically.');
        console.log('💡 Taking a screenshot for debugging...');
        await page.screenshot({ path: path.join(CONFIG.DOWNLOAD_DIR, 'pinpoint-page.png'), fullPage: true });
        console.log(`📷 Screenshot saved to: ${path.join(CONFIG.DOWNLOAD_DIR, 'pinpoint-page.png')}`);
        return [];
    }

    console.log(`\n📄 Processing ${documents.length} documents...\n`);

    const downloadedFiles = [];

    for (let i = 0; i < documents.length; i++) {
        try {
            console.log(`[${i + 1}/${documents.length}] Processing document...`);

            // Click on document
            await documents[i].click();
            await sleep(3000);

            // Look for download button
            const downloadButtonSelectors = [
                'button[aria-label*="Download"]',
                'button[aria-label*="download"]',
                '[data-action="download"]',
                'a[download]',
                'button:has-text("Download")'
            ];

            let downloaded = false;
            for (const selector of downloadButtonSelectors) {
                try {
                    const downloadBtn = await page.$(selector);
                    if (downloadBtn) {
                        await downloadBtn.click();
                        console.log('  ✓ Download initiated');
                        downloaded = true;
                        await sleep(CONFIG.DELAY_BETWEEN_DOWNLOADS);
                        break;
                    }
                } catch (e) {
                    continue;
                }
            }

            if (!downloaded) {
                console.log('  ⚠️  Download button not found, trying alternative methods...');
                // Try keyboard shortcut
                await page.keyboard.press('Control+S');
                await sleep(1000);
            }

            // Go back to list
            await page.goBack({ waitUntil: 'networkidle2' });
            await sleep(1000);

            // Re-query documents (DOM might have changed)
            documents = await page.$$(usedSelector);

        } catch (error) {
            console.log(`  ❌ Error processing document ${i + 1}: ${error.message}`);
        }
    }

    // Get list of downloaded files
    await sleep(2000);
    const files = await fs.readdir(CONFIG.DOWNLOAD_DIR);
    const pdfFiles = files.filter(f => f.endsWith('.pdf'));

    console.log(`\n✓ Downloaded ${pdfFiles.length} PDF files to ${CONFIG.DOWNLOAD_DIR}`);

    return pdfFiles.map(f => path.join(CONFIG.DOWNLOAD_DIR, f));
}

// ============ VAULT UPLOAD FUNCTIONS ============

async function uploadToVault(filePaths) {
    console.log(`\n📤 Uploading ${filePaths.length} files to Vault...`);

    const uploadUrl = `${CONFIG.VAULT_API_URL}/admin/upload-documents`;
    const results = {
        uploaded: [],
        errors: []
    };

    for (let i = 0; i < filePaths.length; i++) {
        const filePath = filePaths[i];
        const fileName = path.basename(filePath);

        console.log(`  [${i + 1}/${filePaths.length}] Uploading: ${fileName}`);

        try {
            const form = new FormData();
            const fileStream = require('fs').createReadStream(filePath);
            form.append('files', fileStream, fileName);

            const result = await new Promise((resolve, reject) => {
                const protocol = uploadUrl.startsWith('https') ? https : http;

                const request = protocol.request(uploadUrl, {
                    method: 'POST',
                    headers: form.getHeaders()
                }, (response) => {
                    let data = '';
                    response.on('data', chunk => data += chunk);
                    response.on('end', () => {
                        try {
                            if (response.statusCode === 200) {
                                const json = JSON.parse(data);
                                resolve(json);
                            } else {
                                reject(new Error(`HTTP ${response.statusCode}: ${data}`));
                            }
                        } catch (e) {
                            reject(e);
                        }
                    });
                });

                request.on('error', reject);
                form.pipe(request);
            });

            if (result.success_count > 0) {
                console.log(`    ✓ Uploaded successfully (${result.uploaded[0].pages} pages extracted)`);
                results.uploaded.push(fileName);
            } else if (result.errors && result.errors.length > 0) {
                console.log(`    ⚠️  ${result.errors[0]}`);
                results.errors.push({ file: fileName, error: result.errors[0] });
            }

            await sleep(500);

        } catch (error) {
            console.log(`    ❌ Upload failed: ${error.message}`);
            results.errors.push({ file: fileName, error: error.message });
        }
    }

    return results;
}

// ============ MAIN EXECUTION ============

async function main() {
    console.log('🚀 Pinpoint to Vault Automation\n');
    console.log('='.repeat(60));

    await ensureDownloadDirectory();

    // Launch browser
    console.log(`\n🌐 Launching browser (headless: ${CONFIG.HEADLESS_MODE})...`);
    const browser = await puppeteer.launch({
        headless: CONFIG.HEADLESS_MODE,
        defaultViewport: null,
        args: ['--start-maximized', '--no-sandbox'],
    });

    try {
        const page = await browser.newPage();

        // Set download behavior
        const client = await page.target().createCDPSession();
        await client.send('Page.setDownloadBehavior', {
            behavior: 'allow',
            downloadPath: CONFIG.DOWNLOAD_DIR
        });

        // Step 1: Login to Google and download from Pinpoint
        await loginToGoogle(page);
        const downloadedFiles = await downloadAllFromPinpoint(page);

        if (downloadedFiles.length === 0) {
            console.log('\n⚠️  No files were downloaded.');
            console.log('💡 Check the screenshot at:', path.join(CONFIG.DOWNLOAD_DIR, 'pinpoint-page.png'));
            console.log('💡 You may need to manually download files from Pinpoint');
            console.log('   Then run the simple upload script (coming soon)');
            await sleep(10000);
            return;
        }

        console.log('\n✓ Download phase complete!');
        await browser.close();

        // Step 2: Upload files to Vault via API
        const uploadResults = await uploadToVault(downloadedFiles);

        // Print final summary
        console.log('\n' + '='.repeat(60));
        console.log('✅ AUTOMATION COMPLETE!');
        console.log('='.repeat(60));
        console.log(`📁 Download location: ${CONFIG.DOWNLOAD_DIR}`);
        console.log(`📊 Files downloaded: ${downloadedFiles.length}`);
        console.log(`✅ Successfully uploaded: ${uploadResults.uploaded.length}`);
        console.log(`❌ Failed uploads: ${uploadResults.errors.length}`);

        if (uploadResults.errors.length > 0) {
            console.log('\n⚠️  Upload Errors:');
            uploadResults.errors.forEach(err => {
                console.log(`   - ${err.file}: ${err.error}`);
            });
        }

        console.log('\n🎉 Check your Vault at:');
        console.log(`   - Admin: ${CONFIG.VAULT_API_URL}/admin/upload`);
        console.log(`   - Search: ${CONFIG.VAULT_API_URL.replace(':8000', ':3000')}/search`);
        console.log(`   - Connections: ${CONFIG.VAULT_API_URL.replace(':8000', ':3000')}/connections`);
        console.log('='.repeat(60) + '\n');

    } catch (error) {
        console.error('\n❌ FATAL ERROR:', error.message);
        console.error(error.stack);
        process.exit(1);
    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

// Run the script
if (require.main === module) {
    main().catch(error => {
        console.error('Fatal error:', error);
        process.exit(1);
    });
}

module.exports = { main, uploadToVault };
