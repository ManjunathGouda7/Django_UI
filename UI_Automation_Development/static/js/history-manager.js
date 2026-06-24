/**
 * History Manager
 * Tracks chat conversations and displays them in the history sidebar
 * Matches the CSS classes from next_gen_ui.css
 */

// Track all chat conversations
let chatHistory = [];
let currentChatId = null;

/**
 * Toggle history sidebar (already defined in main HTML, but here as backup)
 */
function toggleHistorySidebar() {
    const sidebar = document.getElementById('historySidebar');
    if (sidebar) {
        sidebar.classList.toggle('active');
    }
}

/**
 * Load chat history from server/localStorage
 */
async function loadChatHistory() {
    try {
        // Try to fetch from API
        let history = [];
        
        try {
            const response = await fetch('/api/get-chat-history/');
            if (response.ok) {
                const data = await response.json();
                history = data.history || [];
            }
        } catch (error) {
            console.log('API not available, using localStorage');
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
 * Group chats by date (Today, Yesterday, This Week, This Month, Older)
 */
function groupChatsByDate(chats) {
    const groups = {
        today: [],
        yesterday: [],
        thisWeek: [],
        thisMonth: [],
        older: []
    };
    
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const weekAgo = new Date(today);
    weekAgo.setDate(weekAgo.getDate() - 7);
    const monthAgo = new Date(today);
    monthAgo.setMonth(monthAgo.getMonth() - 1);
    
    chats.forEach(chat => {
        const chatDate = new Date(chat.updatedAt);
        const chatDay = new Date(chatDate.getFullYear(), chatDate.getMonth(), chatDate.getDate());
        
        if (chatDay.getTime() === today.getTime()) {
            groups.today.push(chat);
        } else if (chatDay.getTime() === yesterday.getTime()) {
            groups.yesterday.push(chat);
        } else if (chatDay > weekAgo) {
            groups.thisWeek.push(chat);
        } else if (chatDay > monthAgo) {
            groups.thisMonth.push(chat);
        } else {
            groups.older.push(chat);
        }
    });
    
    return groups;
}

/**
 * Render history list in sidebar
 */
function renderHistoryList() {
    const listContainer = document.getElementById('historyList');
    if (!listContainer) return;
    
    if (chatHistory.length === 0) {
        listContainer.innerHTML = `
            <div class="history-empty">
                <i class="fas fa-comments"></i>
                <p>No previous chats yet</p>
            </div>
        `;
        return;
    }
    
    const groups = groupChatsByDate(chatHistory);
    const groupLabels = {
        today: 'Today',
        yesterday: 'Yesterday',
        thisWeek: 'This Week',
        thisMonth: 'This Month',
        older: 'Older'
    };
    
    let html = '';
    
    for (const [groupKey, groupChats] of Object.entries(groups)) {
        if (groupChats.length === 0) continue;
        
        html += `
            <div class="history-group">
                <h4>${groupLabels[groupKey]}</h4>
                <div class="history-items">
        `;
        
        groupChats.forEach(chat => {
            const isActive = currentChatId === chat.id;
            const title = escapeHtml(chat.title || 'New Chat');
            const preview = escapeHtml(chat.preview || 'No messages yet');
            const timeStr = formatTime(chat.updatedAt);
            
            html += `
                <div class="history-item ${isActive ? 'active' : ''}" data-chat-id="${chat.id}">
                    <div class="history-item-title" onclick="loadChatConversation(${chat.id})" title="${title}">
                        <i class="fas fa-comment"></i> ${title}
                        <div style="font-size: 10px; opacity: 0.6; margin-top: 2px;">
                            ${preview}
                        </div>
                        <div style="font-size: 9px; opacity: 0.4; margin-top: 2px;">
                            <i class="far fa-clock"></i> ${timeStr}
                        </div>
                    </div>
                    <button class="history-item-delete" onclick="event.stopPropagation(); deleteChatHistory(${chat.id})" title="Delete chat">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    }
    
    listContainer.innerHTML = html;
}

/**
 * Format time for display
 */
function formatTime(date) {
    if (!date) return 'Unknown';
    
    const d = new Date(date);
    const now = new Date();
    const diffMs = now - d;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    
    return d.toLocaleDateString();
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
    
    // Create new chat object
    const newChat = {
        id: Date.now(),
        title: 'New Chat',
        messages: [],
        createdAt: new Date(),
        updatedAt: new Date(),
        preview: 'No messages yet',
        messageCount: 0
    };
    
    chatHistory.unshift(newChat);
    currentChatId = newChat.id;
    
    await saveChatHistory();
    renderHistoryList();
    
    // Close sidebar on mobile
    if (window.innerWidth <= 768) {
        toggleHistorySidebar();
    }
    
    // Highlight the new chat
    highlightHistoryItem(newChat.id);
    
    return newChat.id;
}

/**
 * Load a specific chat conversation
 */
async function loadChatConversation(chatId) {
    const chat = chatHistory.find(c => c.id === chatId);
    if (!chat) {
        console.error('Chat not found:', chatId);
        return;
    }
    
    currentChatId = chatId;
    
    // Clear messages container
    const messagesContainer = document.getElementById('messagesContainer');
    if (!messagesContainer) return;
    
    // Show loading state
    messagesContainer.innerHTML = '<div class="loading-messages"><i class="fas fa-spinner fa-spin"></i> Loading chat...</div>';
    
    // Simulate load delay for better UX
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
                appendMessageToChat(message);
            });
            scrollToBottom();
        }
        
        // Highlight active chat
        highlightHistoryItem(chatId);
        
        // Close sidebar on mobile
        if (window.innerWidth <= 768) {
            toggleHistorySidebar();
        }
    }, 300);
}

/**
 * Append message to chat container
 */
function appendMessageToChat(message) {
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
                ${marked.parse(message.content)}
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
 * Add a message to current chat
 */
function addMessageToCurrentChat(sender, content) {
    if (!currentChatId) {
        createNewChat();
    }
    
    const chat = chatHistory.find(c => c.id === currentChatId);
    if (!chat) return;
    
    const message = {
        id: Date.now(),
        sender: sender,
        content: content,
        timestamp: new Date()
    };
    
    chat.messages.push(message);
    chat.messageCount = chat.messages.length;
    chat.updatedAt = new Date();
    
    // Update preview
    chat.preview = content.substring(0, 60) + (content.length > 60 ? '...' : '');
    
    // Update title from first user message
    if (chat.title === 'New Chat' && sender === 'user') {
        chat.title = content.substring(0, 30) + (content.length > 30 ? '...' : '');
    }
    
    saveChatHistory();
    renderHistoryList();
    
    // Append to UI
    appendMessageToChat(message);
    scrollToBottom();
}

/**
 * Delete a chat from history
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
        
        showToast('Chat deleted successfully', 'success');
    }
}

/**
 * Clear all chats
 */
async function clearAllChats() {
    if (!confirm('⚠️ WARNING: This will delete ALL chat history. This action cannot be undone. Are you sure?')) {
        return;
    }
    
    chatHistory = [];
    await saveChatHistory();
    renderHistoryList();
    await createNewChat();
    showToast('All chats cleared successfully', 'success');
}

/**
 * Delete a single message from current chat
 */
function deleteMessageFromChat(messageId) {
    const chat = chatHistory.find(c => c.id === currentChatId);
    if (chat) {
        const messageIndex = chat.messages.findIndex(m => m.id == messageId);
        if (messageIndex !== -1) {
            chat.messages.splice(messageIndex, 1);
            chat.messageCount = chat.messages.length;
            chat.updatedAt = new Date();
            
            // Update preview if messages exist
            if (chat.messages.length > 0) {
                const lastMessage = chat.messages[chat.messages.length - 1];
                chat.preview = lastMessage.content.substring(0, 60) + (lastMessage.content.length > 60 ? '...' : '');
            } else {
                chat.preview = 'No messages yet';
                if (chat.title !== 'New Chat') {
                    chat.title = 'New Chat';
                }
            }
            
            saveChatHistory();
            renderHistoryList();
            
            // Reload current conversation
            loadChatConversation(currentChatId);
            showToast('Message deleted', 'success');
        }
    }
}

/**
 * Highlight active history item
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
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
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
 * Show toast notification
 */
function showToast(message, type = 'info') {
    let toast = document.querySelector('.chat-toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.className = 'chat-toast';
        document.body.appendChild(toast);
    }
    
    toast.textContent = message;
    toast.className = `chat-toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Initialize history on page load
window.addEventListener('DOMContentLoaded', () => {
    loadChatHistory();
});