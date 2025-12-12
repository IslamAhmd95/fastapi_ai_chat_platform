# just for testing new concepts like websocket and redis

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi_limiter.depends import WebSocketRateLimiter


html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var client_id = Date.now()
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`ws://localhost:8000/ws/chat/${client_id}`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        await self.send_personal_message("Welcome to the chat! We have {} users online.".format(len(self.active_connections)), websocket)


    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        inactive_connections = []

        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except RuntimeError:
                print(f"Skipping connection: {connection.client}")
                inactive_connections.append(connection)

        for connection in inactive_connections:
            self.active_connections.remove(connection)


manager = ConnectionManager()


router = APIRouter(
    prefix="/ws",
)

@router.get("/")
async def get():
    return HTMLResponse(html)


@router.websocket("/chat/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket) # The moment we agree to connect
    ratelimit = WebSocketRateLimiter(times=1, seconds=50)

    try:
        await manager.broadcast(f"Client #{client_id} joins the chat")
        while True:
            data = await websocket.receive_text()

            try:
                await ratelimit(websocket, context_key=f"ws:{client_id}")
            except HTTPException:
                await manager.send_personal_message("⚠️ Rate limit exceeded! Please slow down.", websocket)
                continue

            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id} says: {data}")

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")









"""
```
try:
    await ratelimit(websocket, context_key=f"ws:{client_id}")
except HTTPException:
    await manager.send_personal_message("⚠️ Rate limit exceeded!", websocket)
    continue
```

**What actually happens in Redis:**

When `client_id = 2`:
- **Key**: `"ws:2"` ✅ (you got this right!)
- **Value**: Not just a simple counter, but a **list of timestamps** of recent requests

**Behind the scenes:**
1. **First request**: Redis stores `ws:2 = [timestamp1]` → ✅ Allowed
2. **Second request within 50 seconds**: Redis checks `ws:2 = [timestamp1]`, counts 1 request in the last 50 seconds → ❌ **HTTPException raised** (limit exceeded!)
3. **Request after 50 seconds**: Redis removes old timestamps, `ws:2 = []` or expired → ✅ Allowed again

**The sliding window concept:**
```
Timeline:
0s -----> 10s -----> 50s -----> 60s
|         |          |          |
Req1 ✅   Req2 ❌   Req3 ✅    Req4 ✅
         (too soon!) (50s passed, OK!)

"""

""""
Redis on terminal

```bash
redis-cli
127.0.0.1:6379> KEYS *
# You'll see keys like "ws:2" when someone is rate-limited

127.0.0.1:6379> GET "ws:2"
# You'll see the timestamp data

127.0.0.1:6379> TTL "ws:2"
# Shows how many seconds until the key expires
```
"""