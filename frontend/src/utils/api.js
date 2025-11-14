/**
 * API utility functions for backend communication
 */

// Use environment variable for API URL, fallback to localhost for development
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Create a new room
 */
export const createRoom = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/create-room`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error creating room:', error);
    throw error;
  }
};

/**
 * Check if a room exists
 */
export const checkRoomExists = async (roomId) => {
  try {
    console.log(`Checking room: ${API_BASE_URL}/rooms/${roomId}`);
    const response = await fetch(`${API_BASE_URL}/rooms/${roomId}`, {
      method: 'GET',
    });
    
    console.log('Response status:', response.status);
    
    if (response.status === 404) {
      console.log('Room not found (404)');
      return false;
    }
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('HTTP error response:', errorText);
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('Room data:', data);
    return data.exists || false;
  } catch (error) {
    console.error('Error checking room:', error);
    // If it's a network error, throw it so the UI can show a proper error
    // If it's a 404, we already returned false above
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Network error: Could not connect to backend server. Make sure it is running on port 8000.');
    }
    throw error;
  }
};

/**
 * Get room information
 */
export const getRoomInfo = async (roomId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/rooms/${roomId}`, {
      method: 'GET',
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error getting room info:', error);
    throw error;
  }
};

