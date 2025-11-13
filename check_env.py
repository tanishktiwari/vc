"""
Debug script to check environment variables.
This can help diagnose if DATABASE_URL is being read correctly.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("ENVIRONMENT VARIABLE CHECK")
print("=" * 60)

# Check DATABASE_URL
database_url = os.getenv('DATABASE_URL')
if database_url:
    # Mask password for security
    if '@' in database_url:
        parts = database_url.split('@')
        if ':' in parts[0]:
            user_pass = parts[0].split(':')
            if len(user_pass) >= 2:
                masked = f"{user_pass[0]}:****@{parts[1]}"
                print(f"✅ DATABASE_URL is set: {masked}")
            else:
                print(f"✅ DATABASE_URL is set: {database_url[:50]}...")
        else:
            print(f"✅ DATABASE_URL is set: {database_url[:50]}...")
    else:
        print(f"✅ DATABASE_URL is set: {database_url[:50]}...")
else:
    print("❌ DATABASE_URL is NOT set")

# Check individual variables
print("\nIndividual variables:")
print(f"  DB_HOST: {os.getenv('DB_HOST', 'NOT SET')}")
print(f"  DB_PORT: {os.getenv('DB_PORT', 'NOT SET')}")
print(f"  DB_NAME: {os.getenv('DB_NAME', 'NOT SET')}")
print(f"  DB_USER: {os.getenv('DB_USER', 'NOT SET')}")
print(f"  DB_PASSWORD: {'SET' if os.getenv('DB_PASSWORD') else 'NOT SET'}")

# Check database configuration logic
print("\n" + "=" * 60)
print("CONFIGURATION CHECK")
print("=" * 60)

db_configured = bool(
    os.getenv('DATABASE_URL') or 
    os.getenv('DB_PASSWORD') or 
    (os.getenv('DB_NAME') and os.getenv('DB_NAME') != 'video_conferencing')
)

if db_configured:
    print("✅ Database is configured")
else:
    print("❌ Database is NOT configured")

print("\n" + "=" * 60)

