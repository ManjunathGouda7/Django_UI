/**
 * Streaming Response Handler
 * Implements real-time streaming responses using Server-Sent Events (SSE)
 */

// Active streaming connections
let activeStreams = {};

/**
 * Send message with streaming response
 * @param {string} message - User message
 * @param {File} file - Optional file upload
 * @param {Function} onChunk - Callback when chunk received
 * @param {Function} onComplete - Callback when stream completes
 */
function sendMessageWithStreaming(message = '', file = null, onChunk = null, onComplete = null) {
    const streamId = Date.now();
    
    if (!message && !file) return;
    
    // Clear input after sending
    messageInput.value = '';
    fileInput.value = '';
    fileNameDisplay.textContent = '';
    
    // Add user message immediately
    const tempUserId = 'temp-user-' + Date.now();
    const displayMsg = message || (file ? `File: ${file.name}` : 'Sent a file');
    addMessage(displayMsg, 'user', new Date().toISOString(), tempUserId);
    
    // Add loading indicator
    const loadingId = 'loading-' + streamId;
    addMessage('<div class="typing-indicator"><span></span><span></span><span></span></div>', 'bot', new Date().toISOString(), loadingId, true);
    
    // Prepare FormData for streaming request
    const formData = new FormData();
    formData.append('message', message);
    if (file) {
        formData.append('file', file);
    }
    formData.append('stream', 'true');  // Flag for streaming
    
    // Send initial request to get user message ID and bot message ID
    fetch('/api/send-message/', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            // Remove loading indicator
            const loadingMsg = document.getElementById(`message-${loadingId}`);
            if (loadingMsg) loadingMsg.remove();
            
            if (data.error) {
                addMessage('Error: ' + data.error, 'bot', new Date().toISOString(), 'error');
            } else {
                // Update user message ID
                const userMsgDiv = document.getElementById(`message-${tempUserId}`);
                if (userMsgDiv) {
                    userMsgDiv.id = `message-${data.user_message.id}`;
                    const menuBtn = userMsgDiv.querySelector('.action-btn');
                    if (menuBtn) menuBtn.setAttribute('onclick', `toggleMenu('${data.user_message.id}')`);
                    const menuDiv = userMsgDiv.querySelector('.action-menu');
                    if (menuDiv) menuDiv.id = `menu-${data.user_message.id}`;
                }
                
                // Add initial empty bot message for streaming
                if (data.bot_message) {
                    addMessage('', 'bot', data.bot_message.timestamp, data.bot_message.id);
                    
                    // Connect to SSE stream if endpoint available
                    const botMsgDiv = document.getElementById(`message-${data.bot_message.id}`);
                    if (botMsgDiv) {
                        botMsgDiv.classList.add('streaming');
                        const indicator = document.createElement('span');
                        indicator.className = 'stream-indicator';
                        botMsgDiv.querySelector('.message-content').appendChild(indicator);
                    }
                    
                    // Start streaming chunk by chunk (simulated with fetch)
                    streamBotResponse(data.bot_message.id, message, file, onChunk);
                }
            }
        })
        .catch(error => {
            console.error('Streaming error:', error);
            const loadingMsg = document.getElementById(`message-${loadingId}`);
            if (loadingMsg) loadingMsg.remove();
            addMessage('Connection error. Please try again.', 'bot', new Date().toISOString(), 'error-' + Date.now());
        });
}

/**
 * Stream bot response by fetching from dedicated endpoint
 * @param {string} botMessageId - ID of bot message to update
 * @param {string} userMessage - The user message
 * @param {File} file - Uploaded file if any
 * @param {Function} onChunk - Callback for each chunk
 */
function streamBotResponse(botMessageId, userMessage, file = null, onChunk = null) {
    const messageDiv = document.getElementById(`message-${botMessageId}`);
    if (!messageDiv) return;
    
    const contentDiv = messageDiv.querySelector('.message-content');
    if (!contentDiv) return;
    
    let fullContent = '';
    
    // For now, we'll use the standard response (backend will support streaming in future)
    // This is a placeholder for when backend implements Server-Sent Events
    
    // Prepare form data
    const formData = new FormData();
    formData.append('message', userMessage);
    if (file) {
        formData.append('file', file);
    }
    
    fetch('/api/send-message/', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.bot_message) {
                fullContent = data.bot_message.content;
                
                // Remove stream indicator
                const indicator = contentDiv.querySelector('.stream-indicator');
                if (indicator) indicator.remove();
                
                // Render markdown content
                if (hasMarkdown && hasMarkdown(fullContent)) {
                    contentDiv.innerHTML = renderMarkdown(fullContent);
                } else {
                    contentDiv.innerText = fullContent;
                }
                
                // Remove streaming class
                messageDiv.classList.remove('streaming');
                
                // Add copy button
                if (addCopyButton) {
                    addCopyButton(messageDiv);
                }
                
                // Add document indicator if present
                if (fullContent.includes('📄')) {
                    const docName = 'Uploaded Document';
                    if (addDocumentIndicator) {
                        addDocumentIndicator(messageDiv, docName);
                    }
                }
                
                if (onChunk) onChunk(fullContent);
            }
        })
        .catch(error => {
            console.error('Stream fetch error:', error);
            const indicator = contentDiv.querySelector('.stream-indicator');
            if (indicator) indicator.remove();
            contentDiv.innerText = 'Error while streaming response.';
            messageDiv.classList.remove('streaming');
        });
}

/**
 * Check if streaming is supported
 * @returns {boolean} True if server supports streaming
 */
async function checkStreamingSupport() {
    try {
        const response = await fetch('/api/status/');
        const data = await response.json();
        return data.streaming_enabled || false;
    } catch {
        return false;
    }
}

/**
 * Cancel active stream
 * @param {string} messageId - ID of message to cancel
 */
function cancelStream(messageId) {
    if (activeStreams[messageId]) {
        activeStreams[messageId].abort();
        delete activeStreams[messageId];
    }
}

// Enhanced sendMessage to use streaming by default
const originalSendMessage = typeof sendMessage === 'function' ? sendMessage : null;

// Will be integrated into main script.js after this
