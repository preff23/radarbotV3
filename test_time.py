#!/usr/bin/env python3
"""
Test time parsing fix
"""

import subprocess
from datetime import datetime
import pytz

def test_time_sources():
    """Test different time sources"""
    
    print("🕐 Testing Time Sources...")
    print("=" * 50)
    
    # Test 1: System command
    print("1️⃣ Testing system command...")
    try:
        result = subprocess.run(['TZ=Europe/Moscow', 'date', '+%d.%m.%Y, %H:%M МСК'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            moscow_time = result.stdout.strip()
            print(f"✅ System command: {moscow_time}")
        else:
            print(f"❌ System command failed: {result.stderr}")
    except Exception as e:
        print(f"❌ System command error: {e}")
    
    # Test 2: Python datetime with pytz
    print("\n2️⃣ Testing Python datetime with pytz...")
    try:
        moscow_tz = pytz.timezone('Europe/Moscow')
        moscow_time = datetime.now(moscow_tz).strftime('%d.%m.%Y, %H:%M МСК')
        print(f"✅ Python datetime: {moscow_time}")
    except Exception as e:
        print(f"❌ Python datetime error: {e}")
    
    # Test 3: Fallback datetime
    print("\n3️⃣ Testing fallback datetime...")
    try:
        moscow_time = datetime.now().strftime('%d.%m.%Y, %H:%M МСК')
        print(f"✅ Fallback datetime: {moscow_time}")
    except Exception as e:
        print(f"❌ Fallback datetime error: {e}")
    
    print("\n🏁 Time testing completed!")

if __name__ == "__main__":
    test_time_sources()
