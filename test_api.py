"""
Скрипт для тестирования DeepSeek API
"""

import asyncio
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

async def test_deepseek_api():
    """Тестирует подключение к DeepSeek API"""
    
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_BASE_URL = "https://api.deepseek.com"
    
    if not DEEPSEEK_API_KEY:
        print("❌ DEEPSEEK_API_KEY не найден в .env файле")
        return False
    
    client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    
    print("🔍 Тестируем подключение к DeepSeek API...")
    
    try:
        response = await client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "user", "content": "Привет! Это тест подключения. Ответь кратко."}
            ],
            stream=False
        )
        
        result = response.choices[0].message.content
        print(f"✅ API работает! Ответ: {result[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка API: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_deepseek_api())
