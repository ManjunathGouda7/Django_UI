/**
 * Markdown Handler
 * Renders markdown content securely using marked.js and DOMPurify
 */

// Configure marked.js
marked.setOptions({
    breaks: true,
    gfm: true,
    pedantic: false
});

/**
 * Convert markdown to HTML and sanitize it
 * @param {string} markdown - Raw markdown text
 * @returns {string} Safe HTML string
 */
function renderMarkdown(markdown) {
    if (!markdown) return '';
    
    try {
        // Convert markdown to HTML
        const rawHtml = marked.parse(markdown);
        
        // Sanitize HTML to prevent XSS
        const cleanHtml = DOMPurify.sanitize(rawHtml, {
            ALLOWED_TAGS: [
                'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'hr', 'a', 'img',
                'table', 'thead', 'tbody', 'tr', 'th', 'td'
            ],
            ALLOWED_ATTR: ['href', 'title', 'src', 'alt', 'target', 'rel'],
            RETURN_DOM_FRAGMENT: false,
            RETURN_DOM: false
        });
        
        return cleanHtml;
    } catch (error) {
        console.error('Markdown rendering error:', error);
        return escapeHtml(markdown);
    }
}

/**
 * Check if text contains markdown formatting
 * @param {string} text - Text to check
 * @returns {boolean} True if contains markdown
 */
function hasMarkdown(text) {
    if (!text) return false;
    
    const markdownPatterns = [
        /[*_]{1,3}[^*_\n]+[*_]{1,3}/,  // Bold/italic
        /^#{1,6}\s/m,                   // Headers
        /^[\s]*[-*+]\s/m,               // Lists
        /^[\s]*\d+\.\s/m,               // Numbered lists
        /```[\s\S]*?```/,               // Code blocks
        /`[^`]+`/,                      // Inline code
        /\[.+\]\(.+\)/,                 // Links
        /^>\s/m                         // Blockquotes
    ];
    
    return markdownPatterns.some(pattern => pattern.test(text));
}

/**
 * Format bot message with markdown rendering
 * Uses markdown rendering for bot messages, plain text for user messages
 * @param {HTMLElement} messageDiv - Message DOM element
 * @param {string} content - Message content
 * @param {string} sender - 'user' or 'bot'
 */
function formatMessageContent(messageDiv, content, sender) {
    const contentDiv = messageDiv.querySelector('.message-content');
    
    if (!contentDiv) return;
    
    if (sender === 'bot') {
        // Render markdown for bot messages
        const html = renderMarkdown(content);
        contentDiv.innerHTML = html;
    } else {
        // Keep plain text for user messages
        contentDiv.textContent = content;
    }
}

/**
 * Update existing message with markdown
 * @param {string} messageId - ID of the message to update
 * @param {string} newContent - New content with markdown
 */
function updateMessageMarkdown(messageId, newContent) {
    const messageDiv = document.getElementById(`message-${messageId}`);
    if (!messageDiv) return;
    
    const contentDiv = messageDiv.querySelector('.message-content');
    if (!contentDiv) return;
    
    const html = renderMarkdown(newContent);
    contentDiv.innerHTML = html;
}

/**
 * Add copy-to-clipboard button functionality
 * @param {HTMLElement} messageDiv - Message element
 */
function addCopyButton(messageDiv) {
    const contentDiv = messageDiv.querySelector('.message-content');
    if (!contentDiv) return;
    
    // Check if copy button already exists
    if (messageDiv.querySelector('.copy-btn')) return;
    
    const messageId = messageDiv.id.replace('message-', '');
    const actionMenu = messageDiv.querySelector('.action-menu');
    
    if (!actionMenu) return;
    
    const copyItem = document.createElement('div');
    copyItem.className = 'menu-item copy';
    copyItem.innerHTML = '<i class="fas fa-copy"></i> Copy';
    copyItem.onclick = (e) => {
        e.stopPropagation();
        copyMessageContent(messageId, contentDiv);
    };
    
    actionMenu.insertBefore(copyItem, actionMenu.firstChild);
}

/**
 * Copy message content to clipboard
 * @param {string} messageId - ID of message
 * @param {HTMLElement} contentDiv - Content element to copy
 */
function copyMessageContent(messageId, contentDiv) {
    const text = contentDiv.innerText || contentDiv.textContent;
    
    navigator.clipboard.writeText(text).then(() => {
        // Show feedback
        const messageDiv = document.getElementById(`message-${messageId}`);
        const originalText = messageDiv.querySelector('.copy-btn')?.innerText;
        const copyBtn = messageDiv?.querySelector('.copy-btn');
        
        if (copyBtn) {
            copyBtn.innerText = '✓ Copied!';
            setTimeout(() => {
                copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copy';
            }, 2000);
        }
    }).catch(err => {
        console.error('Failed to copy:', err);
        alert('Failed to copy message');
    });
}
