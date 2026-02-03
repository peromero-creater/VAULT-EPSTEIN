const https = require('https');

https.get('https://epstein-docs.github.io/all-documents/', (res) => {
    let data = '';
    res.on('data', (chunk) => data += chunk);
    res.on('end', () => {
        // Look for links
        console.log('Page size:', data.length);

        // Print sample of ANY hrefs
        const allLinks = data.match(/href="([^"]+)"/g);
        if (allLinks) {
            console.log('Sample links:', allLinks.slice(50, 60));
        } else {
            console.log('No hrefs found?');
        }
        // Find PDF links
        const pdfs = data.match(/href="([^"]+\.pdf)"/g);
        if (pdfs) {
            console.log('Found PDF links:', pdfs.slice(0, 10));
        } else {
            console.log('No direct PDF links found.');
        }

        // Find document page links
        const docPages = data.match(/href="(\/documents\/[^"]+)"/g);
        if (docPages) {
            console.log('Found Document Page links:', docPages.slice(0, 10));
        }

        // Check for "download" keyword
        if (data.includes('download')) {
            console.log('Page contains "download" keyword');
        }
    });
}).on('error', (e) => {
    console.error(e);
});
