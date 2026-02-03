/**
 * Simplified Pinpoint Automation - Uses Your Existing Chrome Session
 * 
 * No login needed! Uses your already logged-in Google account.
 * Just closes all Chrome windows first, then run this.
 * 
 * Run: node pinpoint-logged-in.js
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs').promises;
const FormData = require('form-data');
const http = require('http');
const os = require('os');

// ============ CONFIGURATION ============
const CONFIG = {
    PINPOINT_URL: 'https://journaliststudio.google.com/pinpoint/search?collection=061ce61c9e70bdfd',
    VAULT_API_URL: 'http://localhost:8000',
    DOWNLOAD_DIR: path.resolve(__dirname, 'downloads'),
    DELAY_BETWEEN_DOWNLOADS: 2000,

    // Your Chrome user data directory
    // This is where Chrome stores your logged-in sessions
    CHROME_USER_DATA: path.join(os.homedir(), 'AppData', 'Local', 'Google', 'Chrome', 'User Data')
};

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

async function downloadAllFromPinpoint(page) {
    console.log('\n📥 Navigating to Pinpoint collection...');

    await page.goto(CONFIG.PINPOINT_URL, {
        waitUntil: 'networkidle2',
        timeout: 30000
    });

    console.log('⏳ Waiting for page to load...');
    await sleep(5000);

    console.log('🔍 Scanning for documents...');

    // Try multiple selectors to find documents
    const documentSelectors = [
        'a[href*="/document/"]',
        '.document-item',
        '[data-document-id]',
        'div[role="listitem"] a',
        '.search-result-item'
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
        console.log('\n⚠️  No documents found automatically.');
        console.log('💡 Taking screenshot for manual inspection...');
        await page.screenshot({
            path: path.join(CONFIG.DOWNLOAD_DIR, 'pinpoint-page.png'),
            fullPage: true
        });
        console.log(`📷 Screenshot: ${path.join(CONFIG.DOWNLOAD_DIR, 'pinpoint-page.png')}`);
        console.log('\n💡 MANUAL DOWNLOAD MODE:');
        console.log('   The browser will stay open for 10 minutes.');
        console.log('   Manually download the PDFs, they will be saved to the downloads folder.');
        console.log('   Then this script will upload them automatically!\n');
        await sleep(600000); // 10 minutes for manual download
        return [];
    }

    console.log(`\n📄 Downloading ${documents.length} documents...\n`);

    for (let i = 0; i < documents.length; i++) {
        try {
            console.log(`[${i + 1}/${documents.length}] Processing document...`);

            // Click document
            await documents[i].click();
            await sleep(3000);

            // Look for download button
            const downloadButtonSelectors = [
                'button[aria-label*="Download"]',
                'button[aria-label*="download"]',
                '[data-action="download"]',
                'a[download]'
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
                console.log('  ⚠️  Download button not found');
            }

            // Go back
            await page.goBack({ waitUntil: 'networkidle2' });
            await sleep(1000);

            // Re-query documents
            documents = await page.$$(usedSelector);

        } catch (error) {
            console.log(`  ❌ Error: ${error.message}`);
        }
    }

    // Get downloaded files
    await sleep(2000);
    const files = await fs.readdir(CONFIG.DOWNLOAD_DIR);
    const pdfFiles = files.filter(f => f.endsWith('.pdf'));

    console.log(`\n✓ Found ${pdfFiles.length} PDFs in download directory`);
    return pdfFiles.map(f => path.join(CONFIG.DOWNLOAD_DIR, f));
}

// ============ VAULT UPLOAD ============

async function uploadToVault(filePaths) {
    if (filePaths.length === 0) {
        console.log('\n⚠️  No files to upload');
        return { uploaded: [], errors: [] };
    }

    console.log(`\n📤 Uploading ${filePaths.length} files to Vault...\n`);

    const uploadUrl = `${CONFIG.VAULT_API_URL}/admin/upload-documents`;
    const results = { uploaded: [], errors: [] };

    for (let i = 0; i < filePaths.length; i++) {
        const filePath = filePaths[i];
        const fileName = path.basename(filePath);

        console.log(`[${i + 1}/${filePaths.length}] Uploading: ${fileName}`);

        try {
            const form = new FormData();
            const fileStream = require('fs').createReadStream(filePath);
            form.append('files', fileStream, fileName);

            const result = await new Promise((resolve, reject) => {
                const request = http.request(uploadUrl, {
                    method: 'POST',
                    headers: form.getHeaders()
                }, (response) => {
                    let data = '';
                    response.on('data', chunk => data += chunk);
                    response.on('end', () => {
                        try {
                            if (response.statusCode === 200) {
                                resolve(JSON.parse(data));
                            } else {
                                reject(new Error(`HTTP ${response.statusCode}`));
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
                const pages = result.uploaded[0]?.pages || 0;
                console.log(`  ✓ Success (${pages} pages)`);
                results.uploaded.push(fileName);
            } else if (result.errors?.length > 0) {
                console.log(`  ⚠️  ${result.errors[0]}`);
                results.errors.push({ file: fileName, error: result.errors[0] });
            }

            await sleep(500);

        } catch (error) {
            console.log(`  ❌ ${error.message}`);
            results.errors.push({ file: fileName, error: error.message });
        }
    }

    return results;
}

// ============ MAIN ============

async function main() {
    console.log('🚀 Pinpoint Automation (Using Existing Login)\n');
    console.log('='.repeat(60));
    console.log('💡 This uses your existing Google Chrome login');
    console.log('💡 Make sure you closed ALL Chrome windows before running!');
    console.log('='.repeat(60));

    await ensureDownloadDirectory();

    console.log('\n🌐 Launching Chrome with your profile...');

    const browser = await puppeteer.launch({
        headless: false,
        defaultViewport: null,
        args: [
            '--start-maximized',
            '--no-sandbox',
            `--user-data-dir=${CONFIG.CHROME_USER_DATA}`,
            '--profile-directory=Default'
        ]
    });

    try {
        const pages = await browser.pages();
        const page = pages[0] || await browser.newPage();

        // Set download behavior
        const client = await page.target().createCDPSession();
        await client.send('Page.setDownloadBehavior', {
            behavior: 'allow',
            downloadPath: CONFIG.DOWNLOAD_DIR
        });

        // Download from Pinpoint
        const downloadedFiles = await downloadAllFromPinpoint(page);

        console.log('\n✓ Download phase complete!');
        await browser.close();

        // Upload to Vault
        const uploadResults = await uploadToVault(downloadedFiles);

        // Summary
        console.log('\n' + '='.repeat(60));
        console.log('✅ AUTOMATION COMPLETE!');
        console.log('='.repeat(60));
        console.log(`📁 Download location: ${CONFIG.DOWNLOAD_DIR}`);
        console.log(`📊 Files found: ${downloadedFiles.length}`);
        console.log(`✅ Uploaded: ${uploadResults.uploaded.length}`);
        console.log(`❌ Failed: ${uploadResults.errors.length}`);

        if (uploadResults.errors.length > 0) {
            console.log('\n⚠️  Errors:');
            uploadResults.errors.forEach(err => {
                console.log(`   - ${err.file}: ${err.error}`);
            });
        }

        console.log('\n🎉 Check your Vault:');
        console.log(`   http://localhost:3000/connections`);
        console.log(`   http://localhost:3000/countries`);
        console.log('='.repeat(60) + '\n');

    } catch (error) {
        console.error('\n❌ ERROR:', error.message);
        console.error(error.stack);
    }
}

main().catch(console.error);
