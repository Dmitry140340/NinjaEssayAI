#!/bin/bash

# Скрипт для обновления бота на сервере
cd /home/ninja/NinjaEssayAI

# Останавливаем сервис
sudo systemctl stop ninjaessayai-bot

# Получаем последние изменения
git pull origin main

# Устанавливаем зависимости (если есть новые)
pip3 install -r requirements.txt

# Запускаем сервис обратно
sudo systemctl start ninjaessayai-bot

# Проверяем статус
sudo systemctl status ninjaessayai-bot

echo "Обновление завершено!"
