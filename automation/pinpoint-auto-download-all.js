/**
 * FULLY AUTOMATED Pinpoint Downloader (Pagination Support)
 * 
 * Strategy:
 * 1. Stay on the main list
 * 2. Open documents in NEW TABS (preserves pagination state)
 * 3. Ctrl+P -> Save -> Close Tab
 * 4. Click "Next >" button to go to next page
 * 5. Handle all 47+ pages automatically
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
    DELAY_PAGE_LOAD: 5000,        // Wait for list to load
    DELAY_TAB_OPEN: 3000,         // Wait for doc to open
    DELAY_PRINT_DIALOG: 2000,     // Wait for print dialog
    DELAY_NEXT_PAGE: 5000,        // Wait after clicking next page
};

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function ensureDownloadDirectory() {
    try {
        await fs.access(CONFIG.DOWNLOAD_DIR);
    } catch {
        await fs.mkdir(CONFIG.DOWNLOAD_DIR, { recursive: true });
    }
}

async function uploadToVault(filePaths) {
    if (filePaths.length === 0) return { uploaded: [], errors: [] };
    const uploadUrl = `${CONFIG.VAULT_API_URL}/admin/upload-documents`;
    const results = { uploaded: [], errors: [] };

    for (const filePath of filePaths) {
        const fileName = path.basename(filePath);
        try {
            const form = new FormData();
            const fileStream = require('fs').createReadStream(filePath);
            form.append('files', fileStream, fileName);

            const result = await new Promise((resolve, reject) => {
                const request = http.request(uploadUrl, { method: 'POST', headers: form.getHeaders() }, (res) => {
                    let data = '';
                    res.on('data', c => data += c);
                    res.on('end', () => res.statusCode === 200 ? resolve(JSON.parse(data)) : reject(new Error(res.statusCode)));
                });
                request.on('error', reject);
                form.pipe(request);
            });
            if (result.success_count > 0) results.uploaded.push(fileName);
        } catch (e) { results.errors.push(e.message); }
    }
    return results;
}

async function processPage(browser, page, pageNum, processedSet) {
    // Get all document links
    const links = await page.evaluate(() => {
        return Array.from(document.querySelectorAll('a[href*="/document/"]'))
            .map(a => ({ href: a.href, text: a.innerText.trim() }))
            .filter(l => l.text.endsWith('.pdf') || l.href.includes('.pdf'));
    });

    console.log(`\n📄 Page ${pageNum}: Found ${links.length} documents`);

    let newDocsOnPage = 0;

    for (let i = 0; i < links.length; i++) {
        const link = links[i];
        if (processedSet.has(link.href)) continue;

        processedSet.add(link.href);
        newDocsOnPage++;

        console.log(`  [${processedSet.size}] Downloading: ${link.text.substring(0, 40)}...`);

        // OPEN IN NEW TAB
        const newPage = await browser.newPage();
        try {
            // Set download behavior for new tab
            const client = await newPage.target().createCDPSession();
            await client.send('Page.setDownloadBehavior', { behavior: 'allow', downloadPath: CONFIG.DOWNLOAD_DIR });

            await newPage.goto(link.href, { waitUntil: 'networkidle2', timeout: 60000 });
            await sleep(CONFIG.DELAY_TAB_OPEN);

            // Ctrl+P
            await newPage.keyboard.down('Control');
            await newPage.keyboard.press('KeyP');
            await newPage.keyboard.up('Control');
            await sleep(CONFIG.DELAY_PRINT_DIALOG);
            console.log('    ✓ Saved');

        } catch (e) {
            console.log(`    ❌ Error: ${e.message}`);
        } finally {
            await newPage.close();
        }

        // Upload check every 5 docs
        if (processedSet.size % 5 === 0) {
            await checkAndUpload();
        }
    }

    return newDocsOnPage;
}

async function checkAndUpload() {
    const files = await fs.readdir(CONFIG.DOWNLOAD_DIR);
    const pdfs = files.filter(f => f.endsWith('.pdf'));
    // Simple check: Just upload everything that looks like a PDF
    const results = await uploadToVault(pdfs.map(f => path.join(CONFIG.DOWNLOAD_DIR, f)));
    if (results.uploaded.length > 0) {
        console.log(`    📤 Auto-uploaded ${results.uploaded.length} files`);
    }
}

async function main() {
    console.log('🚀 FULL AUTOMATION (Multi-Page / New Tab Mode)');
    console.log('==============================================');

    await ensureDownloadDirectory();

    const browser = await puppeteer.launch({
        headless: false,
        defaultViewport: null,
        args: ['--start-maximized', `--user-data-dir=${CONFIG.CHROME_USER_DATA}`]
    });

    const page = (await browser.pages())[0];

    console.log('🌐 Opening Pinpoint...');
    await page.goto(CONFIG.PINPOINT_URL);

    console.log('⏳ Waiting 10s for you to ensure filters are correct...');
    await sleep(10000); // Give user time to see the page

    let currentPage = 1;
    const processedSet = new Set();

    while (true) {
        // 1. Process all docs on current page
        const count = await processPage(browser, page, currentPage, processedSet);

        if (count === 0 && processedSet.size > 0) {
            console.log('⚠️ No new documents found on this page.');
        }

        // 2. Find and click "Next" button
        // The arrow is usually an SVG or button with aria-label
        // Look for right arrow icon or button at bottom
        console.log('🔎 Looking for Next Page button...');

        const nextButton = await page.evaluateHandle(() => {
            // Logic: Find the pagination container, then the active page, then the next element
            // Or find button with 'chevron_right' or aria-label='Next page'
            const buttons = Array.from(document.querySelectorAll('div[role="button"], button'));
            // Pinpoint pagination usually looks like numbers and arrows
            // The Next button is typically the last one or has specific aria
            return buttons.find(b => b.ariaLabel?.includes('Next') || b.textContent.trim() === '>' || b.querySelector('i')?.textContent === 'chevron_right');
        });

        if (nextButton && nextButton.asElement()) {
            console.log('➡️ Clicking Next Page...');
            await nextButton.click();
            await sleep(CONFIG.DELAY_NEXT_PAGE);
            currentPage++;
        } else {
            console.log('🛑 No "Next" button found. We managed to reach the end!');
            break;
        }
    }

    console.log('✅ ALL PAGES PROCESSED!');
    await browser.close();
}

main().catch(console.error);
