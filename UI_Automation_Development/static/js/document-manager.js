/**
 * History Manager
 * Tracks chat conversations and displays them in a side panel
 */

// Track all chat conversations
let chatHistory = [];
let currentChatId = null;

/**
 * Toggle history panel visibility
 */
function toggleHistoryPanel() {
    const panel = document.getElementById('historyPanel');
    if (panel) {
        panel.classList.toggle('open');
    }
}

/**
 * Load chat history from server
 */
async function loadChatHistory() {
    try {
        // Try to fetch from API first
        let history = [];
        
        try {
            const response = await fetch('/api/get-chat-history/');
            if (response.ok) {
                const data = await response.json();
                history = data.history || [];
            }
        } catch (error) {
            console.log('API not available, using localStorage');
            // Fallback to localStorage
            const saved = localStorage.getItem('chatHistory');
            if (saved) {
                history = JSON.parse(saved);
            }
        }
        
        chatHistory = history;
        renderHistoryList();
        
    } catch (error) {
        console.error('Error loading chat history:', error);
        renderHistoryList();
    }
}

/**
 * Save chat history to server/localStorage
 */
async function saveChatHistory() {
    try {
        // Try to save to API
        const response = await fetch('/api/save-chat-history/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ history: chatHistory })
        });
        
        if (!response.ok) {
            throw new Error('API save failed');
        }
    } catch (error) {
        // Fallback to localStorage
        localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
    }
}

/**
 * Add a new chat to history
 * @param {string} title - Title of the chat (first few words of first message)
 */
function addChatToHistory(title = 'New Chat') {
    const chat = {
        id: Date.now(),
        title: title,
        messages: [],
        createdAt: new Date(),
        updatedAt: new Date(),
        preview: 'No messages yet',
        messageCount: 0
    };
    
    chatHistory.unshift(chat); // Add to beginning
    currentChatId = chat.id;
    saveChatHistory();
    renderHistoryList();
    highlightHistoryItem(chat.id);
    
    return chat.id;
}

/**
 * Update chat messages
 * @param {number} chatId - ID of the chat
 * @param {Array} messages - Array of message objects
 */
function updateChatMessages(chatId, messages) {
    const chat = chatHistory.find(c => c.id === chatId);
    if (!chat) return;
    
    chat.messages = messages;
    chat.messageCount = messages.length;
    chat.updatedAt = new Date();
    
    // Update preview (last message content)
    const lastMessage = messages[messages.length - 1];
    if (lastMessage) {
        const previewText = lastMessage.content.substring(0, 60);
        chat.preview = previewText + (lastMessage.content.length > 60 ? '...' : '');
        
        // Update title from first user message if still default
        if (chat.title === 'New Chat') {
            const firstUserMessage = messages.find(m => m.sender === 'user');
            if (firstUserMessage) {
                chat.title = firstUserMessage.content.substring(0, 30) + 
                           (firstUserMessage.content.length > 30 ? '...' : '');
            }
        }
    }
    
    saveChatHistory();
    renderHistoryList();
}

/**
 * Add a single message to chat
 * @param {number} chatId - ID of the chat
 * @param {Object} message - Message object {sender, content, timestamp}
 */
function addMessageToChat(chatId, message) {
    const chat = chatHistory.find(c => c.id === chatId);
    if (!chat) return;
    
    chat.messages.push(message);
    chat.messageCount = chat.messages.length;
    chat.updatedAt = new Date();
    
    // Update preview
    const previewText = message.content.substring(0, 60);
    chat.preview = previewText + (message.content.length > 60 ? '...' : '');
    
    // Update title from first user message
    if (chat.title === 'New Chat' && message.sender === 'user') {
        chat.title = message.content.substring(0, 30) + 
                   (message.content.length > 30 ? '...' : '');
    }
    
    saveChatHistory();
    renderHistoryList();
}

/**
 * Load a specific chat conversation
 * @param {number} chatId - ID of the chat to load
 */
async function loadChatConversation(chatId) {
    const chat = chatHistory.find(c => c.id === chatId);
    if (!chat) {
        console.error('Chat not found:', chatId);
        return;
    }
    
    currentChatId = chatId;
    
    // Clear current messages container
    const messagesContainer = document.getElementById('messagesContainer');
    if (!messagesContainer) return;
    
    // Show loading state
    messagesContainer.innerHTML = '<div class="loading-messages"><i class="fas fa-spinner fa-spin"></i> Loading chat...</div>';
    
    // Simulate loading delay for better UX
    setTimeout(() => {
        if (chat.messages.length === 0) {
            messagesContainer.innerHTML = `
                <div class="no-messages">
                    <i class="fas fa-comments"></i>
                    <p>💬 No messages in this chat yet</p>
                    <p style="font-size: 13px; opacity: 0.7;">Start typing to begin the conversation!</p>
                </div>
            `;
        } else {
            messagesContainer.innerHTML = '';
            chat.messages.forEach(message => {
                appendMessageToContainer(message);
            });
            scrollToBottom();
        }
        
        // Highlight the active chat in history list
        highlightHistoryItem(chatId);
    }, 300);
    
    // Close history panel on mobile
    if (window.innerWidth <= 768) {
        toggleHistoryPanel();
    }
}

/**
 * Append message to container (helper function)
 * @param {Object} message - Message object
 */
function appendMessageToContainer(message) {
    const messagesContainer = document.getElementById('messagesContainer');
    if (!messagesContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${message.sender}`;
    messageDiv.id = `message-${message.id || Date.now()}`;
    
    const timestamp = message.timestamp ? new Date(message.timestamp) : new Date();
    const timeString = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    messageDiv.innerHTML = `
        <div class="message-wrapper">
            <div class="message-content">
                ${message.content}
            </div>
            <div class="message-info">
                <span class="timestamp">
                    ${message.sender === 'user' ? '<i class="fas fa-arrow-up"></i>' : '<i class="fas fa-arrow-down"></i>'}
                    ${timeString}
                </span>
                <div class="message-actions">
                    <button class="action-btn" onclick="toggleMenu('${message.id || Date.now()}')">
                        <i class="fas fa-ellipsis-h"></i>
                    </button>
                    <div class="action-menu" id="menu-${message.id || Date.now()}">
                        <div class="menu-item delete" onclick="deleteMessageFromChat('${message.id || Date.now()}')">
                            <i class="fas fa-trash-alt"></i> Delete
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
}

/**
 * Scroll to bottom of messages
 */
function scrollToBottom() {
    const messagesContainer = document.getElementById('messagesContainer');
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

/**
 * Delete a chat from history
 * @param {number} chatId - ID of the chat to delete
 */
async function deleteChatHistory(chatId) {
    if (!confirm('Are you sure you want to delete this chat? This action cannot be undone.')) {
        return;
    }
    
    const index = chatHistory.findIndex(c => c.id === chatId);
    if (index !== -1) {
        chatHistory.splice(index, 1);
        await saveChatHistory();
        renderHistoryList();
        
        // If current chat was deleted, create new chat
        if (currentChatId === chatId) {
            await createNewChat();
        }
        
        showNotification('Chat deleted successfully', 'success');
    }
}

/**
 * Rename a chat
 * @param {number} chatId - ID of the chat
 * @param {string} newTitle - New title for the chat
 */
async function renameChat(chatId, newTitle) {
    const chat = chatHistory.find(c => c.id === chatId);
    if (chat && newTitle && newTitle.trim()) {
        chat.title = newTitle.trim();
        await saveChatHistory();
        renderHistoryList();
        showNotification('Chat renamed successfully', 'success');
    }
}

/**
 * Clear all chat history
 */
async function clearAllChats() {
    if (!confirm('⚠️ WARNING: This will delete ALL chat history. This action cannot be undone. Are you sure?')) {
        return;
    }
    
    chatHistory = [];
    await saveChatHistory();
    renderHistoryList();
    await createNewChat();
    showNotification('All chats cleared successfully', 'success');
}

/**
 * Create a new chat
 */
async function createNewChat() {
    // Clear messages container
    const messagesContainer = document.getElementById('messagesContainer');
    if (messagesContainer) {
        messagesContainer.innerHTML = `
            <div class="no-messages">
                <i class="fas fa-comments"></i>
                <p>👋 Welcome to GRL Chatbot!</p>
                <p style="font-size: 13px; opacity: 0.7;">Start a conversation and let's chat! 💬</p>
            </div>
        `;
    }
    
    // Clear input
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.value = '';
    }
    
    // Add new chat to history
    const newChatId = addChatToHistory('New Chat');
    currentChatId = newChatId;
    
    // Remove highlight from all history items
    document.querySelectorAll('.history-item').forEach(item => {
        item.classList.remove('active');
    });
    
    return newChatId;
}

/**
 * Render the history list in the panel
 */
function renderHistoryList() {
    const listContainer = document.getElementById('historyList');
    if (!listContainer) return;
    
    if (chatHistory.length === 0) {
        listContainer.innerHTML = '<p class="empty-history">No previous chats yet</p>';
        return;
    }
    
    listContainer.innerHTML = chatHistory.map(chat => `
        <div class="history-item ${currentChatId === chat.id ? 'active' : ''}" data-chat-id="${chat.id}">
            <div class="history-item-content" onclick="loadChatConversation(${chat.id})">
                <div class="history-item-header">
                    <i class="fas fa-comment"></i>
                    <span class="history-title" title="${escapeHtml(chat.title)}">${escapeHtml(chat.title)}</span>
                </div>
                <div class="history-preview">
                    ${escapeHtml(chat.preview || 'No messages yet')}
                </div>
                <div class="history-footer">
                    <span class="history-date">
                        <i class="far fa-clock"></i> ${formatDate(chat.updatedAt)}
                    </span>
                    <span class="history-message-count">
                        <i class="fas fa-envelope"></i> ${chat.messageCount} message${chat.messageCount !== 1 ? 's' : ''}
                    </span>
                </div>
            </div>
            <div class="history-item-actions">
                <button class="history-action-btn" onclick="event.stopPropagation(); showRenameDialog(${chat.id}, '${escapeHtml(chat.title)}')" title="Rename">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="history-action-btn delete" onclick="event.stopPropagation(); deleteChatHistory(${chat.id})" title="Delete">
                    <i class="fas fa-trash-alt"></i>
                </button>
            </div>
        </div>
    `).join('');
}

/**
 * Show rename dialog
 * @param {number} chatId - Chat ID
 * @param {string} currentTitle - Current title
 */
function showRenameDialog(chatId, currentTitle) {
    const newTitle = prompt('Enter new title for this chat:', currentTitle);
    if (newTitle && newTitle.trim() && newTitle !== currentTitle) {
        renameChat(chatId, newTitle);
    }
}

/**
 * Highlight the active history item
 * @param {number} chatId - Chat ID to highlight
 */
function highlightHistoryItem(chatId) {
    document.querySelectorAll('.history-item').forEach(item => {
        if (parseInt(item.dataset.chatId) === chatId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
}

/**
 * Format date for display
 * @param {Date|string} date - Date to format
 * @returns {string} Formatted date string
 */
function formatDate(date) {
    if (!date) return 'Unknown';
    
    const d = new Date(date);
    const now = new Date();
    const diffMs = now - d;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    
    return d.toLocaleDateString();
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Show notification
 * @param {string} message - Notification message
 * @param {string} type - Type (success, error, info)
 */
function showNotification(message, type = 'info') {
    // Create notification element if it doesn't exist
    let notification = document.querySelector('.chat-notification');
    if (!notification) {
        notification = document.createElement('div');
        notification.className = 'chat-notification';
        document.body.appendChild(notification);
    }
    
    notification.textContent = message;
    notification.className = `chat-notification ${type} show`;
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

/**
 * Delete a single message from current chat
 * @param {string} messageId - Message ID
 */
function deleteMessageFromChat(messageId) {
    const chat = chatHistory.find(c => c.id === currentChatId);
    if (chat) {
        const messageIndex = chat.messages.findIndex(m => m.id == messageId);
        if (messageIndex !== -1) {
            chat.messages.splice(messageIndex, 1);
            updateChatMessages(currentChatId, chat.messages);
            
            // Reload current conversation
            loadChatConversation(currentChatId);
            showNotification('Message deleted', 'success');
        }
    }
}

// Initialize history on page load
window.addEventListener('load', () => {
    renderHistoryList();
});