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

function sendMessage(messageToSend, messageToDisplay) {
    const userInputElement = document.getElementById('userInput');
    let internalMessage;
    let displayMessage;

    // 如果 messageToSend 未定义，说明是用户直接输入，否则是按钮点击
    if (messageToSend === undefined) {
        internalMessage = userInputElement.value.trim();
        displayMessage = internalMessage;
        userInputElement.value = ''; // 清空输入框
    } else {
        internalMessage = messageToSend;
        displayMessage = messageToDisplay;
    }

    if (displayMessage === '') return;

    const chatbox = document.getElementById('chatbox');

    // 创建并显示用户消息气泡
    const userMsgElement = document.createElement('div');
    userMsgElement.className = 'message user-message';
    const p = document.createElement('p');
    p.className = 'message-content';
    p.textContent = displayMessage; // 使用要显示的消息
    const ts = document.createElement('div');
    ts.className = 'timestamp';
    ts.textContent = '今天 ' + getCurrentTimestamp();
    userMsgElement.appendChild(p);
    userMsgElement.appendChild(ts);
    chatbox.appendChild(userMsgElement);

    userInputElement.focus();
    chatbox.scrollTop = chatbox.scrollHeight;

    // 显示打字指示器
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'typing-indicator';
    typingIndicator.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';
    chatbox.appendChild(typingIndicator);
    chatbox.scrollTop = chatbox.scrollHeight;

    document.getElementById('sendBtn').disabled = true;

    // 发送内部消息到后端
    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: internalMessage, user_id: getUserId() })
    })
        .then(response => response.json())
        .then(data => {
            console.log('收到API响应:', data);
            console.log('clarification_options:', data.clarification_options);

            chatbox.removeChild(typingIndicator);
            const aiMsgElement = document.createElement('div');
            aiMsgElement.className = 'message ai-message';

            const messageContent = document.createElement('p');
            messageContent.className = 'message-content';
            // 检查并使用 data.message 或 data.response (优先使用 message)
            const messageText = data.message || data.response || "抱歉，收到空回复。";
            messageContent.innerHTML = formatResponse(messageText);
            aiMsgElement.appendChild(messageContent);

            // 将澄清选项的检查移到消息内容之后
            if (data.clarification_options && data.clarification_options.length > 0) {
                console.log('创建clarification按钮，数量:', data.clarification_options.length);
                const optionsContainer = document.createElement('div');
                optionsContainer.className = 'clarification-options-container';
                data.clarification_options.forEach(option => {
                    console.log('创建按钮:', option.display_text, 'payload:', option.payload);
                    const button = document.createElement('button');
                    button.className = 'clarification-btn';
                    button.textContent = option.display_text;
                    button.dataset.payload = option.payload;
                    button.addEventListener('click', function() {
                        console.log('按钮被点击:', option.display_text);
                        // 传递 payload 和 display_text
                        sendClarificationChoice(option.payload, option.display_text, optionsContainer);
                    });
                    optionsContainer.appendChild(button);
                });
                aiMsgElement.appendChild(optionsContainer);
                console.log('按钮容器已添加到消息元素');
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
                        // 传递 payload 和 display_text
                        sendProductSuggestionChoice(suggestion.payload, suggestion.display_text, suggestionsContainer);
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
    // 快速消息是用户可见的，所以内部消息和显示消息相同
    sendMessage(message, message);
}

function sendClarificationChoice(payload, displayText, optionsContainer) {
    // 禁用所有澄清按钮以防止重复点击
    const buttons = optionsContainer.getElementsByClassName('clarification-btn');
    for (let btn of buttons) {
        btn.disabled = true;
        btn.style.opacity = '0.7';
        btn.style.cursor = 'default';
    }

    // 调用新的 sendMessage，分别传递内部消息和显示消息
    sendMessage(`product_selection:${payload}`, displayText);
}

function sendProductSuggestionChoice(payload, displayText, suggestionsContainer) {
    // 禁用所有产品建议按钮以防止重复点击
    const buttons = suggestionsContainer.getElementsByClassName('product-suggestion-btn');
    for (let btn of buttons) {
        btn.disabled = true;
        btn.style.opacity = '0.7';
        btn.style.cursor = 'default';
    }

    // 调用新的 sendMessage，分别传递内部消息和显示消息
    sendMessage(`product_selection:${payload}`, displayText);
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
