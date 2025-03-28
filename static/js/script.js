document.addEventListener('DOMContentLoaded', (event) => {
    const copyBtn = document.getElementById('copy-btn');
    // Get the hidden textarea containing the raw markdown
    const rawMarkdownTextarea = document.getElementById('raw-markdown-for-copy');

    // Check if the button and the textarea exist
    if (copyBtn && rawMarkdownTextarea) {
        copyBtn.addEventListener('click', () => {
            // Get the value from the textarea
            const textToCopy = rawMarkdownTextarea.value;

            navigator.clipboard.writeText(textToCopy).then(() => {
                // Success feedback
                const originalText = copyBtn.textContent;
                copyBtn.textContent = 'Copied!';
                copyBtn.style.backgroundColor = '#48bb78'; // Green feedback

                setTimeout(() => {
                    copyBtn.textContent = originalText;
                    copyBtn.style.backgroundColor = ''; // Revert style
                }, 2000); // Revert after 2 seconds

            }).catch(err => {
                console.error('Failed to copy text: ', err);
                // Error feedback
                const originalText = copyBtn.textContent;
                copyBtn.textContent = 'Copy Failed';
                copyBtn.style.backgroundColor = '#e53e3e'; // Red feedback

                 setTimeout(() => {
                    copyBtn.textContent = originalText;
                    copyBtn.style.backgroundColor = ''; // Revert style
                }, 2000);
            });
        });
    } else {
        // Log an error if elements aren't found, helps debugging
        if (!copyBtn) console.error("Copy button not found");
        if (!rawMarkdownTextarea) console.error("Raw markdown textarea not found");
    }
});
