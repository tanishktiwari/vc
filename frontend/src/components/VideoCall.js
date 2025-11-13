import React, { useEffect, useRef, useState } from 'react';
import EmojiPicker from './EmojiPicker';
import FloatingEmoji from './FloatingEmoji';
import { getColorFromName, getInitials } from '../utils/avatarUtils';

/**
 * Main VideoCall component that handles WebRTC and WebSocket signaling
 * Manages peer connections, media streams, and signaling messages
 */
function VideoCall({ roomId, username, onLeave }) {
  // State management
  const [localStream, setLocalStream] = useState(null);
  const [remoteStreams, setRemoteStreams] = useState(new Map()); // Map<user_id, MediaStream>
  const [remoteMuteStatus, setRemoteMuteStatus] = useState(new Map()); // Map<user_id, boolean> - Track remote mute status
  const [remoteUsernames, setRemoteUsernames] = useState(new Map()); // Map<user_id, username> - Track remote usernames
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOff, setIsVideoOff] = useState(false);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [participants, setParticipants] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [floatingEmojis, setFloatingEmojis] = useState([]);
  const [showScreenShareWarning, setShowScreenShareWarning] = useState(false);

  // Refs for DOM elements and connections
  const localVideoRef = useRef(null);
  const wsRef = useRef(null);
  const peersRef = useRef(new Map()); // Map<user_id, RTCPeerConnection>
  const localStreamRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  // STUN servers for NAT traversal (you can add TURN servers for production)
  const iceServers = {
    iceServers: [
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' },
    ],
  };

  /**
   * Initialize local media stream (camera and microphone)
   */
  const initializeLocalStream = async () => {
    try {
      console.log('Requesting media access...');
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true,
      });
      
      console.log('Media access granted');
      localStreamRef.current = stream;
      setLocalStream(stream);
      
      // Attach stream to local video element
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }
      
      // Set loading to false once media is ready
      // WebSocket can connect in background
      console.log('Media ready - setting loading to false');
      setIsLoading(false);
    } catch (error) {
      console.error('Error accessing media devices:', error);
      setError(`Could not access camera/microphone: ${error.message}`);
      setIsLoading(false);
      // Don't block the UI, allow user to continue without media
      // Still try to connect WebSocket even if media fails
    }
  };

  /**
   * Create a new RTCPeerConnection for a remote peer
   */
  const createPeerConnection = (userId) => {
    const peerConnection = new RTCPeerConnection(iceServers);

    // Add local stream tracks to peer connection
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach((track) => {
        peerConnection.addTrack(track, localStreamRef.current);
      });
    }

    // Handle remote stream
    peerConnection.ontrack = (event) => {
      console.log('Received remote track from:', userId, event.streams);
      const [remoteStream] = event.streams;
      if (remoteStream) {
        setRemoteStreams((prev) => {
          const newMap = new Map(prev);
          newMap.set(userId, remoteStream);
          console.log('Remote streams updated, total:', newMap.size);
          return newMap;
        });
      }
    };

    // Handle ICE candidates
    peerConnection.onicecandidate = (event) => {
      if (event.candidate) {
        sendSignalingMessage({
          type: 'ice-candidate',
          room_id: roomId,
          data: {
            candidate: event.candidate.candidate,
            sdpMLineIndex: event.candidate.sdpMLineIndex,
            sdpMid: event.candidate.sdpMid,
          },
        });
      }
    };

    // Handle connection state changes
    peerConnection.onconnectionstatechange = () => {
      console.log(`Connection state with ${userId}:`, peerConnection.connectionState);
      if (peerConnection.connectionState === 'failed') {
        // Try to reconnect
        peerConnection.restartIce();
      }
    };

    peersRef.current.set(userId, peerConnection);
    return peerConnection;
  };

  /**
   * Send signaling message via WebSocket
   */
  const sendSignalingMessage = (message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, message not sent:', message);
    }
  };

  /**
   * Handle incoming signaling messages
   */
  const handleSignalingMessage = async (message) => {
    const { type, sender_id, user_id, data } = message;
    
    // For user-joined messages, use user_id instead of sender_id
    const actualSenderId = sender_id || user_id;
    
    console.log('Handling signaling message:', type, 'sender_id:', sender_id, 'user_id:', user_id, 'actualSenderId:', actualSenderId, 'my userId:', wsRef.current?.userId);

    // Ignore messages from self (but allow user-joined and existing-participants to process)
    if (actualSenderId && actualSenderId === wsRef.current?.userId && type !== 'user-joined' && type !== 'existing-participants' && type !== 'connected') {
      console.log('Ignoring message from self:', type);
      return;
    }

    switch (type) {
      case 'user-joined':
        // Use user_id from message (backend sends user_id, not sender_id for user-joined)
        const joinedUserId = user_id || sender_id || message.user_id;
        console.log('User joined event received:', {
          joinedUserId,
          sender_id,
          user_id,
          message_user_id: message.user_id,
          myUserId: wsRef.current?.userId
        });
        
        if (!joinedUserId) {
          console.error('No user ID in user-joined message');
          break;
        }
        
        // Don't create connection for self
        if (joinedUserId === wsRef.current?.userId) {
          console.log('Ignoring user-joined for self');
          break;
        }
        
        // Check if peer connection already exists
        if (peersRef.current.has(joinedUserId)) {
          console.log('Peer connection already exists for:', joinedUserId);
          break;
        }
        
        // Create offer for new user
        console.log('Creating peer connection and offer for:', joinedUserId);
        const peerConnection = createPeerConnection(joinedUserId);
        try {
          const offer = await peerConnection.createOffer();
          await peerConnection.setLocalDescription(offer);
          console.log('Sending offer to:', joinedUserId, 'offer type:', offer.type);
          sendSignalingMessage({
            type: 'offer',
            room_id: roomId,
            data: {
              sdp: offer.sdp,
              type: offer.type,
            },
          });
        } catch (error) {
          console.error('Error creating offer for user-joined:', error);
        }
        break;

      case 'offer':
        console.log('Received offer from:', sender_id);
        let answerPeerConnection = peersRef.current.get(sender_id);
        if (!answerPeerConnection) {
          answerPeerConnection = createPeerConnection(sender_id);
        }
        try {
          await answerPeerConnection.setRemoteDescription(
            new RTCSessionDescription(data)
          );
          const answer = await answerPeerConnection.createAnswer();
          await answerPeerConnection.setLocalDescription(answer);
          sendSignalingMessage({
            type: 'answer',
            room_id: roomId,
            data: {
              sdp: answer.sdp,
              type: answer.type,
            },
          });
        } catch (error) {
          console.error('Error handling offer:', error);
        }
        break;

      case 'answer':
        console.log('Received answer from:', sender_id);
        const offerPeerConnection = peersRef.current.get(sender_id);
        if (offerPeerConnection) {
          try {
            await offerPeerConnection.setRemoteDescription(
              new RTCSessionDescription(data)
            );
          } catch (error) {
            console.error('Error handling answer:', error);
          }
        }
        break;

      case 'ice-candidate':
        console.log('Received ICE candidate from:', sender_id);
        const icePeerConnection = peersRef.current.get(sender_id);
        if (icePeerConnection) {
          try {
            await icePeerConnection.addIceCandidate(
              new RTCIceCandidate({
                candidate: data.candidate,
                sdpMLineIndex: data.sdpMLineIndex,
                sdpMid: data.sdpMid,
              })
            );
          } catch (error) {
            console.error('Error adding ICE candidate:', error);
          }
        }
        break;

      case 'user-left':
        console.log('User left:', sender_id);
        // Close peer connection and remove remote stream
        const leavingPeer = peersRef.current.get(sender_id);
        if (leavingPeer) {
          leavingPeer.close();
          peersRef.current.delete(sender_id);
        }
        setRemoteStreams((prev) => {
          const newMap = new Map(prev);
          newMap.delete(sender_id);
          return newMap;
        });
        // Remove mute status for leaving user
        setRemoteMuteStatus((prev) => {
          const newMap = new Map(prev);
          newMap.delete(sender_id);
          return newMap;
        });
        // Remove username for leaving user
        setRemoteUsernames((prev) => {
          const newMap = new Map(prev);
          newMap.delete(sender_id);
          return newMap;
        });
        break;

      case 'connected':
        console.log('Connected to room, user ID:', data?.user_id || data);
        if (wsRef.current) {
          wsRef.current.userId = data?.user_id || data;
        }
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
        // Make sure loading is false when connected message is received
        console.log('Setting loading to false - received connected message');
        setIsLoading(false);
        break;

      case 'existing-participants':
        // Create peer connections for all existing participants
        console.log('Existing participants in room:', data?.participants);
        if (data?.participants && Array.isArray(data.participants)) {
          // Use Promise.all to handle async operations properly
          Promise.all(
            data.participants.map(async (existingUserId) => {
              if (existingUserId !== wsRef.current?.userId) {
                // Check if peer connection already exists
                if (peersRef.current.has(existingUserId)) {
                  console.log('Peer connection already exists for existing participant:', existingUserId);
                  return;
                }
                console.log('Creating peer connection for existing participant:', existingUserId);
                const peerConnection = createPeerConnection(existingUserId);
                try {
                  const offer = await peerConnection.createOffer();
                  await peerConnection.setLocalDescription(offer);
                  console.log('Sending offer to existing participant:', existingUserId);
                  sendSignalingMessage({
                    type: 'offer',
                    room_id: roomId,
                    data: {
                      sdp: offer.sdp,
                      type: offer.type,
                    },
                  });
                } catch (error) {
                  console.error('Error creating offer for existing participant:', error);
                }
              }
            })
          );
        }
        // Note: Usernames for existing participants will be received via 'join' messages
        break;

      case 'join':
        // Store username from join message
        console.log('Join message received from:', sender_id, 'username:', user_id);
        if (sender_id && user_id && sender_id !== wsRef.current?.userId) {
          // user_id in join message is actually the username
          setRemoteUsernames((prev) => {
            const newMap = new Map(prev);
            newMap.set(sender_id, user_id);
            return newMap;
          });
        }
        break;

      case 'emoji':
        // Handle emoji from other participants
        console.log('Received emoji from:', sender_id, data?.emoji);
        if (data?.emoji) {
          const id = Date.now() + Math.random();
          const newEmoji = { id, emoji: data.emoji };
          setFloatingEmojis((prev) => [...prev, newEmoji]);
          
          // Remove emoji after animation completes
          setTimeout(() => {
            setFloatingEmojis((prev) => prev.filter((e) => e.id !== id));
          }, 3000);
        }
        break;

      case 'mute-status':
        // Update remote participant mute status
        console.log('Received mute status from:', sender_id, 'muted:', data?.muted);
        if (sender_id && sender_id !== wsRef.current?.userId) {
          setRemoteMuteStatus((prev) => {
            const newMap = new Map(prev);
            newMap.set(sender_id, data?.muted || false);
            return newMap;
          });
        }
        break;

      case 'error':
        console.error('Signaling error:', data?.message || data);
        break;

      default:
        console.warn('Unknown message type:', type, message);
    }
  };

  /**
   * Connect to WebSocket signaling server
   */
  const connectWebSocket = () => {
    // Close existing connection if any
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('Closing existing WebSocket connection');
      wsRef.current.close();
      wsRef.current = null;
    }
    
    // Use current roomId from props (not closure)
    const currentRoomId = roomId;
    if (!currentRoomId) {
      console.error('Cannot connect: roomId is empty');
      setError('Room ID is missing');
      return;
    }
    
    const wsUrl = `ws://localhost:8000/ws/${currentRoomId}`;
    console.log('Connecting to WebSocket:', wsUrl, 'for room:', currentRoomId);
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      reconnectAttemptsRef.current = 0;
      
      // Send join message
      ws.send(
        JSON.stringify({
          type: 'join',
          room_id: currentRoomId,
          user_id: username,
        })
      );
      
      // Set loading to false once WebSocket is connected and media is ready
      // Use a small delay to ensure state updates properly
      setTimeout(() => {
        if (localStreamRef.current || isConnected) {
          console.log('Setting loading to false - WebSocket connected');
          setIsLoading(false);
        }
      }, 500);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log('Received WebSocket message:', message.type, message);
        handleSignalingMessage(message);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error, event.data);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };

    ws.onclose = (event) => {
      console.log('WebSocket closed', event.code, event.reason);
      setIsConnected(false);
      
      // Check if room doesn't exist (code 1008)
      if (event.code === 1008) {
        setError(`Room "${roomId}" does not exist. Please create a new room or check the room ID.`);
        // Don't try to reconnect if room doesn't exist
        return;
      }
      
      // Check if it's a normal closure (not an error)
      if (event.code === 1000) {
        console.log('WebSocket closed normally');
        return;
      }
      
      // Attempt to reconnect only if it's a connection error
      if (reconnectAttemptsRef.current < maxReconnectAttempts) {
        reconnectAttemptsRef.current += 1;
        const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
        console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current})...`);
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket();
        }, delay);
      } else {
        console.error('Max reconnection attempts reached');
        setError('Failed to connect to server. Make sure the backend is running on port 8000 and the room exists.');
      }
    };

    wsRef.current = ws;
  };

  /**
   * Toggle microphone mute/unmute
   */
  const toggleMic = () => {
    if (localStreamRef.current) {
      localStreamRef.current.getAudioTracks().forEach((track) => {
        track.enabled = isMuted;
      });
      const newMutedState = !isMuted;
      setIsMuted(newMutedState);
      
      // Broadcast mute status to other participants
      sendSignalingMessage({
        type: 'mute-status',
        room_id: roomId,
        data: { muted: newMutedState },
      });
    }
  };

  /**
   * Toggle camera on/off
   */
  const toggleVideo = () => {
    if (localStreamRef.current) {
      localStreamRef.current.getVideoTracks().forEach((track) => {
        track.enabled = isVideoOff;
      });
      setIsVideoOff(!isVideoOff);
    }
  };

  /**
   * Handle emoji selection - create floating emoji animation
   */
  const handleEmojiSelect = (emoji) => {
    const id = Date.now() + Math.random();
    const newEmoji = { id, emoji };
    
    setFloatingEmojis((prev) => [...prev, newEmoji]);
    
    // Remove emoji after animation completes
    setTimeout(() => {
      setFloatingEmojis((prev) => prev.filter((e) => e.id !== id));
    }, 3000);
    
    // Broadcast emoji to other participants via WebSocket
    sendSignalingMessage({
      type: 'emoji',
      room_id: roomId,
      data: { emoji },
    });
  };

  /**
   * Toggle screen sharing
   */
  const toggleScreenShare = async () => {
    try {
      if (!isScreenSharing) {
        // Start screen sharing
        const screenStream = await navigator.mediaDevices.getDisplayMedia({
          video: true,
          audio: true,
        });

        // Check if user is sharing the current tab/window (infinity mirror detection)
        const videoTrack = screenStream.getVideoTracks()[0];
        // Note: Can use videoTrack.getSettings() for detection if needed
        
        // Show warning overlay when screen sharing starts
        setShowScreenShareWarning(true);

        // Replace video track in all peer connections
        peersRef.current.forEach((peerConnection) => {
          const sender = peerConnection
            .getSenders()
            .find((s) => s.track && s.track.kind === 'video');
          if (sender) {
            sender.replaceTrack(videoTrack);
          }
        });

        // Update local stream
        if (localStreamRef.current) {
          const audioTrack = localStreamRef.current.getAudioTracks()[0];
          screenStream.addTrack(audioTrack);
          localStreamRef.current.getVideoTracks()[0].stop();
        }

        localStreamRef.current = screenStream;
        setLocalStream(screenStream);
        if (localVideoRef.current) {
          localVideoRef.current.srcObject = screenStream;
        }

        // Handle screen share ending
        videoTrack.onended = () => {
          setShowScreenShareWarning(false);
          toggleScreenShare(); // This will revert to camera
        };

        setIsScreenSharing(true);
      } else {
        // Stop screen sharing and revert to camera
        const cameraStream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: true,
        });

        // Replace video track in all peer connections
        const videoTrack = cameraStream.getVideoTracks()[0];
        peersRef.current.forEach((peerConnection) => {
          const sender = peerConnection
            .getSenders()
            .find((s) => s.track && s.track.kind === 'video');
          if (sender) {
            sender.replaceTrack(videoTrack);
          }
        });

        // Stop screen share tracks
        if (localStreamRef.current) {
          localStreamRef.current.getTracks().forEach((track) => {
            if (track.kind === 'video') {
              track.stop();
            }
          });
        }

        localStreamRef.current = cameraStream;
        setLocalStream(cameraStream);
        if (localVideoRef.current) {
          localVideoRef.current.srcObject = cameraStream;
        }

        setIsScreenSharing(false);
        setShowScreenShareWarning(false);
      }
    } catch (error) {
      console.error('Error toggling screen share:', error);
      setShowScreenShareWarning(false);
      if (error.name !== 'NotAllowedError') {
        alert('Could not share screen. Please try again.');
      }
    }
  };

  /**
   * Leave the call and cleanup
   */
  const handleLeave = () => {
    console.log('handleLeave called');
    
    // Close all peer connections
    peersRef.current.forEach((peer) => {
      peer.close();
    });
    peersRef.current.clear();

    // Stop local stream
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach((track) => {
        track.stop();
      });
    }

    // Send leave message if WebSocket is connected
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify({
          type: 'leave',
          room_id: roomId,
        }));
      } catch (e) {
        console.warn('Could not send leave message:', e);
      }
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // Clear reconnection timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    // Call parent's onLeave callback
    onLeave();
  };

  /**
   * Initialize on component mount
   */
  useEffect(() => {
    console.log('VideoCall component mounted, initializing...', 'roomId:', roomId);
    
    // Prevent double initialization in StrictMode
    let isMounted = true;
    let initialized = false;
    
    // Initialize local stream and connect to WebSocket
    const init = async () => {
      if (initialized) {
        console.log('Already initialized, skipping...');
        return;
      }
      initialized = true;
      
      try {
        await initializeLocalStream();
        if (isMounted && roomId) {
          console.log('Media initialized, connecting WebSocket for room:', roomId);
          connectWebSocket();
        } else if (!roomId) {
          console.error('Cannot initialize: roomId is missing');
          setError('Room ID is missing');
          setIsLoading(false);
        }
      } catch (err) {
        console.error('Initialization error:', err);
        if (isMounted) {
          setError(`Initialization failed: ${err.message}`);
          setIsLoading(false);
        }
        initialized = false;
      }
    };

    // Small delay to prevent double initialization in StrictMode
    const timeoutId = setTimeout(() => {
      init();
    }, 100);

    // Cleanup on unmount
    return () => {
      clearTimeout(timeoutId);
      console.log('VideoCall component unmounting, cleaning up...');
      isMounted = false;
      initialized = false;
      
      // Clean up WebSocket connection
      if (wsRef.current) {
        console.log('Closing WebSocket connection...');
        try {
          if (wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.close();
          }
        } catch (e) {
          console.warn('Error closing WebSocket:', e);
        }
        wsRef.current = null;
      }
      
      // Clean up peer connections
      // Capture ref value to satisfy React hooks exhaustive-deps rule
      // eslint-disable-next-line react-hooks/exhaustive-deps
      const currentPeers = peersRef.current;
      if (currentPeers) {
        currentPeers.forEach((peer) => {
          try {
            peer.close();
          } catch (e) {
            console.warn('Error closing peer connection:', e);
          }
        });
        currentPeers.clear();
      }
      
      // Stop local stream tracks
      if (localStreamRef.current) {
        localStreamRef.current.getTracks().forEach((track) => {
          track.stop();
        });
      }
      
      // Clear reconnection timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [roomId]); // Add roomId as dependency

  /**
   * Update participants list when remote streams change
   */
  useEffect(() => {
    const participantIds = Array.from(remoteStreams.keys());
    console.log('Participants updated:', participantIds, 'Total remote streams:', remoteStreams.size);
    setParticipants(participantIds);
  }, [remoteStreams]);

  /**
   * Calculate grid layout for video elements
   * Optimized for 2-8 participants like Google Meet
   */
  const getGridCols = () => {
    const total = participants.length + 1; // +1 for local video
    if (total === 1) return 'grid-cols-1';
    if (total === 2) return 'grid-cols-2';
    if (total <= 4) return 'grid-cols-2';
    if (total <= 6) return 'grid-cols-3';
    if (total <= 9) return 'grid-cols-3';
    return 'grid-cols-4';
  };

  /**
   * Get all participants to display (including local user)
   */
  const getAllParticipants = () => {
    const all = [];
    
    // Add local user first
    all.push({
      userId: 'local',
      name: username,
      stream: localStream,
      isLocal: true,
      isMuted: isMuted,
      isVideoOff: isVideoOff,
    });
    
    // Add remote participants
    participants.forEach((userId) => {
      const remoteStream = remoteStreams.get(userId);
      // Use stored username, or fallback to user ID
      const remoteUsername = remoteUsernames.get(userId) || `User ${userId.substring(0, 8)}`;
      all.push({
        userId: userId,
        name: remoteUsername,
        stream: remoteStream,
        isLocal: false,
        isMuted: remoteMuteStatus.get(userId) || false,
        isVideoOff: false,
      });
    });
    
    return all;
  };

  // Auto-hide loading after timeout to prevent getting stuck
  useEffect(() => {
    if (isLoading && !localStream && !isConnected) {
      const timeout = setTimeout(() => {
        console.warn('Loading timeout - showing UI anyway');
        setIsLoading(false);
      }, 10000);
      return () => clearTimeout(timeout);
    }
  }, [isLoading, localStream, isConnected]);

  // Show loading state - but also show UI if media is ready even if WebSocket isn't connected yet
  if (isLoading && !localStream) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-white mx-auto mb-4"></div>
          <p className="text-xl">Loading video call...</p>
          <p className="text-sm text-gray-400 mt-2">Requesting camera and microphone access</p>
          <p className="text-xs text-gray-500 mt-4">If this takes too long, check browser permissions</p>
        </div>
      </div>
    );
  }
  
  // If media is ready but still loading WebSocket, show UI anyway
  if (isLoading && localStream) {
    console.log('Media ready but WebSocket not connected yet - showing UI');
    // Don't block UI if media is ready
  }

  // Show error state (if critical error before connection)
  if (error && !localStream && !isConnected) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center p-4">
        <div className="bg-red-900 border border-red-700 rounded-lg p-6 max-w-md">
          <h2 className="text-xl font-bold mb-4">Connection Error</h2>
          <p className="mb-4">{error}</p>
          <div className="space-y-2">
            <button
              onClick={onLeave}
              className="w-full bg-red-600 hover:bg-red-700 px-4 py-2 rounded"
            >
              Go Back
            </button>
            <button
              onClick={() => {
                setError(null);
                reconnectAttemptsRef.current = 0;
                connectWebSocket();
              }}
              className="w-full bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded"
            >
              Retry Connection
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Helper component for video/avatar display
  const VideoDisplay = ({ stream, name, userId, isLocal = false, isVideoOff: videoOff, videoRef: externalRef }) => {
    const internalVideoRef = useRef(null);
    const videoRef = externalRef || internalVideoRef;
    const hasVideo = stream && stream.getVideoTracks().some(track => track.enabled && !videoOff);
    
    useEffect(() => {
      if (videoRef.current && stream && hasVideo) {
        videoRef.current.srcObject = stream;
      }
    }, [stream, hasVideo, videoRef]);

    if (hasVideo && stream) {
      return (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted={isLocal}
          className="w-full h-full object-cover"
        />
      );
    }

    // Show avatar when video is off - circular avatar like Google Meet
    const initials = getInitials(name || userId);
    const bgColor = getColorFromName(name || userId);
    
    return (
      <div 
        className="w-full h-full flex items-center justify-center"
        style={{ backgroundColor: bgColor }}
      >
        <div 
          className="rounded-full w-32 h-32 flex items-center justify-center"
          style={{ backgroundColor: bgColor }}
        >
          <div className="text-white text-5xl font-semibold">
            {initials}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="h-screen bg-gray-900 text-white flex flex-col overflow-hidden relative">
      {/* Error Banner */}
      {error && (
        <div className="bg-red-900 border-b border-red-700 p-2 text-center text-sm flex-shrink-0 z-50">
          {error}
        </div>
      )}

      {/* Screen Share Warning Overlay */}
      {showScreenShareWarning && isScreenSharing && (
        <div className="absolute inset-0 bg-black bg-opacity-90 z-40 flex items-center justify-center">
          <div className="bg-gray-800 rounded-lg p-8 max-w-2xl mx-4 border border-gray-700">
            <h2 className="text-2xl font-bold mb-4 text-center">You are presenting</h2>
            <p className="text-gray-300 text-center mb-6">
              To avoid an infinity mirror, don't share your entire screen or browser window. 
              Share just a tab or a different window instead.
            </p>
            <div className="flex gap-4 justify-center">
              <button
                onClick={() => setShowScreenShareWarning(false)}
                className="px-6 py-3 border border-gray-600 rounded-lg hover:bg-gray-700 transition-colors"
              >
                Show my screen anyway
              </button>
              <button
                onClick={toggleScreenShare}
                className="px-6 py-3 bg-white text-gray-900 rounded-lg hover:bg-gray-200 transition-colors font-semibold"
              >
                Stop presenting
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Floating Emojis Container */}
      <div className="absolute inset-0 pointer-events-none z-10">
        {floatingEmojis.map((item) => (
          <FloatingEmoji
            key={item.id}
            emoji={item.emoji}
            onComplete={() => {
              setFloatingEmojis((prev) => prev.filter((e) => e.id !== item.id));
            }}
          />
        ))}
      </div>

      {/* Video Grid - Takes remaining space, no scrolling */}
      <div className={`flex-1 p-4 grid ${getGridCols()} gap-4 overflow-hidden relative`}>
        {getAllParticipants().map((participant) => {
          const { userId, name, stream, isLocal, isMuted: muted, isVideoOff: videoOff } = participant;
          
          return (
            <div
              key={userId}
              className="relative bg-gray-800 rounded-lg overflow-hidden shadow-lg flex flex-col"
            >
              {/* Video/Avatar Display */}
              <div className="flex-1 relative">
                {isLocal ? (
                  <VideoDisplay 
                    stream={stream} 
                    name={name} 
                    userId={userId}
                    isLocal={true}
                    isVideoOff={videoOff}
                    videoRef={localVideoRef}
                  />
                ) : (
                  <VideoDisplay 
                    stream={stream} 
                    name={name}
                    userId={userId}
                    isVideoOff={false}
                  />
                )}
                
                {/* Mute Indicator - Top Right */}
                {muted && (
                  <div className="absolute top-2 right-2 bg-gray-900 bg-opacity-80 rounded-full p-1.5">
                    <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M13.477 14.89A6 6 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" clipRule="evenodd" />
                      <path d="M5 5l10 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                    </svg>
                  </div>
                )}
                
                {/* Video Off Indicator - Top Right (if muted is not shown) */}
                {!muted && videoOff && isLocal && (
                  <div className="absolute top-2 right-2 bg-gray-900 bg-opacity-80 rounded-full p-1.5">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M1 1l22 22" />
                    </svg>
                  </div>
                )}
              </div>
              
              {/* Name Label - Bottom */}
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black via-black/80 to-transparent px-3 py-2 flex items-center justify-between">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <span className="text-white text-sm font-medium truncate">
                    {isLocal ? 'You' : name}
                  </span>
                </div>
                {/* Three dots menu (optional) */}
                <button className="text-white hover:bg-white/20 rounded p-1 ml-2">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                  </svg>
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Controls - Fixed at bottom */}
      <div className="bg-gray-800 p-4 flex-shrink-0 relative">
        <div className="flex items-center justify-center gap-4">
          {/* Toggle Microphone Button */}
          <button
            onClick={toggleMic}
            className={`p-4 rounded-full transition-all duration-200 transform hover:scale-110 ${
              isMuted
                ? 'bg-red-600 hover:bg-red-700'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
            title={isMuted ? 'Unmute' : 'Mute'}
            aria-label={isMuted ? 'Unmute microphone' : 'Mute microphone'}
          >
            <svg
              className="w-6 h-6 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              {isMuted ? (
                <>
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 5l14 14"
                  />
                </>
              ) : (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                />
              )}
            </svg>
          </button>

          {/* Toggle Camera Button */}
          <button
            onClick={toggleVideo}
            className={`p-4 rounded-full transition-all duration-200 transform hover:scale-110 ${
              isVideoOff
                ? 'bg-red-600 hover:bg-red-700'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
            title={isVideoOff ? 'Turn on camera' : 'Turn off camera'}
            aria-label={isVideoOff ? 'Turn on camera' : 'Turn off camera'}
          >
            <svg
              className="w-6 h-6 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              {isVideoOff ? (
                <>
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M1 1l22 22"
                  />
                </>
              ) : (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                />
              )}
            </svg>
          </button>

          {/* Toggle Screen Share Button */}
          <button
            onClick={toggleScreenShare}
            className={`p-4 rounded-full transition-all duration-200 transform hover:scale-110 ${
              isScreenSharing
                ? 'bg-blue-600 hover:bg-blue-700'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
            title={isScreenSharing ? 'Stop sharing' : 'Share screen'}
            aria-label={isScreenSharing ? 'Stop screen sharing' : 'Start screen sharing'}
          >
            <svg
              className="w-6 h-6 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
          </button>

          {/* Emoji Picker - Just before Leave button */}
          <EmojiPicker onEmojiSelect={handleEmojiSelect} />

          {/* Leave Call Button */}
          <button
            onClick={handleLeave}
            className="p-4 rounded-full bg-red-600 hover:bg-red-700 transition-all duration-200 transform hover:scale-110"
            title="Leave call"
            aria-label="Leave the video call"
          >
            <svg
              className="w-6 h-6 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M16 8l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2M5 3a2 2 0 00-2 2v1c0 8.284 6.716 15 15 15h1a2 2 0 002-2v-3.28a1 1 0 00-.684-.948l-4.493-1.498a1 1 0 00-1.21.502l-1.13 2.257a11.042 11.042 0 01-5.516-5.517l2.257-1.128a1 1 0 00.502-1.21L9.228 3.683A1 1 0 008.279 3H5z"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

export default VideoCall;

