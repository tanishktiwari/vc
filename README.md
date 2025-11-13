# Video Conferencing Backend

A FastAPI-based backend for a Zoom-like video conferencing application with WebRTC signaling support.

## Features

- ✅ Create and manage video conference rooms
- ✅ WebSocket-based signaling for WebRTC (SDP offers/answers, ICE candidates)
- ✅ Real-time message broadcasting to all participants in a room
- ✅ Automatic cleanup of empty rooms
- ✅ CORS enabled for frontend integration
- ✅ RESTful API for room management
- ✅ Comprehensive error handling

## Project Structure

```
VC/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── models.py            # Pydantic models for request/response
│   ├── room_manager.py      # Room management logic
│   └── websocket_handler.py # WebSocket connection and signaling handler
├── main.py                  # FastAPI application entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Installation

1. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Server

### Development Mode (with auto-reload):
```bash
python main.py
```

### Production Mode:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The server will start on `http://localhost:8000`

## API Endpoints

### REST Endpoints

#### 1. **GET /** - Root endpoint
   - Returns API information
   - **Example**: `GET http://localhost:8000/`

#### 2. **POST /create-room** - Create a new room
   - Creates a new video conference room
   - Returns room ID and join link
   - **Example**: `POST http://localhost:8000/create-room`
   - **Response**:
     ```json
     {
       "room_id": "550e8400-e29b-41d4-a716-446655440000",
       "join_link": "/room/550e8400-e29b-41d4-a716-446655440000",
       "message": "Room 550e8400-e29b-41d4-a716-446655440000 created successfully"
     }
     ```

#### 3. **GET /rooms** - List all active rooms
   - Returns list of all active rooms with participant counts
   - **Example**: `GET http://localhost:8000/rooms`
   - **Response**:
     ```json
     [
       {
         "room_id": "550e8400-e29b-41d4-a716-446655440000",
         "participant_count": 2,
         "created_at": "2024-01-15T10:30:00"
       }
     ]
     ```

#### 4. **GET /rooms/{room_id}** - Get room information
   - Returns detailed information about a specific room
   - **Example**: `GET http://localhost:8000/rooms/550e8400-e29b-41d4-a716-446655440000`

### WebSocket Endpoint

#### **WS /ws/{room_id}** - WebRTC signaling endpoint
   - Establishes WebSocket connection for signaling
   - Handles SDP offers/answers and ICE candidates
   - **URL**: `ws://localhost:8000/ws/{room_id}`

## WebSocket Message Format

### Client → Server Messages

#### 1. **SDP Offer**
```json
{
  "type": "offer",
  "room_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "sdp": "v=0\r\no=- 123456789 123456789 IN IP4 127.0.0.1\r\n...",
    "type": "offer"
  }
}
```

#### 2. **SDP Answer**
```json
{
  "type": "answer",
  "room_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "sdp": "v=0\r\no=- 987654321 987654321 IN IP4 127.0.0.1\r\n...",
    "type": "answer"
  }
}
```

#### 3. **ICE Candidate**
```json
{
  "type": "ice-candidate",
  "room_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "candidate": "candidate:1 1 UDP 2130706431 192.168.1.1 54321 typ host",
    "sdpMLineIndex": 0,
    "sdpMid": "0"
  }
}
```

### Server → Client Messages

#### 1. **Connection Confirmation**
```json
{
  "type": "connected",
  "user_id": "user-uuid",
  "room_id": "room-uuid",
  "message": "Successfully connected to room"
}
```

#### 2. **User Joined**
```json
{
  "type": "user-joined",
  "user_id": "new-user-uuid",
  "room_id": "room-uuid"
}
```

#### 3. **User Left**
```json
{
  "type": "user-left",
  "user_id": "user-uuid",
  "room_id": "room-uuid"
}
```

#### 4. **Signaling Message (Broadcast)**
```json
{
  "type": "offer",
  "room_id": "room-uuid",
  "sender_id": "sender-uuid",
  "data": { ... }
}
```

#### 5. **Error**
```json
{
  "type": "error",
  "message": "Error description"
}
```

## Testing the Backend

### 1. Testing REST Endpoints

#### Using cURL:

**Create a room:**
```bash
curl -X POST http://localhost:8000/create-room
```

**List rooms:**
```bash
curl http://localhost:8000/rooms
```

**Get room info:**
```bash
curl http://localhost:8000/rooms/{room_id}
```

#### Using Postman:

1. Create a new request
2. Set method to `POST`
3. URL: `http://localhost:8000/create-room`
4. Send request
5. Copy the `room_id` from the response

### 2. Testing WebSocket Connections

#### Option 1: Using Postman

1. **Create a room** (using REST endpoint above)
2. **Open Postman** → New → WebSocket Request
3. **URL**: `ws://localhost:8000/ws/{room_id}` (replace `{room_id}` with actual room ID)
4. **Connect**
5. You should receive a `connected` message with your `user_id`

**Send a test message:**
```json
{
  "type": "join",
  "room_id": "your-room-id"
}
```

**Open a second WebSocket connection** to the same room to test broadcasting:
- Messages sent from one connection will be received by all other connections in the same room

#### Option 2: Using Python Script

Create a test file `test_websocket.py`:

```python
import asyncio
import websockets
import json

async def test_websocket():
    room_id = "your-room-id-here"  # Replace with actual room ID
    uri = f"ws://localhost:8000/ws/{room_id}"
    
    async with websockets.connect(uri) as websocket:
        # Receive connection confirmation
        response = await websocket.recv()
        print(f"Received: {response}")
        
        # Send a test message
        message = {
            "type": "join",
            "room_id": room_id
        }
        await websocket.send(json.dumps(message))
        print(f"Sent: {message}")
        
        # Keep listening for messages
        while True:
            try:
                response = await websocket.recv()
                print(f"Received: {response}")
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
                break

asyncio.run(test_websocket())
```

Run it:
```bash
pip install websockets
python test_websocket.py
```

#### Option 3: Using Browser Console

Open browser console (F12) and run:

```javascript
const roomId = 'your-room-id-here'; // Replace with actual room ID
const ws = new WebSocket(`ws://localhost:8000/ws/${roomId}`);

ws.onopen = () => {
    console.log('Connected');
};

ws.onmessage = (event) => {
    console.log('Received:', JSON.parse(event.data));
};

ws.onerror = (error) => {
    console.error('Error:', error);
};

ws.onclose = () => {
    console.log('Disconnected');
};

// Send a test message
setTimeout(() => {
    ws.send(JSON.stringify({
        type: 'join',
        room_id: roomId
    }));
}, 1000);
```

### 3. Testing Multiple Clients

1. **Create a room** using the REST API
2. **Open multiple WebSocket connections** to the same room (using different tools/clients)
3. **Send a message** from one client
4. **Verify** that all other clients receive the message

## Architecture Explanation

### Room Management (`app/room_manager.py`)

The `RoomManager` class handles:
- **Room Creation**: Generates unique room IDs using UUID
- **Participant Tracking**: Maintains a set of user IDs per room
- **Room Cleanup**: Automatically removes empty rooms
- **Room Listing**: Provides information about all active rooms

**Key Methods:**
- `create_room()`: Creates a new room and returns its ID
- `join_room(room_id, user_id)`: Adds a user to a room
- `leave_room(room_id, user_id)`: Removes a user from a room
- `get_all_rooms()`: Returns list of all active rooms

### WebSocket Handler (`app/websocket_handler.py`)

The `ConnectionManager` class manages:
- **Connection Tracking**: Maps WebSocket connections to rooms and users
- **Message Broadcasting**: Sends messages to all participants in a room
- **Signaling Logic**: Handles WebRTC signaling messages (SDP, ICE candidates)
- **Error Handling**: Manages disconnections gracefully

**Key Methods:**
- `connect(websocket, room_id)`: Establishes a WebSocket connection
- `disconnect(websocket)`: Removes a connection and cleans up
- `handle_signaling_message(websocket, message)`: Processes and broadcasts signaling messages
- `broadcast_to_room(room_id, message)`: Sends message to all room participants

### Main Application (`main.py`)

The FastAPI application provides:
- **REST Endpoints**: Room creation and management
- **WebSocket Endpoint**: `/ws/{room_id}` for signaling
- **CORS Middleware**: Enables cross-origin requests for frontend
- **Error Handling**: HTTP exceptions and WebSocket disconnection handling

**WebSocket Flow:**
1. Client connects to `/ws/{room_id}`
2. Server accepts connection and assigns `user_id`
3. Server sends `connected` message
4. Server notifies other participants about new user
5. Clients exchange signaling messages (SDP, ICE candidates)
6. On disconnect, server notifies other participants

## Error Handling

The backend handles various error scenarios:

1. **Room Not Found**: Returns 404 when accessing non-existent rooms
2. **WebSocket Disconnection**: Automatically cleans up connections and notifies other users
3. **Invalid Messages**: Returns error messages for malformed signaling data
4. **Connection Errors**: Gracefully handles connection failures

## Next Steps

Once the backend is tested and working:

1. **Frontend Integration**: Connect a React frontend to these endpoints
2. **STUN/TURN Servers**: Configure STUN/TURN servers for NAT traversal
3. **Authentication**: Add user authentication and authorization
4. **Database**: Replace in-memory storage with a database (PostgreSQL, MongoDB)
5. **Scalability**: Consider Redis for distributed WebSocket management
6. **Media Server**: Optionally add a media server (Kurento, Janus) for SFU/MCU

## Troubleshooting

### Port Already in Use
If port 8000 is busy, change it in `main.py`:
```python
uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
```

### CORS Issues
If you encounter CORS errors, ensure the frontend URL is added to `allow_origins` in `main.py`.

### WebSocket Connection Fails
- Verify the room exists (use `/rooms/{room_id}` endpoint)
- Check that the server is running
- Ensure the WebSocket URL format is correct: `ws://localhost:8000/ws/{room_id}`

## License

MIT


