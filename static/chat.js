function applyTheme(mode) {
    if (mode === 'dark') {
        document.body.classList.add('dark-mode');
    } else {
        document.body.classList.remove('dark-mode');
    }
}

function escapeHtml(str) {
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function formatResponse(text) {
    let formattedText = escapeHtml(text);
    formattedText = formattedText.replace(/^(-\s+)(\【.*?\】)?(.*?)(:.*)/gm, '<div class="product-item">$1$2$3$4</div>');
    formattedText = formattedText.replace(/\【(当季新鲜|热门好评|精选)\】/g, '<span class="seasonal-tag">$1</span>');
    return formattedText;
}

function getCurrentTimestamp() {
    return new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
}

function getUserId() {
    let userId = localStorage.getItem('fruit_chat_user_id');
    if (!userId) {
        userId = 'user_' + Math.random().toString(36).substring(2, 10);
        localStorage.setItem('fruit_chat_user_id', userId);
    }
    return userId;
}

function sendMessage() {
    const userInputElement = document.getElementById('userInput');
    const message = userInputElement.value.trim();
    if (message === '') return;

    const chatbox = document.getElementById('chatbox');

    const userMsgElement = document.createElement('div');
    userMsgElement.className = 'message user-message';
    const p = document.createElement('p');
    p.className = 'message-content';
    p.textContent = message;
    const ts = document.createElement('div');
    ts.className = 'timestamp';
    ts.textContent = '今天 ' + getCurrentTimestamp();
    userMsgElement.appendChild(p);
    userMsgElement.appendChild(ts);
    chatbox.appendChild(userMsgElement);

    userInputElement.value = '';
    userInputElement.focus();
    chatbox.scrollTop = chatbox.scrollHeight;

    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'typing-indicator';
    typingIndicator.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';
    chatbox.appendChild(typingIndicator);
    chatbox.scrollTop = chatbox.scrollHeight;

    document.getElementById('sendBtn').disabled = true;

    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message, user_id: getUserId() })
    })
        .then(response => response.json())
        .then(data => {
            chatbox.removeChild(typingIndicator);
            const aiMsgElement = document.createElement('div');
            aiMsgElement.className = 'message ai-message';

            const messageContent = document.createElement('p');
            messageContent.className = 'message-content';
            messageContent.innerHTML = formatResponse(data.response);
            aiMsgElement.appendChild(messageContent);

            if (data.clarification_options && data.clarification_options.length > 0) {
                const optionsContainer = document.createElement('div');
                optionsContainer.className = 'clarification-options-container';
                data.clarification_options.forEach(option => {
                    const button = document.createElement('button');
                    button.className = 'clarification-btn';
                    button.textContent = option.display_text;
                    button.dataset.payload = option.payload;
                    button.addEventListener('click', function() {
                        sendClarificationChoice(option.payload, optionsContainer);
                    });
                    optionsContainer.appendChild(button);
                });
                aiMsgElement.appendChild(optionsContainer);
            }

            // 处理产品建议
            if (data.product_suggestions && data.product_suggestions.length > 0) {
                const suggestionsContainer = document.createElement('div');
                suggestionsContainer.className = 'product-suggestions-container';
                data.product_suggestions.forEach(suggestion => {
                    const button = document.createElement('button');
                    button.className = 'product-suggestion-btn'; // 建议使用新的类名以区分样式
                    button.textContent = suggestion.display_text;
                    button.dataset.payload = suggestion.payload;
                    button.addEventListener('click', function() {
                        sendProductSuggestionChoice(suggestion.payload, suggestionsContainer);
                    });
                    suggestionsContainer.appendChild(button);
                });
                aiMsgElement.appendChild(suggestionsContainer);
            }

            const timestamp = document.createElement('div');
            timestamp.className = 'timestamp';
            timestamp.textContent = '今天 ' + getCurrentTimestamp();
            aiMsgElement.appendChild(timestamp);

            chatbox.appendChild(aiMsgElement);
            document.getElementById('sendBtn').disabled = false;
            chatbox.scrollTop = chatbox.scrollHeight;
        })
        .catch(error => {
            console.error('Error:', error);
            if (typingIndicator.parentNode) {
                chatbox.removeChild(typingIndicator);
            }
            const errorMsgElement = document.createElement('div');
            errorMsgElement.className = 'message ai-message';
            errorMsgElement.innerHTML = '<p class="message-content">抱歉，发生了错误，请稍后再试。</p>' +
                '<div class="timestamp">今天 ' + getCurrentTimestamp() + '</div>';
            chatbox.appendChild(errorMsgElement);
            document.getElementById('sendBtn').disabled = false;
            chatbox.scrollTop = chatbox.scrollHeight;
        });
}

function sendQuickMessage(message) {
    document.getElementById('userInput').value = message;
    sendMessage();
}

function sendClarificationChoice(payload, optionsContainer) {
    // 可选：禁用所有澄清按钮以防止重复点击
    const buttons = optionsContainer.getElementsByClassName('clarification-btn');
    for (let btn of buttons) {
        btn.disabled = true;
        btn.style.opacity = '0.7';
        btn.style.cursor = 'default';
    }

    // 将 payload 作为新消息发送
    const userInputElement = document.getElementById('userInput');
    userInputElement.value = `product_selection:${payload}`; // 使用约定的前缀
    sendMessage();
}

function sendProductSuggestionChoice(payload, suggestionsContainer) {
    // 禁用所有产品建议按钮以防止重复点击
    const buttons = suggestionsContainer.getElementsByClassName('product-suggestion-btn');
    for (let btn of buttons) {
        btn.disabled = true;
        btn.style.opacity = '0.7'; // 与澄清按钮保持一致的禁用样式
        btn.style.cursor = 'default';
    }

    // 将 payload 作为新消息发送
    const userInputElement = document.getElementById('userInput');
    userInputElement.value = payload; // 直接发送 payload，后端应能处理
    sendMessage();
}

document.addEventListener('DOMContentLoaded', function () {
    const savedTheme = localStorage.getItem('theme');
    applyTheme(savedTheme);

    const toggleBtn = document.getElementById('themeToggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', function () {
            const isDark = document.body.classList.toggle('dark-mode');
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
        });
    }

    const welcomeTime = document.getElementById('welcomeTime');
    if (welcomeTime) {
        welcomeTime.textContent = getCurrentTimestamp();
    }

    document.getElementById('userInput').focus();
    document.getElementById('userInput').addEventListener('keypress', function (event) {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });
});
