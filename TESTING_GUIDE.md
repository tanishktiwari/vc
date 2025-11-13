# Testing Guide for Database Connection

## 1. Test Locally First

### Step 1: Set up local environment variable

Create a `.env` file in the root directory (if you don't have one):

```env
DATABASE_URL=postgresql://postgres:yrGjdFRaNNLUvzLwCxrTivOFGBpKKWoJ@ballast.proxy.rlwy.net:22903/railway
```

### Step 2: Test database connection

Run the backend locally:
```bash
python main.py
```

You should see:
```
✅ Database connected - Using PostgreSQL
```

If you see an error, check:
- The DATABASE_URL is correct
- Railway database is accessible from your network
- Your firewall allows the connection

### Step 3: Test API endpoints

Open a new terminal and test the endpoints:

**1. Create a room:**
```bash
curl -X POST http://localhost:8000/create-room
```

Expected response:
```json
{
  "room_id": "some-uuid",
  "join_link": "/room/some-uuid",
  "message": "Room some-uuid created successfully"
}
```

**2. List rooms:**
```bash
curl http://localhost:8000/rooms
```

Expected response:
```json
[
  {
    "room_id": "some-uuid",
    "participant_count": 0,
    "created_at": "2025-11-13T..."
  }
]
```

**3. Get room info:**
```bash
curl http://localhost:8000/rooms/{room_id}
```

Replace `{room_id}` with the actual room ID from step 1.

## 2. Test on Vercel (After Deployment)

### Step 1: Check deployment logs

1. Go to your Vercel project dashboard
2. Click on the latest deployment
3. Check the "Function Logs" or "Build Logs"

Look for:
```
✅ Database connected - Using PostgreSQL
```

If you see:
```
⚠️  Database connection failed: ...
```

Then the DATABASE_URL environment variable might not be set correctly.

### Step 2: Test API endpoints

**1. Create a room:**
```bash
curl -X POST https://vc-bice.vercel.app/create-room
```

**2. List rooms:**
```bash
curl https://vc-bice.vercel.app/rooms
```

**3. Test participant count:**

Open your frontend and:
1. Create a room
2. Join the room (this should add a participant)
3. Check the `/rooms` endpoint - participant_count should be 1 or more

## 3. Test Participant Count Functionality

### Manual Testing:

1. **Create a room:**
   - Use the frontend or API to create a room
   - Note the `room_id`

2. **Join the room:**
   - Open the room in your browser
   - This should trigger a WebSocket connection
   - The participant should be added to the database

3. **Check participant count:**
   ```bash
   curl https://vc-bice.vercel.app/rooms
   ```
   - The room should show `participant_count: 1` or more

4. **Join with another browser/device:**
   - Open the same room in an incognito window or another device
   - Check the count again - it should increase

5. **Leave the room:**
   - Close the browser tab
   - Wait a few seconds
   - Check the count - it should decrease

### Using the Test Script:

Run the provided test script (see `test_database.py`)

## 4. Check Database Directly (Optional)

If you have access to Railway's database interface or pgAdmin:

```sql
-- Check rooms
SELECT * FROM rooms ORDER BY created_at DESC;

-- Check participants
SELECT * FROM participants WHERE status = 'active';

-- Check participant count per room
SELECT 
    r.room_id,
    r.status as room_status,
    COUNT(p.participant_id) as participant_count
FROM rooms r
LEFT JOIN participants p ON r.room_id = p.room_id AND p.status = 'active'
GROUP BY r.room_id, r.status
ORDER BY r.created_at DESC;
```

## 5. Troubleshooting

### Issue: "Database connection failed"

**Solutions:**
- Verify DATABASE_URL is set in Vercel environment variables
- Check Railway database is running
- Verify the connection string format is correct
- Check Railway allows public connections (if using public network)

### Issue: Participant count stays at 0

**Solutions:**
- Check Vercel function logs for errors when joining rooms
- Verify WebSocket connections are working
- Check if `join_room` is being called successfully
- Look for errors in the logs like "Failed to join room" or "Error joining room"

### Issue: Rooms not showing up

**Solutions:**
- Verify rooms are being created in the database
- Check if rooms have status = 'active'
- Verify the `/rooms` endpoint is filtering correctly

## 6. Quick Test Checklist

- [ ] Backend starts without errors
- [ ] Database connection message appears in logs
- [ ] Can create a room via API
- [ ] Can list rooms via API
- [ ] Can join a room via frontend
- [ ] Participant count increases when joining
- [ ] Participant count decreases when leaving
- [ ] Multiple participants show correct count

