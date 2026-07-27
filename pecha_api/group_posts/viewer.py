"""HTML viewer for group post live comments - token-based auth."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from uuid import UUID

viewer_router = APIRouter(
    prefix="/view",
    tags=["Group Posts Viewer"],
)


@viewer_router.get(
    "/groups/{group_id}/posts/{post_id}",
    response_class=HTMLResponse,
)
def view_post_comments(
    group_id: UUID,
    post_id: UUID,
):
    """Live comment viewer - accepts token via input field in the page."""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Live Comments Viewer</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}

            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
                display: flex;
                flex-direction: column;
                height: 90vh;
            }}

            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-bottom: 2px solid rgba(0,0,0,0.1);
            }}

            .header h1 {{
                font-size: 24px;
                margin-bottom: 8px;
            }}

            .status {{
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 14px;
            }}

            .status-dot {{
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background: #10b981;
                animation: pulse 2s infinite;
            }}

            .status-dot.offline {{
                background: #ef4444;
                animation: none;
            }}

            @keyframes pulse {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.5; }}
            }}

            .auth-section {{
                padding: 20px;
                border-bottom: 1px solid #e5e7eb;
                background: #f9fafb;
                display: flex;
                gap: 10px;
                align-items: flex-end;
            }}

            .auth-section input {{
                flex: 1;
                padding: 12px;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                font-size: 14px;
                font-family: monospace;
            }}

            .auth-section input:focus {{
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }}

            .auth-section button {{
                padding: 12px 24px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 600;
                transition: transform 0.2s, box-shadow 0.2s;
                white-space: nowrap;
            }}

            .auth-section button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }}

            .auth-section button:disabled {{
                opacity: 0.5;
                cursor: not-allowed;
                transform: none;
            }}

            .comments-section {{
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                display: flex;
                flex-direction: column-reverse;
                display: none;
            }}

            .comments-section.active {{
                display: flex;
            }}

            .comment {{
                margin-bottom: 16px;
                padding: 12px;
                background: #f9fafb;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }}

            .comment-author {{
                font-weight: 600;
                color: #1f2937;
                margin-bottom: 4px;
                font-size: 14px;
            }}

            .comment-text {{
                color: #4b5563;
                margin-bottom: 6px;
                line-height: 1.4;
                word-break: break-word;
            }}

            .comment-time {{
                font-size: 12px;
                color: #9ca3af;
            }}

            .comments-empty {{
                text-align: center;
                color: #9ca3af;
                padding: 40px 20px;
            }}

            .input-section {{
                border-top: 1px solid #e5e7eb;
                padding: 16px;
                background: #f9fafb;
                display: flex;
                gap: 10px;
                display: none;
            }}

            .input-section.active {{
                display: flex;
            }}

            .input-section textarea {{
                flex: 1;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                padding: 12px;
                font-family: inherit;
                font-size: 14px;
                resize: none;
                max-height: 100px;
            }}

            .input-section textarea:focus {{
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }}

            .input-section button {{
                padding: 12px 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 600;
                transition: transform 0.2s, box-shadow 0.2s;
            }}

            .input-section button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }}

            .input-section button:disabled {{
                opacity: 0.5;
                cursor: not-allowed;
                transform: none;
            }}

            .error {{
                background: #fee2e2;
                color: #991b1b;
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 12px;
                border-left: 4px solid #dc2626;
            }}

            .loading {{
                text-align: center;
                padding: 20px;
                color: #9ca3af;
            }}

            .spinner {{
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 3px solid #e5e7eb;
                border-top-color: #667eea;
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
            }}

            @keyframes spin {{
                to {{ transform: rotate(360deg); }}
            }}

            .char-count {{
                font-size: 12px;
                color: #9ca3af;
                margin-top: 4px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>💬 Live Comments</h1>
                <div class="status">
                    <div class="status-dot offline" id="statusDot"></div>
                    <span id="statusText">Not connected</span>
                </div>
            </div>

            <div class="auth-section">
                <input
                    type="password"
                    id="tokenInput"
                    placeholder="Enter your bearer token"
                    autocomplete="off"
                />
                <button id="connectBtn">Connect</button>
            </div>

            <div class="comments-section" id="commentsSection">
                <div class="loading">
                    <div class="spinner"></div>
                    <p style="margin-top: 12px;">Loading comments...</p>
                </div>
            </div>

            <div class="input-section" id="inputSection">
                <textarea
                    id="commentInput"
                    placeholder="Write a comment... (max 5000 characters)"
                    maxlength="5000"
                    disabled
                ></textarea>
                <button id="sendBtn" disabled>Send</button>
                <div class="char-count" id="charCount"></div>
            </div>
        </div>

        <script>
            const groupId = "{group_id}";
            const postId = "{post_id}";
            const apiBase = window.location.origin + "/api/v1";

            let ws = null;
            let token = null;

            const tokenInput = document.getElementById("tokenInput");
            const connectBtn = document.getElementById("connectBtn");
            const statusDot = document.getElementById("statusDot");
            const statusText = document.getElementById("statusText");
            const commentsSection = document.getElementById("commentsSection");
            const inputSection = document.getElementById("inputSection");
            const commentInput = document.getElementById("commentInput");
            const sendBtn = document.getElementById("sendBtn");
            const charCount = document.getElementById("charCount");

            function updateStatus(connected, message) {{
                if (connected) {{
                    statusDot.classList.remove("offline");
                }} else {{
                    statusDot.classList.add("offline");
                }}
                statusText.textContent = message;
                commentInput.disabled = !connected;
                sendBtn.disabled = !connected;
            }}

            function showAuth() {{
                commentsSection.classList.remove("active");
                inputSection.classList.remove("active");
                updateStatus(false, "Not connected");
            }}

            function showComments() {{
                commentsSection.classList.add("active");
                inputSection.classList.add("active");
            }}

            function connectWebSocket() {{
                if (!token) {{
                    showError("Token is required");
                    return;
                }}

                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const encodedToken = encodeURIComponent(token);
                const wsUrl = `${{protocol}}//${{window.location.host}}/api/v1/author/groups/${{groupId}}/posts/${{postId}}/comments/live?token=${{encodedToken}}`;

                console.log("[WebSocket Debug]");
                console.log("  Token length:", token.length);
                console.log("  WebSocket URL:", wsUrl);

                ws = new WebSocket(wsUrl);

                ws.onopen = () => {{
                    updateStatus(true, "Connected");
                    loadInitialComments();
                }};

                ws.onmessage = (event) => {{
                    console.log("[WebSocket message received]", event.data.substring(0, 100));
                    try {{
                        const message = JSON.parse(event.data);
                        console.log("[Parsed message type]:", message.type);

                        if (message.type === "comment_created") {{
                            console.log("[Broadcasting comment to UI]");
                            addComment(message.comment);
                        }} else if (message.type === "error") {{
                            console.error("[Server error]", message.message);
                            showError(message.message);
                        }} else {{
                            console.warn("[Unknown message type]", message.type);
                        }}
                    }} catch (e) {{
                        console.error("[Failed to parse message]", e.message);
                    }}
                }};

                ws.onerror = (event) => {{
                    console.error("[WebSocket Error]", event);
                    updateStatus(false, "Connection error");
                }};

                ws.onclose = (event) => {{
                    console.log("[WebSocket Closed]", event.code, event.reason);
                    updateStatus(false, "Disconnected");
                    setTimeout(connectWebSocket, 3000);
                }};
            }}

            function loadInitialComments() {{
                console.log("[Loading initial comments]");
                fetch(`${{apiBase}}/author/groups/${{groupId}}/posts/${{postId}}/comments?limit=50`)
                    .then(r => {{
                        console.log("  HTTP Status:", r.status);
                        return r.json();
                    }})
                    .then(data => {{
                        console.log("  Comments loaded:", data.comments.length);
                        commentsSection.innerHTML = "";
                        if (data.comments.length === 0) {{
                            commentsSection.innerHTML = '<div class="comments-empty">No comments yet. Be the first!</div>';
                        }} else {{
                            data.comments.reverse().forEach(c => addComment(c));
                        }}
                    }})
                    .catch(err => {{
                        console.error("  Failed to load comments:", err);
                        showError("Failed to load comments: " + err.message);
                    }});
            }}

            function addComment(comment) {{
                console.log("[Adding comment]", comment.user_email, ":", comment.text.substring(0, 50));
                if (commentsSection.querySelector(".comments-empty")) {{
                    console.log("[Removing 'no comments' message]");
                    commentsSection.innerHTML = "";
                }}

                const div = document.createElement("div");
                div.className = "comment";

                const date = new Date(comment.created_at).toLocaleString();
                div.innerHTML = `
                    <div class="comment-author">${{escapeHtml(comment.user_email)}}</div>
                    <div class="comment-text">${{escapeHtml(comment.text)}}</div>
                    <div class="comment-time">${{date}}</div>
                `;

                commentsSection.appendChild(div);
                console.log("[Comment added to DOM]");
            }}

            function sendComment() {{
                const text = commentInput.value.trim();
                if (!text) return;

                if (ws && ws.readyState === WebSocket.OPEN) {{
                    console.log("[Sending comment] Text length:", text.length);
                    ws.send(JSON.stringify({{
                        type: "comment",
                        text: text
                    }}));
                    console.log("[Comment sent] Waiting for broadcast...");
                    commentInput.value = "";
                    charCount.textContent = "";
                }} else {{
                    console.error("[Send error] WebSocket not open. State:", ws ? ws.readyState : "null");
                    showError("Not connected. Please wait...");
                }}
            }}

            function escapeHtml(text) {{
                const div = document.createElement("div");
                div.textContent = text;
                return div.innerHTML;
            }}

            function showError(message) {{
                const errorDiv = document.createElement("div");
                errorDiv.className = "error";
                errorDiv.textContent = message;
                commentsSection.insertBefore(errorDiv, commentsSection.firstChild);
                setTimeout(() => errorDiv.remove(), 5000);
            }}

            connectBtn.addEventListener("click", () => {{
                token = tokenInput.value.trim();
                if (!token) {{
                    showError("Please enter a token");
                    return;
                }}
                connectBtn.disabled = true;
                connectBtn.textContent = "Connecting...";
                updateStatus(false, "Connecting...");
                showComments();
                connectWebSocket();
            }});

            tokenInput.addEventListener("keydown", (e) => {{
                if (e.key === "Enter") {{
                    connectBtn.click();
                }}
            }});

            commentInput.addEventListener("input", () => {{
                const len = commentInput.value.length;
                charCount.textContent = len > 0 ? `${{len}}/5000` : "";
            }});

            sendBtn.addEventListener("click", sendComment);

            commentInput.addEventListener("keydown", (e) => {{
                if (e.key === "Enter" && e.ctrlKey) {{
                    sendComment();
                }}
            }});

            showAuth();
        </script>
    </body>
    </html>
    """
