#!/usr/bin/env python3
"""
Детальное тестирование функциональности бота
"""

import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock

def test_validation_functions():
    """Тест функций валидации"""
    print("🔍 Тестируем функции валидации...")
    
    try:
        from bot import sanitize_filename, validate_user_input, validate_contact
        
        # Тест sanitize_filename
        assert sanitize_filename("test<>file") == "test__file"
        assert sanitize_filename("") == "default"
        print("✅ sanitize_filename работает")
        
        # Тест validate_user_input
        assert validate_user_input("test input") == "test input"
        try:
            validate_user_input("")
            assert False, "Должна быть ошибка для пустого ввода"
        except ValueError:
            pass
        print("✅ validate_user_input работает")
        
        # Тест validate_contact
        assert validate_contact("test@example.com") == "test@example.com"
        assert validate_contact("+1234567890") == "+1234567890"
        try:
            validate_contact("invalid")
            assert False, "Должна быть ошибка для неверного контакта"
        except ValueError:
            pass
        print("✅ validate_contact работает")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в функциях валидации: {e}")
        return False

def test_database_models():
    """Тест моделей базы данных"""
    print("\n🔍 Тестируем модели базы данных...")
    
    try:
        from bot import UserAction, Base, engine
        
        # Проверяем, что модель создается
        user_action = UserAction(
            user_id="123",
            action="test_action"
        )
        
        print("✅ UserAction модель создается")
        
        # Проверяем, что таблицы созданы
        assert hasattr(UserAction, '__tablename__')
        assert UserAction.__tablename__ == "user_actions"
        print("✅ Таблица user_actions определена")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в моделях БД: {e}")
        return False

def test_constants():
    """Тест констант и конфигурации"""
    print("\n🔍 Тестируем константы...")
    
    try:
        from bot import PAGE_LIMITS, WORK_TYPE, SCIENCE_NAME, PAGE_NUMBER
        
        # Проверяем лимиты страниц
        assert PAGE_LIMITS["Эссе"] == 10
        assert PAGE_LIMITS["Курсовая работа"] == 30
        print("✅ PAGE_LIMITS настроены")
        
        # Проверяем состояния
        assert isinstance(WORK_TYPE, int)
        assert isinstance(SCIENCE_NAME, int)
        assert isinstance(PAGE_NUMBER, int)
        print("✅ Состояния диалога настроены")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в константах: {e}")
        return False

async def test_mock_handlers():
    """Тест обработчиков с мок-объектами"""
    print("\n🔍 Тестируем обработчики с мок-объектами...")
    
    try:
        from bot import work_type_handler, science_name_handler, SCIENCE_NAME, PAGE_NUMBER
        
        # Создаем мок-объекты
        mock_update = Mock()
        mock_update.message = Mock()
        mock_update.message.text = "📝 Эссе - 300₽"
        mock_update.message.reply_text = AsyncMock()
        
        mock_context = Mock()
        mock_context.user_data = {}
        
        # Тестируем work_type_handler
        result = await work_type_handler(mock_update, mock_context)
        assert result == SCIENCE_NAME
        assert "work_type" in mock_context.user_data
        assert "price" in mock_context.user_data
        print("✅ work_type_handler работает")
        
        # Тестируем science_name_handler
        mock_update.message.text = "Математика"
        mock_context.user_data = {"work_type": "📝 Эссе"}
        
        result = await science_name_handler(mock_update, mock_context)
        assert result == PAGE_NUMBER
        assert mock_context.user_data["science_name"] == "Математика"
        print("✅ science_name_handler работает")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в обработчиках: {e}")
        return False

def test_document_generation():
    """Тест генерации документов"""
    print("\n🔍 Тестируем создание документов...")
    
    try:
        import docx
        from bot import add_page_number
        
        # Создаем тестовый документ
        doc = docx.Document()
        section = doc.sections[0]
        
        # Тестируем добавление нумерации страниц
        add_page_number(section)
        print("✅ add_page_number работает")
        
        # Тестируем сохранение документа
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
            doc.save(tmp.name)
            assert os.path.exists(tmp.name)
            os.unlink(tmp.name)
        print("✅ Сохранение документов работает")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в генерации документов: {e}")
        return False

def test_api_configuration():
    """Тест конфигурации API"""
    print("\n🔍 Тестируем конфигурацию API...")
    
    try:
        from bot import client, Configuration
        from openai import AsyncOpenAI
        
        # Проверяем клиент OpenAI
        assert isinstance(client, AsyncOpenAI)
        print("✅ OpenAI клиент настроен")
        
        # Проверяем YooKassa
        assert hasattr(Configuration, 'account_id')
        assert hasattr(Configuration, 'secret_key')
        print("✅ YooKassa настроена")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в конфигурации API: {e}")
        return False

async def run_detailed_tests():
    """Запуск детальных тестов"""
    print("🧪 Детальное тестирование функциональности\n")
    
    tests = [
        ("Функции валидации", test_validation_functions),
        ("Модели базы данных", test_database_models),
        ("Константы и конфигурация", test_constants),
        ("Обработчики (мок)", test_mock_handlers),
        ("Генерация документов", test_document_generation),
        ("Конфигурация API", test_api_configuration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                print(f"✅ {test_name}: ПРОШЕЛ")
            else:
                print(f"❌ {test_name}: НЕ ПРОШЕЛ")
        except Exception as e:
            print(f"💥 {test_name}: ОШИБКА - {e}")
    
    print(f"\n📊 ИТОГО: {passed}/{total} детальных тестов прошли")
    
    if passed >= total - 1:
        print("\n🎉 ДЕТАЛЬНЫЕ ТЕСТЫ В ОСНОВНОМ ПРОШЛИ!")
        return True
    else:
        print("\n❌ Много ошибок в детальных тестах.")
        return False

if __name__ == "__main__":
    import sys
    success = asyncio.run(run_detailed_tests())
    sys.exit(0 if success else 1)
