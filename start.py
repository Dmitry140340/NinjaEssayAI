#!/usr/bin/env python3
"""
Скрипт запуска бота NinjaEssayAI
"""

import os
import sys
import logging
from pathlib import Path

def check_requirements():
    """Проверяет наличие всех необходимых файлов и настроек"""
    print("🔍 Проверка готовности к запуску...")
    
    # Проверяем .env файл
    if not Path(".env").exists():
        print("❌ Файл .env не найден!")
        print("📝 Скопируйте .env.example в .env и заполните своими ключами")
        return False
    
    # Проверяем основной файл
    if not Path("bot.py").exists():
        print("❌ Файл bot.py не найден!")
        return False
    
    # Проверяем папку для файлов
    Path("generated").mkdir(exist_ok=True)
    
    # Проверяем переменные окружения
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        "TELEGRAM_BOT_TOKEN",
        "DEEPSEEK_API_KEY",
        "YOOKASSA_SHOP_ID", 
        "YOOKASSA_SECRET_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var) == f"your_{var.lower()}":
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Не заполнены переменные: {', '.join(missing_vars)}")
        print("📝 Заполните их в файле .env")
        return False
    
    print("✅ Все проверки пройдены!")
    return True

def main():
    """Главная функция запуска"""
    print("🥷 NinjaEssayAI Bot Launcher")
    print("=" * 40)
    
    if not check_requirements():
        print("\n❌ Запуск невозможен. Исправьте ошибки выше.")
        sys.exit(1)
    
    print("\n🚀 Запускаем бота...")
    print("📊 Для остановки нажмите Ctrl+C")
    print("=" * 40)
    
    # Настраиваем логирование
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bot.log'),
            logging.StreamHandler()
        ]
    )
    
    try:
        # Импортируем и запускаем бота
        from bot import main as bot_main
        bot_main()
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        logging.exception("Критическая ошибка при запуске бота")
        sys.exit(1)

if __name__ == "__main__":
    main()
