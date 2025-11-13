"""
Simple test script to verify database connection and basic functionality.
Run this after setting up DATABASE_URL environment variable.
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API URL (local or production)
API_URL = os.getenv('API_URL', 'http://localhost:8000')

def test_database_connection():
    """Test if database is connected by checking root endpoint."""
    print("🔍 Testing database connection...")
    try:
        response = requests.get(f"{API_URL}/")
        if response.status_code == 200:
            print("✅ API is responding")
            data = response.json()
            print(f"   API Version: {data.get('version', 'N/A')}")
            return True
        else:
            print(f"❌ API returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error connecting to API: {e}")
        print(f"   Make sure the backend is running at {API_URL}")
        return False

def test_create_room():
    """Test creating a room."""
    print("\n🔍 Testing room creation...")
    try:
        response = requests.post(f"{API_URL}/create-room")
        if response.status_code == 200:
            data = response.json()
            room_id = data.get('room_id')
            print(f"✅ Room created successfully")
            print(f"   Room ID: {room_id}")
            print(f"   Join Link: {data.get('join_link', 'N/A')}")
            return room_id
        else:
            print(f"❌ Failed to create room. Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating room: {e}")
        return None

def test_list_rooms():
    """Test listing all rooms."""
    print("\n🔍 Testing room listing...")
    try:
        response = requests.get(f"{API_URL}/rooms")
        if response.status_code == 200:
            rooms = response.json()
            print(f"✅ Found {len(rooms)} room(s)")
            for room in rooms:
                print(f"   - Room: {room.get('room_id', 'N/A')[:8]}... | Participants: {room.get('participant_count', 0)}")
            return rooms
        else:
            print(f"❌ Failed to list rooms. Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Error listing rooms: {e}")
        return []

def test_get_room_info(room_id):
    """Test getting room information."""
    print(f"\n🔍 Testing room info for {room_id[:8]}...")
    try:
        response = requests.get(f"{API_URL}/rooms/{room_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Room info retrieved")
            print(f"   Room ID: {data.get('room_id', 'N/A')}")
            print(f"   Participant Count: {data.get('participant_count', 0)}")
            print(f"   Status: {data.get('status', 'N/A')}")
            print(f"   Exists: {data.get('exists', False)}")
            return True
        else:
            print(f"❌ Failed to get room info. Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting room info: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("DATABASE CONNECTION TEST")
    print("=" * 60)
    print(f"API URL: {API_URL}\n")
    
    # Test 1: Database connection
    if not test_database_connection():
        print("\n❌ Database connection test failed. Please check your setup.")
        return
    
    # Test 2: Create room
    room_id = test_create_room()
    if not room_id:
        print("\n❌ Room creation test failed.")
        return
    
    # Test 3: List rooms
    rooms = test_list_rooms()
    
    # Test 4: Get room info
    test_get_room_info(room_id)
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("✅ Basic API tests completed")
    print("\n📝 Next steps:")
    print("   1. Open the frontend and join a room")
    print("   2. Check participant count increases")
    print("   3. Join with another browser/device")
    print("   4. Verify participant count updates correctly")
    print("\n💡 To test on Vercel, set API_URL=https://vc-bice.vercel.app")

if __name__ == "__main__":
    main()

