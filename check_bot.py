#!/usr/bin/env python3
"""
Check bot status
"""

import requests
import json

def check_bot():
    """Check if bot is working"""
    
    bot_token = "8389757663:AAHp0ReUexESfHDuif86Nhz5IwC293oPRzk"
    
    print("🔍 Checking bot status...")
    print("=" * 40)
    
    # Check bot info
    try:
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe")
        data = response.json()
        
        if data.get('ok'):
            result = data['result']
            print(f"✅ Bot is online")
            print(f"   Name: {result['first_name']}")
            print(f"   Username: @{result['username']}")
            print(f"   ID: {result['id']}")
        else:
            print(f"❌ Bot error: {data}")
            return
    except Exception as e:
        print(f"❌ Error checking bot: {e}")
        return
    
    # Check updates
    try:
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getUpdates")
        data = response.json()
        
        if data.get('ok'):
            updates = data['result']
            print(f"\n📨 Updates: {len(updates)}")
            
            if updates:
                last_update = updates[-1]
                print(f"   Last update ID: {last_update.get('update_id')}")
                
                if 'message' in last_update:
                    msg = last_update['message']
                    text = msg.get('text', 'No text')
                    from_user = msg.get('from', {})
                    name = from_user.get('first_name', 'Unknown')
                    print(f"   Last message: '{text}' from {name}")
                elif 'callback_query' in last_update:
                    cb = last_update['callback_query']
                    data_text = cb.get('data', 'No data')
                    from_user = cb.get('from', {})
                    name = from_user.get('first_name', 'Unknown')
                    print(f"   Last callback: '{data_text}' from {name}")
            else:
                print("   No recent updates")
        else:
            print(f"❌ Error getting updates: {data}")
    except Exception as e:
        print(f"❌ Error checking updates: {e}")

if __name__ == "__main__":
    check_bot()
