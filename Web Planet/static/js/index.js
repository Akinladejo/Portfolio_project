// Toggle the chatbot window
function toggleChat() {
    const chatbotWindow = document.getElementById('chatbot-window');
    chatbotWindow.style.display = chatbotWindow.style.display === 'block' ? 'none' : 'block';

    // Show welcome message on first open
    if (chatbotWindow.style.display === 'block' && !document.getElementById('welcome-message')) {
        const messagesDiv = document.getElementById('messages');
        const welcomeMessage = document.createElement('div');
        welcomeMessage.id = 'welcome-message';
        welcomeMessage.className = 'message bot-message';
        welcomeMessage.textContent = 'Welcome to Web Planet, how may I assist you?';
        messagesDiv.appendChild(welcomeMessage);
    }
}

// Send a message
function sendMessage() {
    const userInput = document.getElementById('user-input');
    const messagesDiv = document.getElementById('messages');

    if (userInput.value.trim()) {
        // Add user message
        const userMessage = document.createElement('div');
        userMessage.className = 'message user-message';
        userMessage.textContent = userInput.value;
        messagesDiv.appendChild(userMessage);

        // Clear input field
        userInput.value = '';

        // Scroll to the latest message
        messagesDiv.scrollTop = messagesDiv.scrollHeight;

        // Respond with a generic bot message
        setTimeout(() => {
            const botMessage = document.createElement('div');
            botMessage.className = 'message bot-message';
            botMessage.textContent = 'Thank you for reaching out. How can I assist you further?';
            messagesDiv.appendChild(botMessage);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }, 1000);
    }
}
