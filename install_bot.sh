#!/bin/bash
# Скрипт установки NinjaEssayAI Bot на сервер
# Запуск: bash install_bot.sh

set -e

echo "🚀 Установка NinjaEssayAI Bot"
echo "=============================="

# Обновление системы
echo "📦 Обновление системы..."
apt-get update -y
apt-get upgrade -y

# Установка необходимых пакетов
echo "📦 Установка пакетов..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    nginx \
    fail2ban \
    htop \
    curl \
    sqlite3 \
    ufw

# Настройка firewall
echo "🔒 Настройка firewall..."
ufw --force enable
ufw allow ssh
ufw allow http
ufw allow https

# Создание директории для бота
echo "📁 Создание директории..."
mkdir -p /opt/ninjaessayai_bot
cd /opt/ninjaessayai_bot

# Клонирование репозитория
echo "📥 Клонирование репозитория..."
if [ -d ".git" ]; then
    echo "Репозиторий уже существует, обновляем..."
    git pull
else
    git clone https://github.com/Dmitry140340/NinjaEssayAI.git .
fi

# Создание виртуального окружения
echo "🐍 Создание виртуального окружения..."
python3 -m venv venv

# Активация и установка зависимостей
echo "📦 Установка зависимостей..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Создание .env файла
echo "⚙️  Создание .env файла..."
cat > .env << 'EOF'
TELEGRAM_BOT_TOKEN=7860525094:AAETNSM92hnralH0x4QwhnzK4TvLbBELiSQ
DEEPSEEK_API_KEY=sk-2fcca2e6cf50493ba7d67eb50e73516f
DEEPSEEK_BASE_URL=https://api.deepseek.com
YOOKASSA_SHOP_ID=467003
YOOKASSA_SECRET_KEY=live_MzkzYWM5ZmYtZDMzOS00OGY2LTk1Y2EtMjMzYzIyMGE3YmNi
COZE_API_TOKEN=pat_FDqEt0RaRP5NoXKoJdJJIHTmpnRgSHhVTtQ9K4ruar6ybxxZSh3S3HXTXBLaHMO3
COZE_WORKFLOW_ID=7558218366650875916
COZE_SPACE_ID=7428945022634557446
COZE_API_URL=https://api.coze.com/v1/workflow/run
TESTING_MODE=False
EOF

echo "✅ .env файл создан"

# Создание systemd сервиса
echo "⚙️  Создание systemd сервиса..."
cat > /etc/systemd/system/ninjaessayai-bot.service << 'EOF'
[Unit]
Description=NinjaEssayAI Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ninjaessayai_bot
ExecStart=/opt/ninjaessayai_bot/venv/bin/python bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузка systemd и запуск бота
echo "🔄 Перезагрузка systemd..."
systemctl daemon-reload
systemctl enable ninjaessayai-bot

echo "🚀 Запуск бота..."
systemctl start ninjaessayai-bot

# Ожидание запуска
sleep 3

# Проверка статуса
echo ""
echo "=============================="
echo "✅ Установка завершена!"
echo "=============================="
echo ""
echo "📊 Статус бота:"
systemctl status ninjaessayai-bot --no-pager -l

echo ""
echo "📝 Полезные команды:"
echo "  Логи:      journalctl -u ninjaessayai-bot -f"
echo "  Перезапуск: systemctl restart ninjaessayai-bot"
echo "  Остановка: systemctl stop ninjaessayai-bot"
echo "  Статус:    systemctl status ninjaessayai-bot"
echo ""
echo "🎉 Бот установлен и запущен!"
