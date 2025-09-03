#!/usr/bin/env python3
"""
Скрипт для обновления бота через HTTP запрос
"""

import requests
import sys

def update_bot_via_http(server_ip, secret_key="ninja_update_2025"):
    """Обновление бота через HTTP API"""
    try:
        url = f"http://{server_ip}/admin/update"
        headers = {
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, headers=headers, json={"action": "update"})
        
        if response.status_code == 200:
            print("✅ Бот успешно обновлен!")
            return True
        else:
            print(f"❌ Ошибка обновления: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    server_ip = "194.87.143.40"
    if len(sys.argv) > 1:
        server_ip = sys.argv[1]
    
    print(f"🔄 Обновление бота на сервере {server_ip}...")
    success = update_bot_via_http(server_ip)
    
    if not success:
        print("ℹ️ HTTP API недоступен, попробуйте подключиться по SSH позже")
        sys.exit(1)
