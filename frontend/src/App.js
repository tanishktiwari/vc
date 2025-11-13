import React, { useState } from 'react';
import VideoCall from './components/VideoCall';
import { createRoom, checkRoomExists } from './utils/api';

function App() {
  const [roomId, setRoomId] = useState('');
  const [username, setUsername] = useState('');
  const [joined, setJoined] = useState(false);

  const [isCreatingRoom, setIsCreatingRoom] = useState(false);
  const [isJoining, setIsJoining] = useState(false);
  const [error, setError] = useState('');

  const handleJoin = async (e) => {
    e.preventDefault();
    setError('');
    setIsJoining(true);
    
    try {
      if (!roomId.trim() || !username.trim()) {
        setError('Please enter both room ID and username');
        setIsJoining(false);
        return;
      }

      console.log('Checking if room exists:', roomId.trim());
      
      // Check if room exists
      const roomExists = await checkRoomExists(roomId.trim());
      console.log('Room exists:', roomExists);
      
      if (!roomExists) {
        setError(`Room "${roomId.trim()}" does not exist. Please create a new room or check the room ID.`);
        setIsJoining(false);
        return;
      }

      console.log('Joining room...');
      setError(''); // Clear any previous errors
      setIsJoining(false); // Reset loading state before switching components
      setJoined(true);
    } catch (err) {
      console.error('Error joining room:', err);
      setError(`Failed to join room: ${err.message || 'Unknown error'}`);
      setIsJoining(false);
    }
  };

  const handleCreateRoom = async () => {
    setIsCreatingRoom(true);
    setError('');
    try {
      const room = await createRoom();
      setRoomId(room.room_id);
      setError('');
      alert(`Room created! Room ID: ${room.room_id}\nYou can now join the room.`);
    } catch (err) {
      setError('Failed to create room. Make sure the backend is running.');
      console.error('Error creating room:', err);
    } finally {
      setIsCreatingRoom(false);
    }
  };

  const handleLeave = () => {
    setJoined(false);
    setRoomId('');
    setUsername('');
  };

  if (joined) {
    return (
      <VideoCall 
        roomId={roomId} 
        username={username} 
        onLeave={handleLeave}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-2xl p-8 w-full max-w-md">
        <h1 className="text-3xl font-bold text-center text-gray-800 mb-2">
          Video Conference
        </h1>
        <p className="text-center text-gray-600 mb-8">
          Join a room to start video calling
        </p>
        
        <form onSubmit={handleJoin} className="space-y-6">
          <div>
            <label 
              htmlFor="roomId" 
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Room ID
            </label>
            <input
              id="roomId"
              type="text"
              value={roomId}
              onChange={(e) => setRoomId(e.target.value)}
              placeholder="Enter room ID"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
              required
            />
            <p className="mt-1 text-xs text-gray-500">
              Get a room ID from the backend API
            </p>
          </div>

          <div>
            <label 
              htmlFor="username" 
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your name"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
              required
            />
          </div>

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          <div className="flex gap-2">
            <button
              type="submit"
              disabled={isJoining}
              className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-semibold py-3 px-4 rounded-lg transition duration-200 transform hover:scale-105"
            >
              {isJoining ? 'Joining...' : 'Join Room'}
            </button>
            <button
              type="button"
              onClick={handleCreateRoom}
              disabled={isCreatingRoom}
              className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-semibold py-3 px-4 rounded-lg transition duration-200"
            >
              {isCreatingRoom ? 'Creating...' : 'Create Room'}
            </button>
          </div>
        </form>

        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-gray-700 font-medium mb-2">
            💡 Quick Start:
          </p>
          <ol className="text-xs text-gray-600 space-y-1 list-decimal list-inside">
            <li>Create a room using the backend API</li>
            <li>Copy the room_id from the response</li>
            <li>Enter it above and join!</li>
          </ol>
        </div>
      </div>
    </div>
  );
}

export default App;

