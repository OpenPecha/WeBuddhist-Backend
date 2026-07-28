"""HTML viewer for testing the chat system - token-based auth.

Lets a tester paste a bearer token, pick GROUP or DIRECT mode, enter the
target group_id/user_id, and start chatting in that room (auto-created on
first message, exactly like a real client)."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

chat_viewer_router = APIRouter(
    prefix="/view",
    tags=["Chat Viewer"],
)


@chat_viewer_router.get(
    "/chat",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def view_chat():
    """Live chat test page - accepts token, group_id/user_id via input fields."""
    return _CHAT_VIEWER_HTML


_CHAT_VIEWER_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat Test Viewer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 640px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: 90vh;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
        }

        .header h1 { font-size: 22px; margin-bottom: 8px; }

        .status { display: flex; align-items: center; gap: 8px; font-size: 14px; }

        .status-dot {
            width: 12px; height: 12px; border-radius: 50%;
            background: #10b981; animation: pulse 2s infinite;
        }
        .status-dot.offline { background: #ef4444; animation: none; }

        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

        .setup-section {
            padding: 20px;
            border-bottom: 1px solid #e5e7eb;
            background: #f9fafb;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .setup-row { display: flex; gap: 10px; align-items: center; }

        .setup-section input, .setup-section select {
            flex: 1;
            padding: 12px;
            border: 1px solid #d1d5db;
            border-radius: 8px;
            font-size: 14px;
            font-family: inherit;
        }

        .setup-section input[type="password"] { font-family: monospace; }

        .setup-section input:focus, .setup-section select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .setup-section button {
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            white-space: nowrap;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .setup-section button:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3); }
        .setup-section button:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

        .room-label { font-size: 12px; color: #6b7280; padding: 0 20px; }

        .messages-section {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: none;
            flex-direction: column;
        }

        .messages-section.active { display: flex; }

        .message {
            margin-bottom: 12px;
            padding: 10px 14px;
            background: #f3f4f6;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            max-width: 80%;
        }

        .message.mine {
            align-self: flex-end;
            background: #ede9fe;
            border-left: none;
            border-right: 4px solid #764ba2;
        }

        .message-sender { font-weight: 600; color: #1f2937; margin-bottom: 4px; font-size: 13px; }
        .message-body { color: #374151; line-height: 1.4; word-break: break-word; }
        .message-time { font-size: 11px; color: #9ca3af; margin-top: 4px; }

        .messages-empty { text-align: center; color: #9ca3af; padding: 40px 20px; }

        .typing-indicator {
            padding: 4px 20px;
            font-size: 13px;
            color: #6b7280;
            font-style: italic;
            min-height: 22px;
            display: none;
        }
        .typing-indicator.active { display: block; }

        .input-section {
            border-top: 1px solid #e5e7eb;
            padding: 16px;
            background: #f9fafb;
            gap: 10px;
            display: none;
        }
        .input-section.active { display: flex; }

        .input-section textarea {
            flex: 1;
            border: 1px solid #d1d5db;
            border-radius: 8px;
            padding: 12px;
            font-family: inherit;
            font-size: 14px;
            resize: none;
            max-height: 100px;
        }

        .input-section textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .input-section button {
            padding: 12px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .input-section button:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3); }
        .input-section button:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

        .error {
            background: #fee2e2;
            color: #991b1b;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 12px;
            border-left: 4px solid #dc2626;
        }

        .loading { text-align: center; padding: 20px; color: #9ca3af; }

        .spinner {
            display: inline-block;
            width: 20px; height: 20px;
            border: 3px solid #e5e7eb;
            border-top-color: #667eea;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Chat Test Viewer</h1>
            <div class="status">
                <div class="status-dot offline" id="statusDot"></div>
                <span id="statusText">Not connected</span>
            </div>
        </div>

        <div class="setup-section" id="setupSection">
            <div class="setup-row">
                <input type="password" id="tokenInput" placeholder="Enter your bearer token" autocomplete="off" />
            </div>
            <div class="setup-row">
                <select id="modeSelect">
                    <option value="group">Group chat (group_id)</option>
                    <option value="direct">Direct message (user_id)</option>
                </select>
                <input type="text" id="targetInput" placeholder="Enter group_id or user_id (UUID)" />
                <button id="connectBtn">Start Chat</button>
            </div>
        </div>

        <div class="room-label" id="roomLabel"></div>

        <div class="messages-section" id="messagesSection">
            <div class="loading"><div class="spinner"></div></div>
        </div>

        <div class="typing-indicator" id="typingIndicator"></div>

        <div class="input-section" id="inputSection">
            <textarea id="messageInput" placeholder="Type a message... (max 4000 characters)" maxlength="4000" disabled></textarea>
            <button id="sendBtn" disabled>Send</button>
        </div>
    </div>

    <script>
        const apiBase = window.location.origin + "/api/v1";

        let ws = null;
        let token = null;
        let roomId = null;
        let myEmail = null;
        let typingTimeout = null;
        let lastTypingSent = false;

        const tokenInput = document.getElementById("tokenInput");
        const modeSelect = document.getElementById("modeSelect");
        const targetInput = document.getElementById("targetInput");
        const connectBtn = document.getElementById("connectBtn");
        const statusDot = document.getElementById("statusDot");
        const statusText = document.getElementById("statusText");
        const roomLabel = document.getElementById("roomLabel");
        const messagesSection = document.getElementById("messagesSection");
        const typingIndicator = document.getElementById("typingIndicator");
        const inputSection = document.getElementById("inputSection");
        const messageInput = document.getElementById("messageInput");
        const sendBtn = document.getElementById("sendBtn");

        function updateStatus(connected, message) {
            statusDot.classList.toggle("offline", !connected);
            statusText.textContent = message;
            messageInput.disabled = !connected;
            sendBtn.disabled = !connected;
        }

        function showChat() {
            messagesSection.classList.add("active");
            inputSection.classList.add("active");
        }

        function decodeJwtEmail(jwt) {
            try {
                const payload = JSON.parse(atob(jwt.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
                return payload.email || null;
            } catch (e) {
                return null;
            }
        }

        function connectWebSocket() {
            const mode = modeSelect.value;
            const target = targetInput.value.trim();
            if (!target) {
                showError("Please enter a group_id or user_id");
                connectBtn.disabled = false;
                connectBtn.textContent = "Start Chat";
                return;
            }

            const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
            const encodedToken = encodeURIComponent(token);
            const param = mode === "group" ? `group_id=${encodeURIComponent(target)}` : `receiver_id=${encodeURIComponent(target)}`;
            const wsUrl = `${protocol}//${window.location.host}/api/v1/chat/live?token=${encodedToken}&${param}`;

            ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                updateStatus(true, "Connected");
            };

            ws.onmessage = (event) => {
                let message;
                try {
                    message = JSON.parse(event.data);
                } catch (e) {
                    return;
                }

                if (message.type === "room_info") {
                    roomId = message.room_id;
                    roomLabel.textContent = `Room: ${roomId}`;
                    showChat();
                    loadHistory();
                } else if (message.type === "message_created") {
                    addMessage(message.message);
                    setTyping(false, message.message.sender_email);
                } else if (message.type === "typing") {
                    if (message.email !== myEmail) {
                        setTyping(message.is_typing, message.email);
                    }
                } else if (message.type === "error") {
                    showError(message.message);
                }
            };

            ws.onerror = () => {
                updateStatus(false, "Connection error");
            };

            ws.onclose = () => {
                updateStatus(false, "Disconnected");
            };
        }

        function loadHistory() {
            fetch(`${apiBase}/chat/rooms/${roomId}/messages?limit=50`, {
                headers: { "Authorization": `Bearer ${token}` }
            })
                .then(r => r.json())
                .then(data => {
                    messagesSection.innerHTML = "";
                    if (data.messages.length === 0) {
                        messagesSection.innerHTML = '<div class="messages-empty">No messages yet. Say hello!</div>';
                    } else {
                        data.messages.slice().reverse().forEach(m => addMessage(m));
                    }
                })
                .catch(err => showError("Failed to load history: " + err.message));
        }

        function addMessage(message) {
            if (messagesSection.querySelector(".messages-empty")) {
                messagesSection.innerHTML = "";
            }

            const div = document.createElement("div");
            const isMine = message.sender_email === myEmail;
            div.className = "message" + (isMine ? " mine" : "");

            const date = new Date(message.created_at).toLocaleString();
            div.innerHTML = `
                <div class="message-sender">${escapeHtml(message.sender_email)}</div>
                <div class="message-body">${escapeHtml(message.body)}</div>
                <div class="message-time">${date}</div>
            `;

            messagesSection.appendChild(div);
            messagesSection.scrollTop = messagesSection.scrollHeight;
        }

        function setTyping(isTyping, email) {
            if (isTyping) {
                typingIndicator.textContent = `${email} is typing...`;
                typingIndicator.classList.add("active");
            } else {
                typingIndicator.classList.remove("active");
            }
        }

        function sendMessage() {
            const body = messageInput.value.trim();
            if (!body) return;

            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: "message", body: body }));
                messageInput.value = "";
                sendTypingState(false);
            } else {
                showError("Not connected. Please wait...");
            }
        }

        function sendTypingState(isTyping) {
            if (isTyping === lastTypingSent) return;
            lastTypingSent = isTyping;
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: "typing", is_typing: isTyping }));
            }
        }

        function escapeHtml(text) {
            const div = document.createElement("div");
            div.textContent = text;
            return div.innerHTML;
        }

        function showError(message) {
            const errorDiv = document.createElement("div");
            errorDiv.className = "error";
            errorDiv.textContent = message;
            messagesSection.insertBefore(errorDiv, messagesSection.firstChild);
            setTimeout(() => errorDiv.remove(), 5000);
        }

        connectBtn.addEventListener("click", () => {
            token = tokenInput.value.trim();
            if (!token) {
                showError("Please enter a token");
                return;
            }
            myEmail = decodeJwtEmail(token);
            connectBtn.disabled = true;
            connectBtn.textContent = "Connecting...";
            updateStatus(false, "Connecting...");
            connectWebSocket();
        });

        targetInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") connectBtn.click();
        });

        sendBtn.addEventListener("click", sendMessage);

        messageInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        messageInput.addEventListener("input", () => {
            sendTypingState(true);
            clearTimeout(typingTimeout);
            typingTimeout = setTimeout(() => sendTypingState(false), 2000);
        });

        updateStatus(false, "Not connected");
    </script>
</body>
</html>
"""
