"""
Quick script to test Supabase connection and diagnose DNS issues.
Run this to check your Supabase configuration.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "").strip()

print("=" * 60)
print("Supabase Connection Diagnostic Tool")
print("=" * 60)
print()

# Check if variables are set
print("1. Environment Variables Check:")
print(f"   SUPABASE_URL: {'[OK] Set' if SUPABASE_URL else '[ERROR] NOT SET'}")
if SUPABASE_URL:
    print(f"   URL Preview: {SUPABASE_URL[:60]}...")
print(f"   SUPABASE_SERVICE_KEY: {'[OK] Set' if SUPABASE_KEY else '[ERROR] NOT SET'}")
if SUPABASE_KEY:
    print(f"   Key Length: {len(SUPABASE_KEY)} characters")
print()

# Test DNS resolution
print("2. DNS Resolution Test:")
try:
    import socket
    from urllib.parse import urlparse
    
    parsed = urlparse(SUPABASE_URL)
    hostname = parsed.hostname
    
    if hostname:
        print(f"   Hostname: {hostname}")
        try:
            ip_address = socket.gethostbyname(hostname)
            print(f"   [SUCCESS] DNS Resolution: OK")
            print(f"   IP Address: {ip_address}")
        except socket.gaierror as e:
            print(f"   [FAILED] DNS Resolution: ERROR")
            print(f"   Error: {e}")
            print()
            print("   Possible causes:")
            print("   - Supabase project is PAUSED (most common)")
            print("   - Supabase project is DELETED")
            print("   - Incorrect project ID")
            print("   - Network/DNS issue")
            print()
            print("   Solutions:")
            print("   1. Go to https://supabase.com/dashboard")
            print("   2. Check if your project is active (not paused)")
            print("   3. If paused, click 'Restore' or 'Resume'")
            print("   4. Verify the project ID matches your .env file")
    else:
        print("   [ERROR] Could not extract hostname from URL")
except Exception as e:
    print(f"   ❌ Error testing DNS: {e}")
print()

# Test HTTP connection
print("3. HTTP Connection Test:")
if SUPABASE_URL:
    try:
        import urllib.request
        import urllib.error
        
        # Try to connect to the URL
        req = urllib.request.Request(SUPABASE_URL)
        req.add_header('apikey', SUPABASE_KEY if SUPABASE_KEY else 'test')
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                print(f"   [SUCCESS] HTTP Connection: OK")
                print(f"   Status Code: {response.getcode()}")
        except urllib.error.HTTPError as e:
            if e.code == 401:
                print(f"   [WARNING] HTTP Connection: Connected but authentication failed")
                print(f"   This is OK - it means DNS works, just need correct API key")
            else:
                print(f"   [WARNING] HTTP Connection: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            print(f"   [FAILED] HTTP Connection: ERROR")
            print(f"   Error: {e.reason}")
            if "getaddrinfo" in str(e).lower() or "name resolution" in str(e).lower():
                print("   This confirms DNS resolution is failing")
    except Exception as e:
        print(f"   ❌ Error testing HTTP: {e}")
else:
    print("   [SKIPPED] SUPABASE_URL not set")
print()

# Test Supabase client
print("4. Supabase Client Test:")
try:
    from supabase import create_client
    
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            client = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("   [SUCCESS] Client Creation: OK")
            
            # Try a simple query
            try:
                result = client.table("resumes").select("id").limit(1).execute()
                print("   [SUCCESS] Database Query: OK")
                print("   Connection is working!")
            except Exception as e:
                error_str = str(e).lower()
                if "getaddrinfo" in error_str or "dns" in error_str or "errno 11001" in error_str:
                    print("   [FAILED] Database Query: DNS ERROR")
                    print(f"   Error: {e}")
                    print()
                    print("   [ACTION REQUIRED]")
                    print("   Your Supabase project is likely PAUSED or DELETED")
                    print("   Go to https://supabase.com/dashboard and check your project status")
                else:
                    print(f"   [WARNING] Database Query: {e}")
        except Exception as e:
            error_str = str(e).lower()
            if "getaddrinfo" in error_str or "dns" in error_str or "errno 11001" in error_str:
                print("   [FAILED] Client Creation: DNS ERROR")
                print(f"   Error: {e}")
            else:
                print(f"   [ERROR] Client Creation: {e}")
    else:
        print("   [SKIPPED] Missing URL or KEY")
except ImportError:
    print("   [ERROR] Supabase library not installed")
    print("   Run: pip install supabase")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()
print("=" * 60)
print("Diagnostic Complete")
print("=" * 60)
print()
print("Next Steps:")
print("1. If DNS resolution failed -> Check Supabase Dashboard")
print("2. If project is paused -> Click 'Restore' in dashboard")
print("3. If project ID is wrong -> Update .env file with correct URL")
print("4. If all tests pass -> Your connection is working!")
