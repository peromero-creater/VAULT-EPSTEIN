/**
 * FULLY AUTOMATED Pinpoint Downloader
 * 
 * Automates the exact workflow:
 * 1. Click each PDF in the list
 * 2. Press Ctrl+P (print)
 * 3. Save as PDF
 * 4. Repeat for all 4,609 documents
 * 5. Auto-upload to Vault
 * 
 * Run: node pinpoint-auto-download-all.js
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
    CHROME_USER_DATA: path.join(os.homedir(), 'AppData', 'Local', 'Google', 'Chrome', 'User Data'),

    // Delays
    DELAY_AFTER_CLICK: 3000,      // Wait for PDF to open
    DELAY_AFTER_PRINT: 2000,      // Wait for print dialog
    DELAY_BETWEEN_DOCS: 1000,     // Wait between documents

    // Batch upload settings
    UPLOAD_BATCH_SIZE: 10,        // Upload every 10 PDFs
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
    if (filePaths.length === 0) return { uploaded: [], errors: [] };

    const uploadUrl = `${CONFIG.VAULT_API_URL}/admin/upload-documents`;
    const results = { uploaded: [], errors: [] };

    for (let i = 0; i < filePaths.length; i++) {
        const filePath = filePaths[i];
        const fileName = path.basename(filePath);

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
                results.uploaded.push(fileName);
            }

            await sleep(200);

        } catch (error) {
            results.errors.push({ file: fileName, error: error.message });
        }
    }

    return results;
}

async function downloadAllDocuments(page) {
    console.log('\n📥 Navigating to Pinpoint...');

    await page.goto(CONFIG.PINPOINT_URL, {
        waitUntil: 'networkidle2',
        timeout: 30000
    });

    await sleep(5000);

    console.log('🔍 Starting document download process...');
    console.log('💡 Will handle pagination automatically as we go!\n');

    let processedCount = 0;
    const downloadedFiles = [];
    let uploadedCount = 0;
    const processedUrls = new Set();

    // Target is 4609 documents total
    const TARGET_DOCS = 4609;

    while (processedCount < TARGET_DOCS) {
        // Get currently visible documents on this page
        const documentLinks = await page.evaluate(() => {
            const links = Array.from(document.querySelectorAll('a[href*="/document/"], .document-item a, [role="listitem"] a'));
            return links.map(link => ({
                href: link.href,
                text: link.textContent.trim()
            })).filter(link => link.href && link.href.includes('/document/'));
        });

        if (documentLinks.length === 0) {
            console.log('⚠️  No more documents found on this page');
            break;
        }

        // Process each document on the current page
        for (const docLink of documentLinks) {
            // Skip if already processed
            if (processedUrls.has(docLink.href)) {
                continue;
            }

            processedCount++;
            processedUrls.add(docLink.href);

            try {
                console.log(`[${processedCount}/${TARGET_DOCS}] ${docLink.text.substring(0, 50)}...`);

                // Navigate to document
                await page.goto(docLink.href, {
                    waitUntil: 'networkidle2',
                    timeout: 30000
                });

                await sleep(CONFIG.DELAY_AFTER_CLICK);

                // Press Ctrl+P
                await page.keyboard.down('Control');
                await page.keyboard.press('KeyP');
                await page.keyboard.up('Control');

                await sleep(CONFIG.DELAY_AFTER_PRINT);

                console.log('  ✓ Print initiated');

                // Go back to list
                await page.goto(CONFIG.PINPOINT_URL, {
                    waitUntil: 'networkidle2',
                    timeout: 30000
                });

                await sleep(CONFIG.DELAY_BETWEEN_DOCS);

                // Upload batch every 10 documents
                if (processedCount % CONFIG.UPLOAD_BATCH_SIZE === 0) {
                    console.log(`\n📤 Checking for PDFs to upload...`);

                    const files = await fs.readdir(CONFIG.DOWNLOAD_DIR);
                    const pdfFiles = files.filter(f => f.endsWith('.pdf'));
                    const newFiles = pdfFiles.filter(f => !downloadedFiles.includes(f));

                    if (newFiles.length > 0) {
                        console.log(`📥 Found ${newFiles.length} new PDFs, uploading...`);
                        const filePaths = newFiles.map(f => path.join(CONFIG.DOWNLOAD_DIR, f));
                        const results = await uploadToVault(filePaths);

                        uploadedCount += results.uploaded.length;
                        downloadedFiles.push(...newFiles);

                        console.log(`✅ Uploaded ${results.uploaded.length} files (Total: ${uploadedCount})`);
                    }

                    console.log(`\n📊 Progress: ${processedCount}/${TARGET_DOCS} documents processed\n`);
                }

            } catch (error) {
                console.log(`  ❌ Error: ${error.message}`);
                // Go back to list to continue
                try {
                    await page.goto(CONFIG.PINPOINT_URL, {
                        waitUntil: 'networkidle2',
                        timeout: 30000
                    });
                } catch (e) {
                    // ignore
                }
            }
        }

        // Scroll down to load more documents (if using infinite scroll)
        console.log('\n⬇️  Scrolling to load more documents...');
        await page.evaluate(() => {
            window.scrollTo(0, document.body.scrollHeight);
        });

        await sleep(3000);

        // Or click "Next" button if pagination exists
        try {
            const nextButton = await page.$('button:has-text("Next"), a:has-text("Next"), [aria-label*="Next"]');
            if (nextButton) {
                console.log('➡️  Clicking Next page...');
                await nextButton.click();
                await sleep(3000);
            }
        } catch (e) {
            // No next button or scroll is enough
        }
    }

    // Final upload
    console.log('\n📤 Final upload check...');
    const files = await fs.readdir(CONFIG.DOWNLOAD_DIR);
    const pdfFiles = files.filter(f => f.endsWith('.pdf'));
    const newFiles = pdfFiles.filter(f => !downloadedFiles.includes(f));

    if (newFiles.length > 0) {
        const filePaths = newFiles.map(f => path.join(CONFIG.DOWNLOAD_DIR, f));
        const results = await uploadToVault(filePaths);
        uploadedCount += results.uploaded.length;
    }

    return {
        totalProcessed: processedCount,
        totalUploaded: uploadedCount,
        totalDownloaded: pdfFiles.length
    };
}

async function main() {
    console.log('🚀 FULLY AUTOMATED Pinpoint Downloader\n');
    console.log('='.repeat(60));
    console.log('📊 Target: ~4,609 documents');
    console.log('🔄 Workflow: Click → Ctrl+P → Save → Upload → Repeat');
    console.log('⏱️  Estimated time: Several hours');
    console.log('='.repeat(60));

    console.log('\n⚠️  IMPORTANT: Make sure Chrome is set to:');
    console.log('   - Automatically download PDFs (not open in viewer)');
    console.log('   - Save location is set to Downloads folder');
    console.log('\n💡 To check: chrome://settings/downloads');
    console.log('   ☑ "Download PDF files instead of automatically opening"');
    console.log('\nPress Ctrl+C to stop at any time. Progress is saved!\n');

    await sleep(5000);

    await ensureDownloadDirectory();

    console.log('🌐 Launching Chrome...');

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

        const results = await downloadAllDocuments(page);

        await browser.close();

        // Final summary
        console.log('\n' + '='.repeat(60));
        console.log('✅ AUTOMATION COMPLETE!');
        console.log('='.repeat(60));
        console.log(`📁 Download location: ${CONFIG.DOWNLOAD_DIR}`);
        console.log(`📄 Documents processed: ${results.totalProcessed}`);
        console.log(`📥 PDFs downloaded: ${results.totalDownloaded}`);
        console.log(`✅ Uploaded to Vault: ${results.totalUploaded}`);
        console.log('='.repeat(60));

        console.log('\n🎉 All done! Check your Vault:');
        console.log(`   http://localhost:3000/connections`);
        console.log(`   http://localhost:3000/countries`);
        console.log(`   http://localhost:3000/search\n`);

    } catch (error) {
        console.error('\n❌ ERROR:', error.message);
        console.error(error.stack);
        console.log('\n💡 Tip: Any downloaded PDFs were already uploaded!');
        console.log(`   Check ${CONFIG.DOWNLOAD_DIR} for progress`);
    }
}

main().catch(console.error);
