"""
🔍 Комплексная проверка бота NinjaEssayAI
Этот скрипт проверяет все аспекты бота перед запуском
"""

import os
import sys
import importlib.util
from pathlib import Path

def check_emoji(status: bool) -> str:
    """Возвращает эмодзи в зависимости от статуса"""
    return "✅" if status else "❌"

def print_section(title: str):
    """Печатает заголовок секции"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def check_file_exists(filepath: str, description: str) -> bool:
    """Проверяет существование файла"""
    exists = Path(filepath).exists()
    print(f"{check_emoji(exists)} {description}: {filepath}")
    return exists

def check_env_variable(var_name: str, description: str) -> bool:
    """Проверяет наличие переменной окружения"""
    value = os.getenv(var_name)
    exists = value is not None and value != ""
    status = check_emoji(exists)
    masked_value = value[:4] + "..." if exists and len(value) > 4 else "НЕ ЗАДАНА"
    print(f"{status} {description}: {masked_value}")
    return exists

def check_module_import(module_name: str, description: str) -> bool:
    """Проверяет возможность импорта модуля"""
    try:
        __import__(module_name)
        print(f"✅ {description}: установлен")
        return True
    except ImportError as e:
        print(f"❌ {description}: НЕ УСТАНОВЛЕН - {e}")
        return False

def main():
    """Основная функция проверки"""
    print("\n" + "🔍" * 35)
    print("  КОМПЛЕКСНАЯ ПРОВЕРКА БОТА NinjaEssayAI")
    print("🔍" * 35)
    
    all_checks = []
    
    # 1. Проверка файлов проекта
    print_section("📁 ФАЙЛЫ ПРОЕКТА")
    all_checks.append(check_file_exists("bot.py", "Основной файл бота"))
    all_checks.append(check_file_exists("requirements.txt", "Зависимости"))
    all_checks.append(check_file_exists(".env", "Файл переменных окружения"))
    all_checks.append(check_file_exists("README.md", "Документация"))
    all_checks.append(check_file_exists("TESTING.md", "Инструкции по тестированию"))
    
    # 2. Проверка переменных окружения
    print_section("🔑 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ")
    
    # Загружаем .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Файл .env загружен")
    except Exception as e:
        print(f"❌ Ошибка загрузки .env: {e}")
        all_checks.append(False)
    
    all_checks.append(check_env_variable("TELEGRAM_BOT_TOKEN", "Токен Telegram"))
    all_checks.append(check_env_variable("DEEPSEEK_API_KEY", "API ключ DeepSeek"))
    yookassa_shop = check_env_variable("YOOKASSA_SHOP_ID", "YooKassa Shop ID")
    yookassa_key = check_env_variable("YOOKASSA_SECRET_KEY", "YooKassa Secret Key")
    
    if not (yookassa_shop and yookassa_key):
        print("⚠️  ПРЕДУПРЕЖДЕНИЕ: YooKassa не настроена, платежи не будут работать")
    
    # 3. Проверка зависимостей
    print_section("📦 ЗАВИСИМОСТИ Python")
    dependencies = [
        ("telegram", "python-telegram-bot"),
        ("openai", "openai (DeepSeek API)"),
        ("docx", "python-docx"),
        ("dotenv", "python-dotenv"),
        ("sqlalchemy", "SQLAlchemy"),
        ("yookassa", "YooKassa SDK"),
    ]
    
    for module, description in dependencies:
        all_checks.append(check_module_import(module, description))
    
    # 4. Проверка импорта основного модуля
    print_section("🤖 МОДУЛЬ БОТА")
    try:
        import bot
        print("✅ Модуль bot.py импортирован успешно")
        
        # Проверяем основные переменные
        print(f"\n📊 Конфигурация бота:")
        print(f"   • Тестовый режим: {'ВКЛ 🧪' if bot.TESTING_MODE else 'ВЫКЛ 💳'}")
        print(f"   • Администраторы: {len(bot.ADMIN_IDS)} чел.")
        print(f"   • Rate limit: {bot.MAX_REQUESTS_PER_HOUR} запросов/час")
        print(f"   • Окно времени: {bot.REQUEST_WINDOW} сек")
        
        # Проверяем функции
        print(f"\n🔧 Проверка основных функций:")
        test_results = []
        
        # Тест санитизации
        try:
            result = bot.sanitize_filename("Test<>File")
            assert '<' not in result and '>' not in result
            print(f"   ✅ sanitize_filename работает")
            test_results.append(True)
        except Exception as e:
            print(f"   ❌ sanitize_filename: {e}")
            test_results.append(False)
        
        # Тест валидации
        try:
            result = bot.validate_user_input("Test input")
            assert result == "Test input"
            print(f"   ✅ validate_user_input работает")
            test_results.append(True)
        except Exception as e:
            print(f"   ❌ validate_user_input: {e}")
            test_results.append(False)
        
        # Тест админ-функций
        try:
            result = bot.is_admin(bot.ADMIN_IDS[0])
            assert result == True
            print(f"   ✅ is_admin работает")
            test_results.append(True)
        except Exception as e:
            print(f"   ❌ is_admin: {e}")
            test_results.append(False)
        
        # Тест rate limiting
        try:
            result = bot.check_rate_limit(999999)
            assert result == True
            print(f"   ✅ check_rate_limit работает")
            test_results.append(True)
        except Exception as e:
            print(f"   ❌ check_rate_limit: {e}")
            test_results.append(False)
        
        all_checks.extend(test_results)
        all_checks.append(True)
        
    except Exception as e:
        print(f"❌ Ошибка импорта bot.py: {e}")
        all_checks.append(False)
    
    # 5. Проверка базы данных
    print_section("💾 БАЗА ДАННЫХ")
    db_file = "user_activity.db"
    if Path(db_file).exists():
        print(f"✅ База данных существует: {db_file}")
        size = Path(db_file).stat().st_size
        print(f"   Размер: {size} байт")
        all_checks.append(True)
    else:
        print(f"⚠️  База данных будет создана при первом запуске")
        all_checks.append(True)  # Не критично
    
    # 6. Проверка тестов
    print_section("🧪 АВТОМАТИЗИРОВАННЫЕ ТЕСТЫ")
    if Path("test_bot.py").exists():
        print("✅ Тестовый файл существует: test_bot.py")
        print("   Для запуска тестов: py test_bot.py")
        all_checks.append(True)
    else:
        print("⚠️  Тестовый файл не найден")
        all_checks.append(False)
    
    # 7. Итоговый отчет
    print_section("📊 ИТОГОВЫЙ ОТЧЕТ")
    
    total_checks = len(all_checks)
    passed_checks = sum(all_checks)
    failed_checks = total_checks - passed_checks
    success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
    
    print(f"\nВсего проверок: {total_checks}")
    print(f"✅ Успешно: {passed_checks}")
    print(f"❌ Провалено: {failed_checks}")
    print(f"📈 Процент успеха: {success_rate:.1f}%")
    
    # Финальное заключение
    print("\n" + "="*70)
    if success_rate >= 90:
        print("🎉 БОТ ГОТОВ К ЗАПУСКУ!")
        print("   Все критические проверки пройдены.")
        print("\n💡 Для запуска бота выполните:")
        print("   py bot.py")
    elif success_rate >= 70:
        print("⚠️  БОТ ЧАСТИЧНО ГОТОВ")
        print("   Некоторые проверки не пройдены, но бот может работать.")
        print("   Рекомендуется устранить проблемы перед запуском.")
    else:
        print("❌ БОТ НЕ ГОТОВ К ЗАПУСКУ")
        print("   Критические ошибки обнаружены.")
        print("   Необходимо устранить проблемы перед запуском.")
    print("="*70 + "\n")
    
    return 0 if success_rate >= 70 else 1

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Проверка прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка при проверке: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
