# How to View Database Data via API

Your backend has several endpoints to view database data. Here are all the available endpoints:

## 📋 Available Endpoints

### 1. **View All Rooms** (Basic)
**Endpoint:** `GET /rooms`

**Description:** Lists all active rooms with participant counts

**Example:**
```bash
curl https://vc-bice.vercel.app/rooms
```

**Response:**
```json
[
  {
    "room_id": "ba97b1f7-de8f-4f84-969d-bf6eeb1fc27a",
    "participant_count": 2,
    "created_at": "2025-11-13T14:03:48.565099"
  }
]
```

---

### 2. **View All Rooms** (Detailed - Admin)
**Endpoint:** `GET /admin/rooms`

**Description:** Lists ALL rooms (active and ended) with detailed information

**Example:**
```bash
curl https://vc-bice.vercel.app/admin/rooms
```

**Response:**
```json
{
  "rooms": [
    {
      "room_id": "ba97b1f7-de8f-4f84-969d-bf6eeb1fc27a",
      "created_at": "2025-11-13T14:03:48.565099",
      "created_by": "user123",
      "status": "active",
      "participant_count": 2
    }
  ],
  "total": 1
}
```

---

### 3. **View Specific Room Details**
**Endpoint:** `GET /admin/rooms/{room_id}`

**Description:** Get detailed information about a specific room including all participants

**Example:**
```bash
curl https://vc-bice.vercel.app/admin/rooms/ba97b1f7-de8f-4f84-969d-bf6eeb1fc27a
```

**Response:**
```json
{
  "room_id": "ba97b1f7-de8f-4f84-969d-bf6eeb1fc27a",
  "created_at": "2025-11-13T14:03:48.565099",
  "created_by": "user123",
  "status": "active",
  "participants": [
    {
      "user_id": "user-uuid-1",
      "username": "John",
      "joined_at": "2025-11-13T14:04:00",
      "left_at": null,
      "status": "active"
    }
  ],
  "participant_count": 1
}
```

---

### 4. **View All Participants**
**Endpoint:** `GET /admin/participants`

**Description:** Lists all participants from all rooms (last 100)

**Example:**
```bash
curl https://vc-bice.vercel.app/admin/participants
```

**Response:**
```json
{
  "participants": [
    {
      "participant_id": "participant-uuid",
      "room_id": "ba97b1f7-de8f-4f84-969d-bf6eeb1fc27a",
      "user_id": "user-uuid",
      "username": "John",
      "joined_at": "2025-11-13T14:04:00",
      "left_at": null,
      "status": "active"
    }
  ],
  "total": 1
}
```

---

### 5. **View Active Sessions**
**Endpoint:** `GET /admin/sessions`

**Description:** Lists all active WebSocket sessions

**Example:**
```bash
curl https://vc-bice.vercel.app/admin/sessions
```

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "session-uuid",
      "room_id": "ba97b1f7-de8f-4f84-969d-bf6eeb1fc27a",
      "user_id": "user-uuid",
      "connected_at": "2025-11-13T14:04:00",
      "disconnected_at": null,
      "status": "connected"
    }
  ],
  "total": 1
}
```

---

### 6. **View Database Statistics**
**Endpoint:** `GET /admin/stats`

**Description:** Get overall database statistics

**Example:**
```bash
curl https://vc-bice.vercel.app/admin/stats
```

**Response:**
```json
{
  "active_rooms": 5,
  "ended_rooms": 10,
  "active_participants": 8,
  "left_participants": 25,
  "active_sessions": 8,
  "total_rooms": 15,
  "total_participants": 33
}
```

---

## 🌐 Using in Browser

You can also open these URLs directly in your browser:

1. **All Rooms (Basic):**
   ```
   https://vc-bice.vercel.app/rooms
   ```

2. **All Rooms (Detailed):**
   ```
   https://vc-bice.vercel.app/admin/rooms
   ```

3. **Statistics:**
   ```
   https://vc-bice.vercel.app/admin/stats
   ```

4. **All Participants:**
   ```
   https://vc-bice.vercel.app/admin/participants
   ```

---

## 🔧 Using with JavaScript/Fetch

```javascript
// View all rooms
fetch('https://vc-bice.vercel.app/admin/rooms')
  .then(res => res.json())
  .then(data => console.log(data));

// View statistics
fetch('https://vc-bice.vercel.app/admin/stats')
  .then(res => res.json())
  .then(data => console.log(data));

// View specific room
const roomId = 'ba97b1f7-de8f-4f84-969d-bf6eeb1fc27a';
fetch(`https://vc-bice.vercel.app/admin/rooms/${roomId}`)
  .then(res => res.json())
  .then(data => console.log(data));
```

---

## 📊 Quick Reference Table

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/rooms` | GET | List active rooms (basic) |
| `/admin/rooms` | GET | List all rooms (detailed) |
| `/admin/rooms/{room_id}` | GET | Get specific room details |
| `/admin/participants` | GET | List all participants |
| `/admin/sessions` | GET | List active sessions |
| `/admin/stats` | GET | Database statistics |

---

## 💡 Tips

1. **For quick overview:** Use `/admin/stats`
2. **For room details:** Use `/admin/rooms/{room_id}`
3. **For participant tracking:** Use `/admin/participants`
4. **For real-time connections:** Use `/admin/sessions`

All admin endpoints require the database to be configured. If you see a 503 error, make sure `DATABASE_URL` is set in Vercel.

