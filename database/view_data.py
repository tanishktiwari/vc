"""
Script to view data from PostgreSQL database.
Run this to see all rooms, participants, and sessions.
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'video_conferencing')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

# Create database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def view_rooms(db_session):
    """View all rooms."""
    print("\n" + "="*80)
    print("ROOMS")
    print("="*80)
    
    result = db_session.execute(text("""
        SELECT 
            room_id,
            created_at,
            created_by,
            status,
            (SELECT COUNT(*) FROM participants WHERE room_id = rooms.room_id AND status = 'active') as participant_count
        FROM rooms
        ORDER BY created_at DESC
    """))
    
    rooms = result.fetchall()
    
    if not rooms:
        print("No rooms found.")
        return
    
    print(f"{'Room ID':<40} {'Created At':<20} {'Created By':<15} {'Status':<10} {'Participants':<12}")
    print("-" * 80)
    
    for room in rooms:
        room_id, created_at, created_by, status, count = room
        created_at_str = created_at.strftime('%Y-%m-%d %H:%M:%S') if created_at else 'N/A'
        print(f"{str(room_id):<40} {created_at_str:<20} {created_by or 'N/A':<15} {status:<10} {count:<12}")

def view_participants(db_session):
    """View all participants."""
    print("\n" + "="*80)
    print("PARTICIPANTS")
    print("="*80)
    
    result = db_session.execute(text("""
        SELECT 
            p.participant_id,
            p.room_id,
            p.user_id,
            p.username,
            p.joined_at,
            p.left_at,
            p.status,
            r.created_at as room_created
        FROM participants p
        LEFT JOIN rooms r ON p.room_id = r.room_id
        ORDER BY p.joined_at DESC
        LIMIT 50
    """))
    
    participants = result.fetchall()
    
    if not participants:
        print("No participants found.")
        return
    
    print(f"{'Room ID':<40} {'User ID':<40} {'Username':<20} {'Status':<10} {'Joined At':<20}")
    print("-" * 80)
    
    for p in participants:
        participant_id, room_id, user_id, username, joined_at, left_at, status, room_created = p
        joined_str = joined_at.strftime('%Y-%m-%d %H:%M:%S') if joined_at else 'N/A'
        print(f"{str(room_id):<40} {str(user_id):<40} {username or 'N/A':<20} {status:<10} {joined_str:<20}")

def view_sessions(db_session):
    """View all active sessions."""
    print("\n" + "="*80)
    print("ACTIVE SESSIONS (WebSocket Connections)")
    print("="*80)
    
    result = db_session.execute(text("""
        SELECT 
            s.session_id,
            s.room_id,
            s.user_id,
            s.connected_at,
            s.disconnected_at,
            s.status
        FROM sessions s
        WHERE s.status = 'connected'
        ORDER BY s.connected_at DESC
    """))
    
    sessions = result.fetchall()
    
    if not sessions:
        print("No active sessions found.")
        return
    
    print(f"{'Room ID':<40} {'User ID':<40} {'Connected At':<20} {'Status':<10}")
    print("-" * 80)
    
    for s in sessions:
        session_id, room_id, user_id, connected_at, disconnected_at, status = s
        connected_str = connected_at.strftime('%Y-%m-%d %H:%M:%S') if connected_at else 'N/A'
        print(f"{str(room_id):<40} {str(user_id):<40} {connected_str:<20} {status:<10}")

def view_room_details(db_session, room_id=None):
    """View detailed information about a specific room."""
    if room_id:
        print(f"\n" + "="*80)
        print(f"ROOM DETAILS: {room_id}")
        print("="*80)
        
        result = db_session.execute(text("""
            SELECT 
                r.room_id,
                r.created_at,
                r.created_by,
                r.status,
                COUNT(DISTINCT CASE WHEN p.status = 'active' THEN p.user_id END) as active_participants,
                COUNT(DISTINCT p.user_id) as total_participants
            FROM rooms r
            LEFT JOIN participants p ON r.room_id = p.room_id
            WHERE r.room_id = :room_id
            GROUP BY r.room_id, r.created_at, r.created_by, r.status
        """), {"room_id": room_id})
        
        room = result.fetchone()
        
        if room:
            print(f"Room ID: {room[0]}")
            print(f"Created At: {room[1]}")
            print(f"Created By: {room[2] or 'N/A'}")
            print(f"Status: {room[3]}")
            print(f"Active Participants: {room[4]}")
            print(f"Total Participants: {room[5]}")
            
            # Show participants
            participants_result = db_session.execute(text("""
                SELECT user_id, username, joined_at, status
                FROM participants
                WHERE room_id = :room_id
                ORDER BY joined_at DESC
            """), {"room_id": room_id})
            
            participants = participants_result.fetchall()
            if participants:
                print("\nParticipants:")
                for p in participants:
                    print(f"  - User: {p[0]} ({p[1] or 'No name'}) | Joined: {p[2]} | Status: {p[3]}")
        else:
            print(f"Room {room_id} not found.")
    else:
        print("Please provide a room_id to view details.")

def view_statistics(db_session):
    """View database statistics."""
    print("\n" + "="*80)
    print("DATABASE STATISTICS")
    print("="*80)
    
    stats = db_session.execute(text("""
        SELECT 
            (SELECT COUNT(*) FROM rooms WHERE status = 'active') as active_rooms,
            (SELECT COUNT(*) FROM rooms WHERE status = 'ended') as ended_rooms,
            (SELECT COUNT(*) FROM participants WHERE status = 'active') as active_participants,
            (SELECT COUNT(*) FROM participants WHERE status = 'left') as left_participants,
            (SELECT COUNT(*) FROM sessions WHERE status = 'connected') as active_sessions
    """))
    
    stat = stats.fetchone()
    active_rooms, ended_rooms, active_participants, left_participants, active_sessions = stat
    
    print(f"Active Rooms: {active_rooms}")
    print(f"Ended Rooms: {ended_rooms}")
    print(f"Active Participants: {active_participants}")
    print(f"Left Participants: {left_participants}")
    print(f"Active Sessions: {active_sessions}")

def main():
    """Main function to view database data."""
    try:
        # Create engine and session
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        db_session = Session()
        
        print("\n" + "="*80)
        print("VIDEO CONFERENCING DATABASE VIEWER")
        print("="*80)
        
        # Show statistics
        view_statistics(db_session)
        
        # Show all data
        view_rooms(db_session)
        view_participants(db_session)
        view_sessions(db_session)
        
        # If room_id provided as argument, show details
        if len(sys.argv) > 1:
            room_id = sys.argv[1]
            view_room_details(db_session, room_id)
        
        db_session.close()
        
        print("\n" + "="*80)
        print("Done!")
        print("="*80)
        print("\nUsage:")
        print("  python database/view_data.py              # View all data")
        print("  python database/view_data.py <room_id>    # View specific room details")
        
    except Exception as e:
        print(f"\n❌ Error connecting to database: {e}")
        print("\nMake sure:")
        print("  1. PostgreSQL is running")
        print("  2. Database is initialized (run: python database/init_db.py)")
        print("  3. .env file has correct credentials")
        sys.exit(1)

if __name__ == '__main__':
    main()


