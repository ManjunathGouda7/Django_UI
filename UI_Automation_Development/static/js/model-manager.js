/**
 * Model Manager
 * Handles LLM model selection and switching
 */

let availableModels = [];
let currentModel = null;

/**
 * Load available models from backend
 */
async function loadAvailableModels() {
    try {
        const response = await fetch('/api/get-models/');
        const data = await response.json();
        
        if (data.available_models && data.available_models.length > 0) {
            availableModels = data.available_models;
            currentModel = data.current_model;
            
            renderModelSelector();
            showNotification(`✅ Loaded ${availableModels.length} model(s)`, 'success');
        } else {
            showNotification('⚠️ No models available', 'warning');
        }
    } catch (error) {
        console.error('Error loading models:', error);
        showNotification('Failed to load models', 'error');
    }
}

/**
 * Render model selector in UI
 */
function renderModelSelector() {
    const headerLeft = document.querySelector('.header-left');
    if (!headerLeft) return;
    
    // Remove existing selector if present
    const existing = document.getElementById('modelSelector');
    if (existing) existing.remove();
    
    if (availableModels.length === 0) return;
    
    // Create model selector
    const selector = document.createElement('div');
    selector.id = 'modelSelector';
    selector.className = 'model-selector';
    selector.style.marginTop = '10px';
    
    const label = document.createElement('label');
    label.style.fontSize = '12px';
    label.style.opacity = '0.7';
    label.textContent = '🤖 Model: ';
    
    const select = document.createElement('select');
    select.id = 'modelDropdown';
    select.className = 'model-dropdown';
    select.style.padding = '6px 10px';
    select.style.borderRadius = '6px';
    select.style.border = '1px solid #ff6ec4';
    select.style.background = 'rgba(255, 110, 196, 0.1)';
    select.style.color = '#ff6ec4';
    select.style.cursor = 'pointer';
    select.style.fontSize = '12px';
    select.style.fontWeight = '600';
    
    // Add options
    availableModels.forEach(model => {
        const option = document.createElement('option');
        option.value = model;
        option.textContent = model.length > 25 ? model.substring(0, 22) + '...' : model;
        option.selected = model === currentModel;
        select.appendChild(option);
    });
    
    select.addEventListener('change', (e) => {
        switchModel(e.target.value);
    });
    
    label.appendChild(select);
    selector.appendChild(label);
    headerLeft.appendChild(selector);
}

/**
 * Switch to a different model
 * @param {string} modelId - The model ID to switch to
 */
async function switchModel(modelId) {
    if (!modelId || modelId === currentModel) return;
    
    try {
        const response = await fetch('/api/set-model/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ model: modelId })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentModel = modelId;
            showNotification(`✅ Switched to ${modelId}`, 'success');
            
            // Update dropdown
            const select = document.getElementById('modelDropdown');
            if (select) {
                select.value = modelId;
            }
        } else {
            showNotification(`❌ Failed to switch model: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Error switching model:', error);
        showNotification('Error switching model', 'error');
    }
}

/**
 * Show notification message
 * @param {string} message - The message to show
 * @param {string} type - 'success', 'error', 'warning', or 'info'
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notif = document.createElement('div');
    notif.style.position = 'fixed';
    notif.style.top = '20px';
    notif.style.right = '20px';
    notif.style.padding = '12px 20px';
    notif.style.borderRadius = '8px';
    notif.style.fontSize = '13px';
    notif.style.fontWeight = '600';
    notif.style.zIndex = '9999';
    notif.style.animation = 'slideIn 0.3s ease';
    
    // Style based on type
    const styles = {
        success: {
            bg: 'rgba(46, 204, 113, 0.9)',
            text: '#fff'
        },
        error: {
            bg: 'rgba(231, 76, 60, 0.9)',
            text: '#fff'
        },
        warning: {
            bg: 'rgba(243, 156, 18, 0.9)',
            text: '#fff'
        },
        info: {
            bg: 'rgba(52, 152, 219, 0.9)',
            text: '#fff'
        }
    };
    
    const style = styles[type] || styles.info;
    notif.style.background = style.bg;
    notif.style.color = style.text;
    notif.textContent = message;
    
    document.body.appendChild(notif);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notif.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notif.remove(), 300);
    }, 3000);
}

/**
 * Parse timeout error and extract available models
 * @param {string} errorMessage - The error message from bot
 */
function handleTimeoutError(errorMessage) {
    if (errorMessage.includes('Timeout Error')) {
        console.log('Timeout detected, loading alternative models...');
        loadAvailableModels();
        
        // Show alert with available models
        const models = availableModels.map(m => `- ${m}`).join('\n');
        const message = `Your model timed out.\n\nAvailable models:\n${models}\n\n💡 Try switching to a faster model from the dropdown.`;
        
        // Show detailed notification
        const detail = document.createElement('div');
        detail.style.position = 'fixed';
        detail.style.top = '50%';
        detail.style.left = '50%';
        detail.style.transform = 'translate(-50%, -50%)';
        detail.style.background = 'rgba(0, 0, 0, 0.9)';
        detail.style.padding = '30px';
        detail.style.borderRadius = '12px';
        detail.style.border = '2px solid #ff6ec4';
        detail.style.color = '#fff';
        detail.style.maxWidth = '400px';
        detail.style.zIndex = '10000';
        detail.style.fontFamily = 'monospace';
        detail.style.fontSize = '13px';
        detail.style.lineHeight = '1.6';
        detail.style.whiteSpace = 'pre-wrap';
        detail.innerHTML = `<strong>⏱️ Model Timeout</strong><br><br>${message.split('\n').join('<br>')}`;
        
        const overlay = document.createElement('div');
        overlay.style.position = 'fixed';
        overlay.style.top = '0';
        overlay.style.left = '0';
        overlay.style.width = '100%';
        overlay.style.height = '100%';
        overlay.style.background = 'rgba(0, 0, 0, 0.7)';
        overlay.style.zIndex = '9999';
        overlay.onclick = () => {
            overlay.remove();
            detail.remove();
        };
        
        document.body.appendChild(overlay);
        document.body.appendChild(detail);
        
        setTimeout(() => {
            overlay.remove();
            detail.remove();
        }, 8000);
    }
}

/**
 * Check current model status
 */
async function checkModelStatus() {
    try {
        const response = await fetch('/api/status/');
        const data = await response.json();
        
        console.log('Current model:', data.current_model);
        console.log('Available models:', data.available_models);
        
        return data;
    } catch (error) {
        console.error('Error checking status:', error);
    }
}

// Load models on page load
window.addEventListener('load', () => {
    setTimeout(() => {
        loadAvailableModels();
    }, 500);
});
