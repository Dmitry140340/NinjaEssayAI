# 🔧 Критические исправления для bot.py

## 1. Исправление незавершенных функций

### Функция sanitize_filename
```python
def sanitize_filename(text: str) -> str:
    """Безопасная очистка имени файла"""
    if not text:
        return "default"
    
    # Убираем опасные символы
    safe_text = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', text)
    # Ограничиваем длину
    safe_text = safe_text[:50].strip()
    # Убираем точки в начале и конце (скрытые файлы/папки)
    safe_text = safe_text.strip('.')
    return safe_text if safe_text else "default"
```

### Функция log_user_action
```python
async def log_user_action(user_id: str, action: str):
    session = SessionLocal()
    try:
        user_action = UserAction(
            user_id=str(user_id), 
            action=action,
            timestamp=datetime.now(datetime.UTC)  # Заменить deprecated utcnow()
        )
        session.add(user_action)
        session.commit()
        logging.info(f"User action logged: {action} for user {user_id}")
    except Exception as e:
        session.rollback()
        logging.error(f"Ошибка записи действия пользователя: {e}")
        raise
    finally:
        session.close()
```

### Функция validate_user_input
```python
def validate_user_input(text: str, max_length: int = 1000) -> str:
    """Валидация пользовательского ввода"""
    if not text:
        raise ValueError("Пустой ввод не допускается")
    
    if len(text) > max_length:
        raise ValueError(f"Слишком длинный текст (максимум {max_length} символов)")
    
    # Убираем потенциально опасные теги и экранируем HTML
    cleaned_text = html.escape(text.strip())
    return cleaned_text
```

### Функция validate_contact
```python
def validate_contact(contact: str) -> str:
    """Валидация контактных данных"""
    contact = validate_user_input(contact, 100)
    
    # Дополнительная валидация для email/телефона
    pattern_email = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")
    pattern_phone = re.compile(r"^\+?\d{10,15}$")
    
    if not (pattern_email.match(contact) or pattern_phone.match(contact)):
        raise ValueError("Неверный формат контакта")
    
    return contact
```

### Функция get_chat_id
```python
def get_chat_id(context: CallbackContext, update: Update = None) -> int:
    """Безопасное получение chat_id"""
    if hasattr(context, '_chat_id') and context._chat_id:
        return context._chat_id
    elif update and update.effective_chat:
        return update.effective_chat.id
    elif update and update.message:
        return update.message.chat_id
    else:
        raise ValueError("Не удалось определить chat_id")
```

## 2. Исправление функций с заглушками

### work_theme_handler
```python
async def work_theme_handler(update: Update, context: CallbackContext) -> int:
    try:
        theme = validate_user_input(update.message.text, 200)
        context.user_data["work_theme"] = theme
    except ValueError as e:
        await update.message.reply_text(f"⚠️ {str(e)}. Попробуйте еще раз:")
        return WORK_THEME
    
    # Шаг 4 из 5: предпочтения
    await update.message.reply_text(
        "📝 Шаг 4/5: Укажите дополнительные предпочтения (стиль изложения, особые требования) или напишите 'нет':"
    )
    return PREFERENCES
```

### preferences_handler
```python
async def preferences_handler(update: Update, context: CallbackContext) -> int:
    try:
        preferences = validate_user_input(update.message.text, 500)
        context.user_data["preferences"] = preferences if preferences.lower() != 'нет' else None
    except ValueError as e:
        await update.message.reply_text(f"⚠️ {str(e)}. Попробуйте еще раз:")
        return PREFERENCES
    
    # Показываем сводку заказа
    work_type = context.user_data.get("work_type", "")
    science_name = context.user_data.get("science_name", "")
    page_number = context.user_data.get("page_number", 0)
    work_theme = context.user_data.get("work_theme", "")
    preferences = context.user_data.get("preferences", "Нет особых предпочтений")
    price = context.user_data.get("price", 0)
    
    summary = f"""
📋 *Сводка заказа:*

🔸 Тип работы: {work_type}
🔸 Дисциплина: {science_name}
🔸 Тема: {work_theme}
🔸 Количество страниц: {page_number}
🔸 Предпочтения: {preferences}
💰 Стоимость: {price}₽

📝 Шаг 5/5: Укажите email или телефон для отправки готовой работы:
    """
    
    await update.message.reply_text(summary, parse_mode='Markdown')
    return CUSTOMER_CONTACT
```

### contact_handler
```python
async def contact_handler(update: Update, context: CallbackContext) -> int:
    try:
        contact = validate_contact(update.message.text)
        context.user_data["receipt_customer"] = contact
    except ValueError:
        await update.message.reply_text(
            "⚠️ Неверный формат контакта. Попробуйте еще раз:"
        )
        return CUSTOMER_CONTACT
    
    # Показываем кнопку оплаты
    keyboard = [[InlineKeyboardButton("💳 Оплатить", callback_data="pay")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    price = context.user_data.get("price", 0)
    await update.message.reply_text(
        f"💳 Для завершения заказа нажмите кнопку оплаты.\n"
        f"Сумма к оплате: {price}₽",
        reply_markup=reply_markup
    )
    return PAYMENT
```

### create_payment
```python
async def create_payment(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    
    try:
        user_data = context.user_data
        price = user_data.get("price", 0)
        work_type = user_data.get("work_type", "")
        receipt_customer = user_data.get("receipt_customer", "")
        
        if not all([price, work_type, receipt_customer]):
            await query.edit_message_text("❌ Ошибка: неполные данные заказа")
            return ConversationHandler.END
        
        # Создаем платеж через YooKassa
        payment = Payment.create({
            "amount": {
                "value": f"{price}.00",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/your_bot_username"
            },
            "capture": True,
            "description": f"Оплата за {work_type}",
            "receipt": {
                "customer": {
                    "email": receipt_customer if "@" in receipt_customer else None,
                    "phone": receipt_customer if "@" not in receipt_customer else None
                },
                "items": [{
                    "description": work_type,
                    "quantity": "1.00",
                    "amount": {
                        "value": f"{price}.00",
                        "currency": "RUB"
                    },
                    "vat_code": 1
                }]
            }
        })
        
        # Сохраняем ID платежа
        context.user_data["payment_id"] = payment.id
        
        # Отправляем ссылку на оплату
        keyboard = [[InlineKeyboardButton("💳 Перейти к оплате", url=payment.confirmation.confirmation_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"💳 Платеж создан!\n"
            f"Сумма: {price}₽\n"
            f"ID платежа: {payment.id[:8]}...\n\n"
            f"Нажмите кнопку ниже для перехода к оплате:",
            reply_markup=reply_markup
        )
        
        # Запускаем мониторинг платежа
        chat_id = get_chat_id(context, update)
        asyncio.create_task(monitor_payment(context, chat_id, payment.id))
        
        return ConversationHandler.END
        
    except Exception as e:
        logging.error(f"Ошибка создания платежа: {e}")
        await query.edit_message_text(
            "❌ Ошибка при создании платежа. Попробуйте позже или обратитесь в поддержку."
        )
        return ConversationHandler.END
```

### monitor_payment
```python
async def monitor_payment(context: CallbackContext, chat_id: int, payment_id: str) -> None:
    """Мониторинг статуса платежа"""
    max_attempts = 30  # 5 минут с интервалом 10 секунд
    attempt = 0
    
    while attempt < max_attempts:
        try:
            payment = Payment.find_one(payment_id)
            
            if payment.status == "succeeded":
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="✅ Платеж успешно обработан! Начинаем подготовку вашего заказа..."
                )
                # Запускаем генерацию документа
                await process_order(context, chat_id)
                break
                
            elif payment.status == "canceled":
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ Платеж был отменен. Если это произошло по ошибке, создайте новый заказ."
                )
                break
                
            # Ждем 10 секунд перед следующей проверкой
            await asyncio.sleep(10)
            attempt += 1
            
        except Exception as e:
            logging.error(f"Ошибка мониторинга платежа {payment_id}: {e}")
            await asyncio.sleep(10)
            attempt += 1
    
    # Если платеж не был обработан за отведенное время
    if attempt >= max_attempts:
        await context.bot.send_message(
            chat_id=chat_id,
            text="⏳ Проверка статуса платежа заняла больше времени чем ожидалось. "
                 "Мы уведомим вас, как только платеж будет обработан."
        )
```

### process_order (новая функция)
```python
async def process_order(context: CallbackContext, chat_id: int) -> None:
    """Обработка заказа после успешной оплаты"""
    try:
        user_data = context.user_data
        
        # Отправляем сообщение о начале работы
        loading_message = await context.bot.send_message(
            chat_id=chat_id,
            text="🤖 Генерируем ваш заказ...\n⏳ Это может занять несколько минут."
        )
        
        # Генерируем план
        plan = await generate_plan(context)
        if not plan:
            raise ValueError("Не удалось сгенерировать план")
        
        # Обновляем сообщение
        await loading_message.edit_text(
            "📝 План готов! Генерируем текст...\n⏳ Пожалуйста, подождите."
        )
        
        # Генерируем текст
        content = await generate_text(plan, context)
        if not content:
            raise ValueError("Не удалось сгенерировать контент")
        
        # Создаем документ
        document_path = await create_document(plan, content, user_data)
        
        # Отправляем документ пользователю
        await loading_message.edit_text("📄 Отправляем готовый документ...")
        
        with open(document_path, 'rb') as doc:
            await context.bot.send_document(
                chat_id=chat_id,
                document=doc,
                filename=f"{sanitize_filename(user_data.get('work_theme', 'document'))}.docx",
                caption="✅ Ваш заказ готов! Спасибо за использование NinjaEssayAI 🥷"
            )
        
        # Удаляем сообщение загрузки
        await loading_message.delete()
        
        # Логируем успешное завершение
        user_id = user_data.get('user_id', 'unknown')
        await log_user_action(str(user_id), "order_completed")
        
    except Exception as e:
        logging.error(f"Ошибка обработки заказа: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Произошла ошибка при обработке заказа. "
                 "Обратитесь в поддержку, указав ID вашего платежа."
        )
```

## 3. Исправление generate_plan

```python
async def generate_plan(context: CallbackContext) -> list:
    """Генерирует план работы с улучшенной обработкой ошибок"""
    try:
        user_data = context.user_data
        
        # Проверяем наличие необходимых данных
        required_fields = ["work_type", "science_name", "work_theme", "page_number"]
        missing_fields = [field for field in required_fields if not user_data.get(field)]
        
        if missing_fields:
            logging.error(f"Отсутствуют данные для генерации плана: {missing_fields}")
            return []
        
        work_type = user_data["work_type"]
        science_name = user_data["science_name"]
        work_theme = user_data["work_theme"]
        page_number = user_data["page_number"]
        preferences = user_data.get("preferences", "")
        
        # Очищаем тип работы от эмодзи и цены
        clean_work_type = re.sub(r'[^\w\s]', '', work_type).strip()
        
        prompt = f"""
Создай план для академической работы типа "{clean_work_type}" по дисциплине "{science_name}" на тему "{work_theme}".

Требования:
- Объем работы: {page_number} страниц
- Стиль: академический, научный
- Дополнительные требования: {preferences if preferences else "Стандартные требования"}

Структура плана должна соответствовать типу работы:
- Для эссе: введение, основная часть (2-3 пункта), заключение
- Для доклада: введение, основные разделы, заключение, список литературы
- Для реферата: введение, основная часть (3-4 раздела), заключение, список литературы
- Для проекта: введение, теоретическая часть, практическая часть, заключение
- Для курсовой: введение, теоретическая глава, практическая глава, заключение, список литературы

Верни только пронумерованный список пунктов плана, каждый пункт с новой строки.
Не добавляй никаких вводных фраз или комментариев.
        """
        
        # Используем семафор для ограничения одновременных запросов
        async with GENERATION_SEMAPHORE:
            response = await client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.7,
                timeout=30.0
            )
        
        content = response.choices[0].message.content.strip()
        
        # Парсим план
        plan_lines = [line.strip() for line in content.split('\n') if line.strip()]
        plan_array = []
        
        for line in plan_lines:
            # Убираем нумерацию и очищаем
            clean_line = re.sub(r'^\d+\.?\s*', '', line).strip()
            if clean_line and len(clean_line) > 3:
                plan_array.append(clean_line)
        
        if len(plan_array) < 2:
            logging.warning("Сгенерированный план слишком короткий")
            # Возвращаем базовый план
            return [
                "Введение",
                f"Основная часть: {work_theme}",
                "Заключение"
            ]
        
        logging.info(f"Сгенерирован план из {len(plan_array)} пунктов")
        return plan_array
        
    except asyncio.TimeoutError:
        logging.error("Таймаут при генерации плана")
        return []
    except Exception as e:
        logging.error(f"Ошибка при вызове DeepSeek API: {e}")
        return []
```

## 4. Исправление generate_text

```python
async def generate_text(plan_array, context: CallbackContext) -> str:
    """Генерирует текст работы по плану"""
    if not plan_array:
        logging.error("Пустой план для генерации текста")
        return ""
    
    try:
        user_data = context.user_data
        work_type = user_data.get("work_type", "")
        science_name = user_data.get("science_name", "")
        work_theme = user_data.get("work_theme", "")
        page_number = user_data.get("page_number", 1)
        preferences = user_data.get("preferences", "")
        
        # Рассчитываем примерный объем на раздел
        words_per_page = 300
        total_words = page_number * words_per_page
        words_per_section = total_words // len(plan_array)
        
        full_text = ""
        
        # Генерируем текст для каждого раздела
        for i, chapter in enumerate(plan_array, 1):
            try:
                prompt = f"""
Напиши раздел академической работы на тему "{work_theme}" по дисциплине "{science_name}".

Раздел: {chapter}
Примерный объем: {words_per_section} слов
Стиль: академический, научный
Дополнительные требования: {preferences if preferences else "Стандартные требования"}

Требования к тексту:
- Используй научную терминологию
- Структурируй информацию логично
- Избегай повторений
- Не используй вводные фразы типа "В этом разделе рассмотрим..."
- Начинай сразу с содержательной части

Верни только текст раздела без заголовка.
                """
                
                async with GENERATION_SEMAPHORE:
                    response = await client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=min(1500, words_per_section * 2),
                        temperature=0.7,
                        timeout=45.0
                    )
                
                section_text = response.choices[0].message.content.strip()
                
                # Валидируем и очищаем контент
                try:
                    cleaned_text = validate_generated_content(section_text, chapter)
                    full_text += f"{chapter}\n\n{cleaned_text}\n\n"
                    logging.info(f"Сгенерирован раздел {i}/{len(plan_array)}: {chapter}")
                except ValueError as ve:
                    logging.warning(f"Проблема с контентом раздела {chapter}: {ve}")
                    # Используем базовый текст в случае проблем
                    fallback_text = f"Данный раздел посвящен изучению {chapter.lower()}. "
                    full_text += f"{chapter}\n\n{fallback_text}\n\n"
                
                # Небольшая пауза между запросами
                await asyncio.sleep(1)
                
            except asyncio.TimeoutError:
                logging.error(f"Таймаут при генерации раздела: {chapter}")
                continue
            except Exception as e:
                logging.error(f"Ошибка генерации раздела {chapter}: {e}")
                continue
        
        if not full_text.strip():
            logging.error("Не удалось сгенерировать текст")
            return ""
        
        logging.info(f"Генерация текста завершена. Общий объем: {len(full_text)} символов")
        return full_text
        
    except Exception as e:
        logging.error(f"Критическая ошибка при генерации текста: {e}")
        return ""
```

Эти исправления решают основные критические проблемы в коде и делают бота более стабильным и надежным.
