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
            aiMsgElement.innerHTML = '<p class="message-content">' + formatResponse(data.response) + '</p>' +
                '<div class="timestamp">今天 ' + getCurrentTimestamp() + '</div>';
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
