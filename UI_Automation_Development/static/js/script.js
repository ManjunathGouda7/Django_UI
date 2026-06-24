// ====================== DOM Elements ======================
const messagesContainer = document.getElementById('messagesContainer');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const fileInput = document.getElementById('fileInput');
const fileNameDisplay = document.getElementById('fileName');

// ====================== Event Listeners ======================
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey && messageInput.value.trim()) {
        e.preventDefault();
        sendMessage();
    }
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        fileNameDisplay.textContent = file.name;
        if (typeof addDocumentToPanel === 'function') {
            addDocumentToPanel(file.name, file.size);
        }
    } else {
        fileNameDisplay.textContent = '';
    }
});

// Close all action menus when clicking outside
window.addEventListener('click', (e) => {
    if (!e.target.closest('.message-actions')) {
        document.querySelectorAll('.action-menu.show').forEach(menu => {
            menu.classList.remove('show');
        });
    }
});

// ====================== Send Message (Optimistic UI) ======================
async function sendMessage() {
    const text = messageInput.value.trim();
    const file = fileInput.files[0];

    if (!text && !file) return;

    sendBtn.disabled = true;

    messageInput.value = '';
    fileNameDisplay.textContent = '';
    fileInput.value = '';

    const tempUserId = 'temp-' + Date.now();
    const userDisplayText = text || `📄 ${file.name}`;

    addMessage(userDisplayText, 'user', new Date().toISOString(), tempUserId);

    const loadingId = 'loading-' + Date.now();
    addMessage(
        '<div class="typing-indicator"><span></span><span></span><span></span></div>',
        'bot',
        new Date().toISOString(),
        loadingId,
        true
    );

    let options = {};
    if (file) {
        const formData = new FormData();
        formData.append('message', text);
        formData.append('file', file);
        options = { method: 'POST', body: formData };
    } else {
        options = {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                message: text,
                session_id: window.currentSessionId || null
            })
        };
    }

    try {
        const response = await fetch('/api/send-message/', options);
        const data = await response.json();

        document.getElementById(`message-${loadingId}`)?.remove();

        if (data.error) {
            addMessage(`Error: ${data.error}`, 'bot', new Date().toISOString(), 'error-' + Date.now());
            if (typeof handleTimeoutError === 'function') handleTimeoutError(data.error);
            return;
        }

        // Update user message with real ID
        const tempUserDiv = document.getElementById(`message-${tempUserId}`);
        if (tempUserDiv && data.user_message?.id) {
            tempUserDiv.id = `message-${data.user_message.id}`;
            const actionBtn = tempUserDiv.querySelector('.action-btn');
            if (actionBtn) actionBtn.setAttribute('onclick', `toggleMenu('${data.user_message.id}')`);
            const menuDiv = tempUserDiv.querySelector('.action-menu');
            if (menuDiv) menuDiv.id = `menu-${data.user_message.id}`;
            const deleteBtn = tempUserDiv.querySelector('.menu-item.delete');
            if (deleteBtn) deleteBtn.setAttribute('onclick', `deleteMessage('${data.user_message.id}')`);
        }

        if (data.bot_message) {
            addMessage(
                data.bot_message.content,
                'bot',
                data.bot_message.timestamp || new Date().toISOString(),
                data.bot_message.id
            );
        }

        if (file && data.bot_message?.id && typeof linkMessageToDocument === 'function') {
            const doc = typeof getDocumentByName === 'function' ? getDocumentByName(file.name) : null;
            if (doc) linkMessageToDocument(data.bot_message.id, doc.id);
        }

    } catch (error) {
        console.error('Send message failed:', error);
        document.getElementById(`message-${loadingId}`)?.remove();
        addMessage('Sorry, something went wrong. Please try again.', 'bot', new Date().toISOString(), 'error-' + Date.now());
    } finally {
        setTimeout(() => sendBtn.disabled = false, 300);
    }
}

// ====================== Add Message ======================
function addMessage(content, sender, timestamp, id, isHtml = false) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}`;
    msgDiv.id = `message-${id}`;

    const timeStr = new Date(timestamp).toLocaleTimeString('en-US', {
        hour: '2-digit', minute: '2-digit', hour12: false
    });

    msgDiv.innerHTML = `
        <div class="message-wrapper">
            <div class="message-content">${isHtml ? content : escapeHtml(content)}</div>
            <div class="message-info">
                <span class="timestamp">
                    ${sender === 'user' ? '<i class="fas fa-arrow-up"></i>' : '<i class="fas fa-arrow-down"></i>'}
                    ${timeStr}
                </span>
                <div class="message-actions">
                    <button class="action-btn" onclick="toggleMenu('${id}')">
                        <i class="fas fa-ellipsis-h"></i>
                    </button>
                    <div class="action-menu" id="menu-${id}">
                        <div class="menu-item delete" onclick="deleteMessage('${id}')">
                            <i class="fas fa-trash-alt"></i> Delete
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    messagesContainer.querySelector('.no-messages')?.remove();
    messagesContainer.appendChild(msgDiv);

    if (sender === 'bot' && !isHtml && typeof renderMarkdown === 'function') {
        setTimeout(() => {
            formatMessageContent(msgDiv, content, sender);
            if (typeof addCopyButton === 'function') addCopyButton(msgDiv);
        }, 10);
    }

    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// ====================== Message Actions ======================
function toggleMenu(id) {
    const menu = document.getElementById(`menu-${id}`);
    if (!menu) return;

    document.querySelectorAll('.action-menu.show').forEach(m => {
        if (m.id !== `menu-${id}`) m.classList.remove('show');
    });

    menu.classList.toggle('show');
}

function deleteMessage(id) {
    if (!confirm('Delete this message?')) return;

    fetch(`/api/delete-message/${id}/`, { method: 'DELETE' })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'Message deleted') {
                document.getElementById(`message-${id}`)?.remove();
                if (messagesContainer.children.length === 0) {
                    showWelcomeMessage();
                }
            }
        })
        .catch(err => {
            console.error(err);
            alert('Failed to delete message');
        });
}

// ====================== New Chat (No Confirmation) ======================
function newChat() {
    createNewConversation();
}

// ====================== Clear Messages (With Confirmation) ======================
function clearMessages() {
    if (!confirm('Are you sure you want to clear all messages?')) return;

    fetch('/api/clear-messages/', { method: 'DELETE' })
        .then(res => res.json())
        .then(() => {
            showWelcomeMessage();
        })
        .catch(err => console.error('Clear failed:', err));
}

function showWelcomeMessage() {
    messagesContainer.innerHTML = `
        <div class="no-messages">
            <i class="fas fa-comments"></i>
            <p>👋 Welcome to GRL Chatbot!</p>
            <p style="font-size: 13px; opacity: 0.7;">Start a conversation and let's chat! 💬</p>
        </div>
    `;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ====================== History Panel ======================
function toggleHistoryPanel() {
    const historyPanel = document.getElementById('historyPanel');
    const documentsPanel = document.getElementById('documentsPanel');

    historyPanel.classList.toggle('open');
    documentsPanel.classList.remove('open');
}

async function loadChatHistory() {
    try {
        const res = await fetch('/api/chat-history/');
        const data = await res.json();

        const historyList = document.getElementById('historyList');
        historyList.innerHTML = '';

        if (!data.history || data.history.length === 0) {
            historyList.innerHTML = `<p class="empty-history">No previous chats yet</p>`;
            return;
        }

        data.history.forEach(chat => {
            const item = document.createElement('div');
            item.className = `history-item ${chat.is_active ? 'active' : ''}`;
            item.innerHTML = `
                <div class="history-title">${chat.title || 'Untitled Chat'}</div>
                <div class="history-date">${new Date(chat.updated_at || Date.now()).toLocaleDateString()}</div>
            `;
            item.onclick = () => loadSpecificChat(chat.id);
            historyList.appendChild(item);
        });
    } catch (err) {
        console.error('Failed to load history:', err);
        document.getElementById('historyList').innerHTML = `<p class="empty-history">Failed to load history</p>`;
    }
}

function loadSpecificChat(chatId) {
    console.log('Loading chat ID:', chatId);
    // TODO: Add logic to load previous chat messages
    toggleHistoryPanel();
}

// ====================== Initialize on Load ======================
window.addEventListener('load', () => {
    // Show welcome message if chat is empty
    if (messagesContainer.children.length === 0) {
        showWelcomeMessage();
    }

    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Load chat history
    if (typeof loadChatHistory === 'function') {
        setTimeout(loadChatHistory, 700);
    }
});