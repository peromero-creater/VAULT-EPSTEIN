/**
 * Pinpoint Manual Download Helper
 * 
 * Since Pinpoint has 4,078+ documents with complex UI,
 * this script helps you download them manually and auto-uploads to Vault.
 * 
 * Run: node pinpoint-manual-helper.js
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs').promises;
const FormData = require('form-data');
const http = require('http');
const os = require('os');

const CONFIG = {
    PINPOINT_URL: 'https://journaliststudio.google.com/pinpoint/search?collection=061ce61c9e70bdfd',
    VAULT_API_URL: 'http://localhost:8000',
    DOWNLOAD_DIR: path.resolve(__dirname, 'downloads'),
    CHROME_USER_DATA: path.join(os.homedir(), 'AppData', 'Local', 'Google', 'Chrome', 'User Data')
};

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function ensureDownloadDirectory() {
    try {
        await fs.access(CONFIG.DOWNLOAD_DIR);
    } catch {
        await fs.mkdir(CONFIG.DOWNLOAD_DIR, { recursive: true });
        console.log(`✓ Created: ${CONFIG.DOWNLOAD_DIR}`);
    }
}

async function uploadToVault(filePaths) {
    if (filePaths.length === 0) {
        console.log('\n⚠️  No files to upload yet');
        return { uploaded: [], errors: [] };
    }

    console.log(`\n📤 Uploading ${filePaths.length} files to Vault...\n`);

    const uploadUrl = `${CONFIG.VAULT_API_URL}/admin/upload-documents`;
    const results = { uploaded: [], errors: [] };

    for (let i = 0; i < filePaths.length; i++) {
        const filePath = filePaths[i];
        const fileName = path.basename(filePath);

        console.log(`[${i + 1}/${filePaths.length}] ${fileName}`);

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
                console.log(`  ✓ Uploaded (${pages} pages)`);
                results.uploaded.push(fileName);
            } else if (result.errors?.length > 0) {
                console.log(`  ⚠️  ${result.errors[0]}`);
                results.errors.push({ file: fileName, error: result.errors[0] });
            }

            await sleep(300);

        } catch (error) {
            console.log(`  ❌ ${error.message}`);
            results.errors.push({ file: fileName, error: error.message });
        }
    }

    return results;
}

async function main() {
    console.log('🚀 Pinpoint Manual Download Helper\n');
    console.log('='.repeat(60));
    console.log('📊 Collection has ~4,078 documents!');
    console.log('💡 This script will help you download and upload them');
    console.log('='.repeat(60));

    await ensureDownloadDirectory();

    console.log('\n🌐 Opening Pinpoint in Chrome...');
    console.log('💡 Downloads will be saved to:', CONFIG.DOWNLOAD_DIR);

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

        // Set download location
        const client = await page.target().createCDPSession();
        await client.send('Page.setDownloadBehavior', {
            behavior: 'allow',
            downloadPath: CONFIG.DOWNLOAD_DIR
        });

        // Go to Pinpoint
        await page.goto(CONFIG.PINPOINT_URL, { waitUntil: 'networkidle2' });
        await sleep(3000);

        console.log('\n✅ Browser is ready!');
        console.log('\n📖 INSTRUCTIONS:');
        console.log('─'.repeat(60));
        console.log('1. Click on each document in the list');
        console.log('2. Look for the download button (⬇ or three dots menu)');
        console.log('3. Download the PDF');
        console.log('4. Repeat for as many documents as you want');
        console.log('5. Press Ctrl+C in this terminal when done');
        console.log('─'.repeat(60));
        console.log('\n💡 TIP: Use Pinpoint export feature if available!');
        console.log('   Some collections have "Export All" options');
        console.log('\n⏰ Checking for new downloads every 30 seconds...');
        console.log('   I\'ll auto-upload them to Vault as they appear!\n');

        let lastCount = 0;
        const uploadedFiles = new Set();

        // Monitor downloads and auto-upload
        const interval = setInterval(async () => {
            try {
                const files = await fs.readdir(CONFIG.DOWNLOAD_DIR);
                const pdfFiles = files.filter(f => f.endsWith('.pdf') && !uploadedFiles.has(f));

                if (pdfFiles.length > lastCount) {
                    const newFiles = pdfFiles.slice(lastCount);
                    console.log(`\n📥 Found ${newFiles.length} new PDF(s)!`);

                    const filePaths = newFiles.map(f => path.join(CONFIG.DOWNLOAD_DIR, f));
                    const results = await uploadToVault(filePaths);

                    results.uploaded.forEach(f => uploadedFiles.add(f));

                    console.log(`\n✅ Total uploaded so far: ${uploadedFiles.size}`);
                    console.log('💡 Continue downloading more, or press Ctrl+C when done\n');

                    lastCount = pdfFiles.length;
                }
            } catch (e) {
                // Ignore errors during polling
            }
        }, 30000); // Check every 30 seconds

        // Keep running until user stops
        await new Promise(() => { }); // Run forever

    } catch (error) {
        console.error('\n❌ ERROR:', error.message);
    }
}

main().catch(console.error);
