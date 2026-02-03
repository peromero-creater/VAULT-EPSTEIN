const https = require('https');

https.get('https://epstein-docs.github.io/document/21/', (res) => {
    let data = '';
    res.on('data', (chunk) => data += chunk);
    res.on('end', () => {
        console.log('Doc Page size:', data.length);

        // Check for PDF links
        const pdfs = data.match(/href="([^"]+\.pdf)"/g);
        if (pdfs) {
            console.log('Found PDF links:', pdfs);
        } else {
            console.log('No direct PDF links found.');
            // Print all links
            const all = data.match(/href="([^"]+)"/g);
            console.log('All links:', all ? all.slice(0, 20) : 'None');
        }
    });
}).on('error', (e) => {
    console.error(e);
});
