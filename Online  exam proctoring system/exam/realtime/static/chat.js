document.addEventListener('DOMContentLoaded', function() {
    const roomName = "{{ room_name }}";
    const chatSocket = new WebSocket(
        'ws://' + window.location.hostname + ':8000/ws/chat/' + roomName + '/'
    );

    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        const chatLog = document.querySelector('#chat-log');
        
        if (!data.sender || data.sender !== roomName) {
            if (!chatLog.innerHTML.includes(data.message)) {
                chatLog.innerHTML += '<div class="received-message">' + data.message + '</div>';
                chatLog.scrollTop = chatLog.scrollHeight;
            }
        }
    };

    chatSocket.onclose = function(e) {
        console.error('Chat socket closed unexpectedly');
    };

    const messageInputDom = document.querySelector('#chat-message-input');
    if (messageInputDom) {
        messageInputDom.focus();
        messageInputDom.onkeyup = function(e) {
            if (e.keyCode === 13) {  // Enter key
                document.querySelector('#chat-message-submit').click();
            }
        };
    }

    const chatMessageSubmit = document.querySelector('#chat-message-submit');
    if (chatMessageSubmit) {
        chatMessageSubmit.onclick = function(e) {
            e.preventDefault();
            const messageInputDom = document.querySelector('#chat-message-input');
            const message = messageInputDom.value;
            if (message.trim()) {
                const chatLog = document.querySelector('#chat-log');
                chatLog.innerHTML += '<div class="sent-message">' + message + '</div>';
                chatLog.scrollTop = chatLog.scrollHeight;
                if (chatSocket.readyState === WebSocket.OPEN) {
                    chatSocket.send(JSON.stringify({
                        'message': message,
                        'sender': roomName
                    }));
                } else {
                    console.error('WebSocket is not open. Message not sent.');
                }
                messageInputDom.value = '';
            }
        };
    }
});
