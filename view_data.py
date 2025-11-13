"""
Simple script to view database data from your Vercel deployment.
Run this to quickly check what's in your database.
"""
import requests
import json
from datetime import datetime

# Change this to your Vercel URL
API_URL = "https://vc-bice.vercel.app"

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def view_statistics():
    """View database statistics."""
    print_section("DATABASE STATISTICS")
    try:
        response = requests.get(f"{API_URL}/admin/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"Active Rooms:        {stats.get('active_rooms', 0)}")
            print(f"Ended Rooms:         {stats.get('ended_rooms', 0)}")
            print(f"Total Rooms:         {stats.get('total_rooms', 0)}")
            print(f"\nActive Participants: {stats.get('active_participants', 0)}")
            print(f"Left Participants:   {stats.get('left_participants', 0)}")
            print(f"Total Participants:  {stats.get('total_participants', 0)}")
            print(f"\nActive Sessions:    {stats.get('active_sessions', 0)}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def view_all_rooms():
    """View all rooms."""
    print_section("ALL ROOMS (DETAILED)")
    try:
        response = requests.get(f"{API_URL}/admin/rooms")
        if response.status_code == 200:
            data = response.json()
            rooms = data.get('rooms', [])
            total = data.get('total', 0)
            
            if not rooms:
                print("No rooms found.")
                return
            
            print(f"Total Rooms: {total}\n")
            for room in rooms:
                print(f"Room ID: {room.get('room_id', 'N/A')}")
                print(f"  Status: {room.get('status', 'N/A')}")
                print(f"  Created: {room.get('created_at', 'N/A')}")
                print(f"  Created By: {room.get('created_by', 'N/A')}")
                print(f"  Participants: {room.get('participant_count', 0)}")
                print()
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def view_active_rooms():
    """View only active rooms."""
    print_section("ACTIVE ROOMS (BASIC)")
    try:
        response = requests.get(f"{API_URL}/rooms")
        if response.status_code == 200:
            rooms = response.json()
            
            if not rooms:
                print("No active rooms found.")
                return
            
            print(f"Total Active Rooms: {len(rooms)}\n")
            for room in rooms:
                print(f"Room: {room.get('room_id', 'N/A')[:8]}...")
                print(f"  Participants: {room.get('participant_count', 0)}")
                print(f"  Created: {room.get('created_at', 'N/A')}")
                print()
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def view_participants():
    """View all participants."""
    print_section("ALL PARTICIPANTS")
    try:
        response = requests.get(f"{API_URL}/admin/participants")
        if response.status_code == 200:
            data = response.json()
            participants = data.get('participants', [])
            total = data.get('total', 0)
            
            if not participants:
                print("No participants found.")
                return
            
            print(f"Total Participants: {total}\n")
            for p in participants:
                print(f"User: {p.get('user_id', 'N/A')[:8]}...")
                print(f"  Room: {p.get('room_id', 'N/A')[:8]}...")
                print(f"  Username: {p.get('username', 'N/A')}")
                print(f"  Status: {p.get('status', 'N/A')}")
                print(f"  Joined: {p.get('joined_at', 'N/A')}")
                if p.get('left_at'):
                    print(f"  Left: {p.get('left_at', 'N/A')}")
                print()
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def view_room_details(room_id):
    """View details of a specific room."""
    print_section(f"ROOM DETAILS: {room_id[:8]}...")
    try:
        response = requests.get(f"{API_URL}/admin/rooms/{room_id}")
        if response.status_code == 200:
            room = response.json()
            print(f"Room ID: {room.get('room_id', 'N/A')}")
            print(f"Status: {room.get('status', 'N/A')}")
            print(f"Created: {room.get('created_at', 'N/A')}")
            print(f"Created By: {room.get('created_by', 'N/A')}")
            print(f"\nParticipants ({room.get('participant_count', 0)}):")
            
            participants = room.get('participants', [])
            if participants:
                for p in participants:
                    print(f"  - User: {p.get('user_id', 'N/A')[:8]}...")
                    print(f"    Username: {p.get('username', 'N/A')}")
                    print(f"    Status: {p.get('status', 'N/A')}")
                    print(f"    Joined: {p.get('joined_at', 'N/A')}")
            else:
                print("  No participants")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Main function to view all data."""
    print("\n" + "=" * 60)
    print("  DATABASE DATA VIEWER")
    print("=" * 60)
    print(f"API URL: {API_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # View statistics first
    view_statistics()
    
    # View active rooms
    view_active_rooms()
    
    # View all rooms (detailed)
    view_all_rooms()
    
    # View participants
    view_participants()
    
    print("\n" + "=" * 60)
    print("  To view a specific room, use:")
    print(f"  python view_data.py --room <room_id>")
    print("=" * 60)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 2 and sys.argv[1] == "--room":
        room_id = sys.argv[2]
        view_room_details(room_id)
    else:
        main()

