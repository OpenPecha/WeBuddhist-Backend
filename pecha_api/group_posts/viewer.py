"""Simple HTML viewer for testing group posts and real-time comments."""

from fastapi import APIRouter, Query
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
    token: str = Query(...),
):
    """HTML page to view and interact with a post's live comments."""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Post Comments - Live</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
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

            .comments-section {{
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                display: flex;
                flex-direction: column-reverse;
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
                    <div class="status-dot" id="statusDot"></div>
                    <span id="statusText">Connecting...</span>
                </div>
            </div>

            <div class="comments-section" id="commentsSection">
                <div class="loading">
                    <div class="spinner"></div>
                    <p style="margin-top: 12px;">Loading comments...</p>
                </div>
            </div>

            <div class="input-section">
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
            const token = "{token}";

            const statusDot = document.getElementById("statusDot");
            const statusText = document.getElementById("statusText");
            const commentsSection = document.getElementById("commentsSection");
            const commentInput = document.getElementById("commentInput");
            const sendBtn = document.getElementById("sendBtn");
            const charCount = document.getElementById("charCount");

            let ws = null;
            let isConnected = false;

            function updateStatus(connected, message) {{
                isConnected = connected;
                if (connected) {{
                    statusDot.classList.remove("offline");
                    statusDot.textContent = "";
                }} else {{
                    statusDot.classList.add("offline");
                }}
                statusText.textContent = message;
                commentInput.disabled = !connected;
                sendBtn.disabled = !connected;
            }}

            function connectWebSocket() {{
                const wsUrl = `ws://${{window.location.host}}/api/v1/author/groups/${{groupId}}/posts/${{postId}}/comments/live?token=${{token}}`;

                ws = new WebSocket(wsUrl);

                ws.onopen = () => {{
                    updateStatus(true, "🟢 Connected");
                    loadInitialComments();
                }};

                ws.onmessage = (event) => {{
                    const message = JSON.parse(event.data);

                    if (message.type === "comment_created") {{
                        addComment(message.comment);
                    }} else if (message.type === "error") {{
                        showError(message.message);
                    }}
                }};

                ws.onerror = () => {{
                    updateStatus(false, "🔴 Connection error");
                }};

                ws.onclose = () => {{
                    updateStatus(false, "🔴 Disconnected");
                    setTimeout(connectWebSocket, 3000);
                }};
            }}

            function loadInitialComments() {{
                fetch(`/api/v1/author/groups/${{groupId}}/posts/${{postId}}/comments?limit=50`)
                    .then(r => r.json())
                    .then(data => {{
                        commentsSection.innerHTML = "";
                        if (data.comments.length === 0) {{
                            commentsSection.innerHTML = '<div class="comments-empty">No comments yet. Be the first!</div>';
                        }} else {{
                            data.comments.reverse().forEach(c => addComment(c));
                        }}
                    }})
                    .catch(err => showError("Failed to load comments: " + err.message));
            }}

            function addComment(comment) {{
                if (commentsSection.querySelector(".comments-empty")) {{
                    commentsSection.innerHTML = "";
                }}

                const div = document.createElement("div");
                div.className = "comment";

                const date = new Date(comment.created_at).toLocaleString();
                div.innerHTML = `
                    <div class="comment-author">${{comment.user_email}}</div>
                    <div class="comment-text">${{escapeHtml(comment.text)}}</div>
                    <div class="comment-time">${{date}}</div>
                `;

                commentsSection.appendChild(div);
            }}

            function showError(message) {{
                const errorDiv = document.createElement("div");
                errorDiv.className = "error";
                errorDiv.textContent = message;
                commentsSection.insertBefore(errorDiv, commentsSection.firstChild);
                setTimeout(() => errorDiv.remove(), 5000);
            }}

            function sendComment() {{
                const text = commentInput.value.trim();
                if (!text) return;

                if (ws && ws.readyState === WebSocket.OPEN) {{
                    ws.send(JSON.stringify({{
                        type: "comment",
                        text: text
                    }}));
                    commentInput.value = "";
                    charCount.textContent = "";
                }} else {{
                    showError("Not connected. Please wait...");
                }}
            }}

            function escapeHtml(text) {{
                const div = document.createElement("div");
                div.textContent = text;
                return div.innerHTML;
            }}

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

            connectWebSocket();
        </script>
    </body>
    </html>
    """
