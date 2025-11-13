# Video Conferencing Frontend

React frontend for the video conferencing application with WebRTC and WebSocket signaling.

## Features

- ✅ Join rooms with room ID and username
- ✅ Real-time video/audio streaming using WebRTC
- ✅ Multiple participants support with grid layout
- ✅ Microphone mute/unmute
- ✅ Camera on/off toggle
- ✅ Screen sharing
- ✅ Leave call functionality
- ✅ Automatic WebSocket reconnection
- ✅ Responsive design with Tailwind CSS

## Prerequisites

- Node.js (v14 or higher)
- npm or yarn
- Backend server running on `http://localhost:8000`

## Installation

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

## Running the Application

1. **Make sure the backend server is running:**
   ```bash
   # In the backend directory
   python main.py
   ```

2. **Start the React development server:**
   ```bash
   npm start
   ```

3. **Open your browser:**
   - The app will open at `http://localhost:3000`
   - If it doesn't open automatically, navigate to it manually

## Usage

### Step 1: Create a Room

Use the backend API to create a room:

```bash
curl.exe --location --request POST 'http://localhost:8000/create-room'
```

Copy the `room_id` from the response.

### Step 2: Join the Room

1. Open the app in your browser (`http://localhost:3000`)
2. Enter the room ID you copied
3. Enter your username
4. Click "Join Room"
5. Allow camera/microphone permissions when prompted

### Step 3: Test with Multiple Users

1. Open the app in multiple browser tabs/windows
2. Use the same room ID but different usernames
3. You should see all participants in a grid layout

## Controls

- **🎤 Toggle Mic**: Mute/unmute your microphone
- **📷 Toggle Camera**: Turn camera on/off
- **🖥️ Screen Share**: Share your screen (click again to stop)
- **🚪 Leave Call**: Exit the room and return to join screen

## Project Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── VideoCall.js    # Main WebRTC component
│   │   └── Controls.js     # Control buttons component
│   ├── App.js              # Main app component with join form
│   ├── index.js            # React entry point
│   └── index.css           # Tailwind CSS styles
├── package.json
├── tailwind.config.js
└── postcss.config.js
```

## How It Works

### WebRTC Flow

1. **Local Stream**: User's camera/mic is captured using `getUserMedia()`
2. **WebSocket Connection**: Connects to signaling server at `ws://localhost:8000/ws/{room_id}`
3. **Peer Connection**: Creates RTCPeerConnection for each remote participant
4. **Signaling**: Exchanges SDP offers/answers and ICE candidates via WebSocket
5. **Media Streaming**: Once connection is established, video/audio streams are exchanged

### Signaling Messages

- **Join**: Sent when user joins a room
- **Offer**: SDP offer sent to initiate connection
- **Answer**: SDP answer sent in response to offer
- **ICE Candidate**: Network information for peer connection
- **Leave**: Sent when user leaves the room

## Troubleshooting

### Camera/Microphone Not Working

- Check browser permissions
- Make sure you're using HTTPS or localhost (required for `getUserMedia`)
- Check browser console for errors

### Can't See Other Participants

- Verify both users are in the same room
- Check WebSocket connection status (shown in header)
- Check browser console for WebRTC errors
- Make sure STUN servers are accessible

### Screen Share Not Working

- Some browsers require HTTPS for screen sharing
- Check if browser supports `getDisplayMedia()`
- Make sure you grant screen share permissions

### WebSocket Connection Issues

- Verify backend server is running on port 8000
- Check room ID is correct
- Check browser console for connection errors
- The app will attempt to reconnect automatically (up to 5 times)

## Production Considerations

For production deployment, you should:

1. **Add TURN servers** for better NAT traversal:
   ```javascript
   iceServers: [
     { urls: 'stun:stun.l.google.com:19302' },
     { urls: 'turn:your-turn-server.com:3478', username: 'user', credential: 'pass' }
   ]
   ```

2. **Use HTTPS/WSS** (required for production):
   - Update WebSocket URL to `wss://`
   - Deploy with SSL certificate

3. **Add authentication**:
   - Implement user authentication
   - Secure room access

4. **Error handling**:
   - Add more robust error handling
   - User-friendly error messages

5. **Optimize for mobile**:
   - Test on mobile devices
   - Adjust UI for smaller screens

## Browser Support

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support (may need additional configuration)
- Mobile browsers: ⚠️ Limited support (test thoroughly)

## Development

### Available Scripts

- `npm start`: Start development server
- `npm build`: Build for production
- `npm test`: Run tests

### Environment Variables

You can create a `.env` file to customize:

```
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_API_URL=http://localhost:8000
```

Then update the code to use these variables.

## License

MIT

