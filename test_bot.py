import pytest
import asyncio
import os
import tempfile
import shutil
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from telegram import Update, User, Message, Chat, CallbackQuery
from telegram.ext import CallbackContext
import sqlite3
from datetime import datetime

# Импортируем наш бот
import sys
sys.path.append('.')
from bot import (
    start, help_command, menu, continue_handler, order, 
    work_type_handler, science_name_handler, page_number_handler,
    work_theme_handler, preferences_handler, contact_handler,
    create_payment, generate_plan, generate_text,
    cancel, log_user_action, UserAction, Base, engine, SessionLocal
)

class TestBot:
    """Тесты для Telegram бота NinjaEssayAI"""
    
    @pytest.fixture
    def setup_test_db(self):
        """Создаем тестовую базу данных"""
        # Создаем временную базу данных для тестов
        test_db_path = ":memory:"
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        test_engine = create_engine(f"sqlite:///{test_db_path}")
        Base.metadata.create_all(bind=test_engine)
        TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
        
        yield TestSessionLocal
        
    @pytest.fixture
    def mock_update(self):
        """Создаем мок-объект Update"""
        update = Mock(spec=Update)
        update.effective_user = Mock(spec=User)
        update.effective_user.id = 12345
        update.effective_user.username = "testuser"
        
        update.message = Mock(spec=Message)
        update.message.chat = Mock(spec=Chat)
        update.message.chat.id = 67890
        update.message.reply_text = AsyncMock()
        update.message.reply_document = AsyncMock()
        update.message.text = "тестовое сообщение"
        
        return update
    
    @pytest.fixture
    def mock_context(self):
        """Создаем мок-объект CallbackContext"""
        context = Mock(spec=CallbackContext)
        context.user_data = {}
        context.bot = Mock()
        context.bot.send_message = AsyncMock()
        context.bot.send_document = AsyncMock()
        context.bot.username = "testbot"
        context._chat_id = 67890
        return context
    
    @pytest.mark.asyncio
    async def test_start_command(self, mock_update, mock_context):
        """Тестируем команду /start"""
        with patch('bot.log_user_action') as mock_log:
            await start(mock_update, mock_context)
            
            # Проверяем, что логирование вызвано
            mock_log.assert_called_once_with(12345, "start_command")
            
            # Проверяем, что отправлено приветственное сообщение
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args[0][0]
            assert "NinjaEssayAI" in call_args
            assert "пользовательским соглашением" in call_args
    
    @pytest.mark.asyncio
    async def test_help_command(self, mock_update, mock_context):
        """Тестируем команду /help"""
        await help_command(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "/order" in call_args
        assert "/cancel" in call_args
        assert "/help" in call_args
    
    @pytest.mark.asyncio
    async def test_menu_command(self, mock_update, mock_context):
        """Тестируем команду /menu"""
        await menu(mock_update, mock_context)
        
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Меню команд" in call_args
    
    @pytest.mark.asyncio
    async def test_continue_handler(self, mock_update, mock_context):
        """Тестируем обработчик кнопки 'Продолжить'"""
        with patch('bot.log_user_action') as mock_log:
            await continue_handler(mock_update, mock_context)
            
            mock_log.assert_called_once_with(12345, "accepted_terms")
            mock_update.message.reply_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_order_command(self, mock_update, mock_context):
        """Тестируем команду /order"""
        with patch('bot.log_user_action') as mock_log:
            result = await order(mock_update, mock_context)
            
            mock_log.assert_called_once_with(12345, "order_command")
            mock_update.message.reply_text.assert_called_once()
            
            # Проверяем, что возвращается правильное состояние
            from bot import WORK_TYPE
            assert result == WORK_TYPE
    
    @pytest.mark.asyncio
    async def test_work_type_handler(self, mock_update, mock_context):
        """Тестируем обработчик выбора типа работы"""
        mock_update.message.text = "📝 Эссе - 300₽"
        
        result = await work_type_handler(mock_update, mock_context)
        
        # Проверяем, что данные сохранены
        assert mock_context.user_data["work_type"] == "📝 Эссе"
        assert mock_context.user_data["price"] == 300
        
        from bot import SCIENCE_NAME
        assert result == SCIENCE_NAME
    
    @pytest.mark.asyncio
    async def test_science_name_handler(self, mock_update, mock_context):
        """Тестируем обработчик названия дисциплины"""
        mock_update.message.text = "Математика"
        mock_context.user_data = {"work_type": "📝 Эссе"}
        
        result = await science_name_handler(mock_update, mock_context)
        
        assert mock_context.user_data["science_name"] == "Математика"
        from bot import PAGE_NUMBER
        assert result == PAGE_NUMBER
    
    @pytest.mark.asyncio
    async def test_page_number_handler_valid(self, mock_update, mock_context):
        """Тестируем обработчик количества страниц - корректный ввод"""
        mock_update.message.text = "5"
        mock_context.user_data = {"work_type": "📝 Эссе"}
        
        result = await page_number_handler(mock_update, mock_context)
        
        assert mock_context.user_data["page_number"] == 5
        from bot import WORK_THEME
        assert result == WORK_THEME
    
    @pytest.mark.asyncio
    async def test_page_number_handler_invalid(self, mock_update, mock_context):
        """Тестируем обработчик количества страниц - некорректный ввод"""
        mock_update.message.text = "abc"
        mock_context.user_data = {"work_type": "📝 Эссе"}
        
        result = await page_number_handler(mock_update, mock_context)
        
        # Должен остаться в том же состоянии
        from bot import PAGE_NUMBER
        assert result == PAGE_NUMBER
        mock_update.message.reply_text.assert_called_with("⚠️ Пожалуйста, введите число:")
    
    @pytest.mark.asyncio
    async def test_page_number_handler_exceeds_limit(self, mock_update, mock_context):
        """Тестируем обработчик количества страниц - превышение лимита"""
        mock_update.message.text = "15"  # Лимит для эссе - 10
        mock_context.user_data = {"work_type": "📝 Эссе"}
        
        result = await page_number_handler(mock_update, mock_context)
        
        from bot import PAGE_NUMBER
        assert result == PAGE_NUMBER
        mock_update.message.reply_text.assert_called()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "максимальное количество страниц" in call_args
    
    @pytest.mark.asyncio
    async def test_work_theme_handler(self, mock_update, mock_context):
        """Тестируем обработчик темы работы"""
        mock_update.message.text = "Интегралы и производные"
        
        result = await work_theme_handler(mock_update, mock_context)
        
        assert mock_context.user_data["work_theme"] == "Интегралы и производные"
        from bot import PREFERENCES
        assert result == PREFERENCES
    
    @pytest.mark.asyncio
    async def test_preferences_handler(self, mock_update, mock_context):
        """Тестируем обработчик предпочтений"""
        mock_update.message.text = "Научный стиль, много примеров"
        mock_context.user_data = {
            "work_type": "📝 Эссе",
            "science_name": "Математика",
            "work_theme": "Интегралы",
            "page_number": 5,
            "price": 300
        }
        
        result = await preferences_handler(mock_update, mock_context)
        
        assert mock_context.user_data["preferences"] == "Научный стиль, много примеров"
        from bot import CUSTOMER_CONTACT
        assert result == CUSTOMER_CONTACT
        
        # Проверяем, что показана сводка заказа
        mock_update.message.reply_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_contact_handler_valid_email(self, mock_update, mock_context):
        """Тестируем обработчик контакта - корректный email"""
        mock_update.message.text = "test@example.com"
        mock_context.user_data = {"work_type": "📝 Эссе", "price": 300}
        
        result = await contact_handler(mock_update, mock_context)
        
        assert mock_context.user_data["receipt_customer"] == "test@example.com"
        from bot import PAYMENT
        assert result == PAYMENT
    
    @pytest.mark.asyncio
    async def test_contact_handler_valid_phone(self, mock_update, mock_context):
        """Тестируем обработчик контакта - корректный телефон"""
        mock_update.message.text = "+71234567890"
        mock_context.user_data = {"work_type": "📝 Эссе", "price": 300}
        
        result = await contact_handler(mock_update, mock_context)
        
        assert mock_context.user_data["receipt_customer"] == "+71234567890"
        from bot import PAYMENT
        assert result == PAYMENT
    
    @pytest.mark.asyncio
    async def test_contact_handler_invalid(self, mock_update, mock_context):
        """Тестируем обработчик контакта - некорректный формат"""
        mock_update.message.text = "неправильный_контакт"
        mock_context.user_data = {"work_type": "📝 Эссе", "price": 300}
        
        result = await contact_handler(mock_update, mock_context)
        
        from bot import CUSTOMER_CONTACT
        assert result == CUSTOMER_CONTACT
        mock_update.message.reply_text.assert_called_with(
            "Неверный формат контакта. Введите корректный email или телефон (например, +71234567890):"
        )
    
    @pytest.mark.asyncio
    async def test_cancel_handler(self, mock_update, mock_context):
        """Тестируем обработчик отмены"""
        from telegram.ext import ConversationHandler
        
        result = await cancel(mock_update, mock_context)
        
        assert result == ConversationHandler.END
        mock_update.message.reply_text.assert_called_with("Заказ отменен.")
    
    @pytest.mark.asyncio 
    async def test_log_user_action(self, setup_test_db):
        """Тестируем логирование действий пользователя"""
        TestSessionLocal = setup_test_db
        
        with patch('bot.SessionLocal', TestSessionLocal):
            await log_user_action("12345", "test_action")
            
            # Проверяем, что запись добавлена в базу
            session = TestSessionLocal()
            try:
                action = session.query(UserAction).filter_by(user_id="12345").first()
                assert action is not None
                assert action.action == "test_action"
            finally:
                session.close()
    
    @pytest.mark.asyncio
    async def test_generate_plan_success(self, mock_context):
        """Тестируем успешную генерацию плана"""
        mock_context.user_data = {
            "science_name": "Математика",
            "work_type": "📝 Эссе", 
            "work_theme": "Интегралы",
            "preferences": "Научный стиль",
            "page_number": 4
        }
        
        # Мокаем ответ от OpenAI
        mock_response = AsyncMock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "1. Введение\n2. Основная часть"
        
        with patch('bot.client.chat.completions.create', return_value=mock_response):
            result = await generate_plan(mock_context)
            
            assert isinstance(result, list)
            assert len(result) == 2
            assert "Введение" in result[0]
            assert "Основная часть" in result[1]
    
    @pytest.mark.asyncio
    async def test_generate_plan_insufficient_data(self, mock_context):
        """Тестируем генерацию плана с недостающими данными"""
        mock_context.user_data = {
            "science_name": "Математика"
            # Отсутствуют другие необходимые поля
        }
        
        result = await generate_plan(mock_context)
        
        assert result == []
        mock_context.bot.send_message.assert_called()
    
    @pytest.mark.asyncio
    async def test_generate_text_empty_plan(self, mock_context):
        """Тестируем генерацию текста с пустым планом"""
        mock_context.user_data = {
            "science_name": "Математика",
            "work_type": "📝 Эссе",
            "work_theme": "Интегралы", 
            "preferences": "Научный стиль"
        }
        
        result = await generate_text([], mock_context)
        
        assert result == ""
        mock_context.bot.send_message.assert_called()
    
    def test_page_limits(self):
        """Тестируем лимиты страниц для разных типов работ"""
        from bot import PAGE_LIMITS
        
        assert PAGE_LIMITS["Эссе"] == 10
        assert PAGE_LIMITS["Доклад"] == 10
        assert PAGE_LIMITS["Реферат"] == 20
        assert PAGE_LIMITS["Проект"] == 20
        assert PAGE_LIMITS["Курсовая работа"] == 30
    
    @pytest.mark.asyncio
    async def test_create_payment_mock(self, mock_context):
        """Тестируем создание платежа (мок-версия)"""
        # Создаем мок для callback query
        mock_query = Mock()
        mock_query.answer = AsyncMock()
        mock_query.edit_message_text = AsyncMock()
        mock_query.message = Mock()
        mock_query.message.chat = Mock()
        mock_query.message.chat.id = 67890
        
        mock_update = Mock()
        mock_update.callback_query = mock_query
        
        mock_context.user_data = {
            "work_type": "📝 Эссе",
            "work_theme": "Интегралы",
            "price": 300,
            "receipt_customer": "test@example.com"
        }
        
        # Мокаем YooKassa Payment
        mock_payment = Mock()
        mock_payment.id = "test_payment_id"
        mock_payment.confirmation = Mock()
        mock_payment.confirmation.confirmation_url = "https://test.url"
        
        with patch('bot.Payment.create', return_value=mock_payment), \
             patch('bot.asyncio.create_task') as mock_create_task:
            
            from telegram.ext import ConversationHandler
            result = await create_payment(mock_update, mock_context)
            
            assert result == ConversationHandler.END
            assert mock_context.user_data["payment_id"] == "test_payment_id"
            mock_query.edit_message_text.assert_called_once()
            mock_create_task.assert_called_once()


class TestIntegration:
    """Интеграционные тесты"""
    
    @pytest.mark.asyncio
    async def test_full_order_flow_mock(self):
        """Тестируем полный процесс заказа (мок-версия)"""
        # Создаем мок-объекты
        mock_update = Mock(spec=Update)
        mock_update.effective_user = Mock(spec=User)
        mock_update.effective_user.id = 12345
        mock_update.message = Mock(spec=Message)
        mock_update.message.reply_text = AsyncMock()
        mock_update.message.chat = Mock(spec=Chat)
        mock_update.message.chat.id = 67890
        
        mock_context = Mock(spec=CallbackContext)
        mock_context.user_data = {}
        mock_context.bot = Mock()
        mock_context.bot.send_message = AsyncMock()
        
        # Проходим через все этапы заказа
        with patch('bot.log_user_action'):
            # 1. Начинаем заказ
            result1 = await order(mock_update, mock_context)
            from bot import WORK_TYPE
            assert result1 == WORK_TYPE
            
            # 2. Выбираем тип работы
            mock_update.message.text = "📝 Эссе - 300₽"
            result2 = await work_type_handler(mock_update, mock_context)
            from bot import SCIENCE_NAME
            assert result2 == SCIENCE_NAME
            
            # 3. Указываем дисциплину
            mock_update.message.text = "Математика"
            result3 = await science_name_handler(mock_update, mock_context)
            from bot import PAGE_NUMBER
            assert result3 == PAGE_NUMBER
            
            # 4. Указываем количество страниц
            mock_update.message.text = "5"
            result4 = await page_number_handler(mock_update, mock_context)
            from bot import WORK_THEME
            assert result4 == WORK_THEME
            
            # 5. Указываем тему
            mock_update.message.text = "Интегралы и производные"
            result5 = await work_theme_handler(mock_update, mock_context)
            from bot import PREFERENCES
            assert result5 == PREFERENCES
            
            # 6. Указываем предпочтения
            mock_update.message.text = "Научный стиль"
            result6 = await preferences_handler(mock_update, mock_context)
            from bot import CUSTOMER_CONTACT
            assert result6 == CUSTOMER_CONTACT
            
            # 7. Указываем контакт
            mock_update.message.text = "test@example.com"
            result7 = await contact_handler(mock_update, mock_context)
            from bot import PAYMENT
            assert result7 == PAYMENT
            
            # Проверяем, что все данные сохранены
            assert mock_context.user_data["work_type"] == "📝 Эссе"
            assert mock_context.user_data["price"] == 300
            assert mock_context.user_data["science_name"] == "Математика"
            assert mock_context.user_data["page_number"] == 5
            assert mock_context.user_data["work_theme"] == "Интегралы и производные"
            assert mock_context.user_data["preferences"] == "Научный стиль"
            assert mock_context.user_data["receipt_customer"] == "test@example.com"


def run_tests():
    """Запускаем все тесты"""
    print("🧪 Запуск тестов бота NinjaEssayAI...")
    
    # Проверяем наличие необходимых зависимостей
    try:
        import pytest
        print("✅ pytest найден")
    except ImportError:
        print("❌ pytest не установлен. Установите: pip install pytest")
        return False
    
    try:
        import asyncio
        print("✅ asyncio доступен")
    except ImportError:
        print("❌ asyncio недоступен")
        return False
    
    # Запускаем тесты
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x"  # Останавливаться на первой ошибке
    ])
    
    if exit_code == 0:
        print("🎉 Все тесты прошли успешно!")
        return True
    else:
        print("❌ Некоторые тесты не прошли")
        return False


if __name__ == "__main__":
    run_tests()
