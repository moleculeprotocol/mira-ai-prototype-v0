var disclaimerHTML = 'MIRA can make mistakes. By chatting with MIRA you agree to our <a href="https://molecule.xyz/terms-and-conditions" target="_blank" style="text-decoration: underline;">Terms & Conditions</a>.<br> For more info check our <a href="https://github.com/moleculeprotocol/mira-knowledge" target="_blank" style="text-decoration: underline;">Docs</a>.';

// Wait for the welcome-screen element to be available and append disclaimer
function addDisclaimer() {
    const welcomeScreen = document.getElementById('welcome-screen');

    if (welcomeScreen) {
        // Check if disclaimer already exists to avoid duplicates
        if (!welcomeScreen.querySelector('.disclaimer-notice')) {
            // Create the disclaimer div
            const disclaimerDiv = document.createElement('div');
            disclaimerDiv.className = 'disclaimer-notice';
            disclaimerDiv.innerHTML = disclaimerHTML;

            // Append to welcome screen
            welcomeScreen.appendChild(disclaimerDiv);
        }
        return true;
    }
    return false;
}

// Replace the watermark element with disclaimer
function replaceWatermarkWithDisclaimer() {
    const watermarkElement = document.querySelector('a.watermark');

    if (watermarkElement) {
        // Check if watermark has already been replaced by checking if it's still an 'a' tag
        if (watermarkElement.tagName === 'A') {
            // Create the disclaimer div
            const disclaimerDiv = document.createElement('div');
            disclaimerDiv.className = 'disclaimer-notice disclaimer-notice-watermark';
            disclaimerDiv.innerHTML = disclaimerHTML;

            // Replace the watermark element with the disclaimer
            watermarkElement.parentNode.replaceChild(disclaimerDiv, watermarkElement);
        }
        return true;
    }
    return false;
}

// Try to add disclaimer and replace watermark immediately
const disclaimerAdded = addDisclaimer();
const watermarkReplaced = replaceWatermarkWithDisclaimer();

// If either element not found, use MutationObserver to wait for them
if (!disclaimerAdded || !watermarkReplaced) {
    const observer = new MutationObserver((mutations, obs) => {
        const disclaimerNowAdded = addDisclaimer();
        const watermarkNowReplaced = replaceWatermarkWithDisclaimer();

        // Stop observing once both tasks are completed
        if (disclaimerNowAdded && watermarkNowReplaced) {
            obs.disconnect();
        }
    });

    // Start observing when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        });
    } else {
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
}