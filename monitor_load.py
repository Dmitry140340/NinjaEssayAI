#!/usr/bin/env python3
"""
Мониторинг нагрузки для NinjaEssayAI бота
Поможет определить оптимальное значение семафора
"""
import asyncio
import sqlite3
from datetime import datetime, timedelta
import os

def check_semaphore_load():
    """Проверка текущей нагрузки и рекомендации"""
    print("🔍 Анализ нагрузки NinjaEssayAI бота...")
    print("=" * 50)
    
    # Проверяем файл бота
    if not os.path.exists('user_activity.db'):
        print("❌ База данных user_activity.db не найдена")
        return
    
    conn = sqlite3.connect('user_activity.db')
    cursor = conn.cursor()
    
    # Статистика за разные периоды
    periods = [
        ('час', 1),
        ('день', 24),
        ('неделю', 24 * 7)
    ]
    
    for period_name, hours in periods:
        time_ago = datetime.now() - timedelta(hours=hours)
        
        cursor.execute('''
            SELECT COUNT(*) FROM user_actions 
            WHERE timestamp > ? AND action LIKE '%generate%'
        ''', (time_ago,))
        
        generations = cursor.fetchone()[0]
        avg_per_hour = generations / hours if hours > 0 else 0
        
        print(f"📊 За {period_name}: {generations} генераций ({avg_per_hour:.1f}/час)")
    
    # Рекомендации по семафору
    print("\n🎯 Рекомендации по семафору:")
    
    cursor.execute('''
        SELECT COUNT(*) FROM user_actions 
        WHERE timestamp > ? AND action LIKE '%generate%'
    ''', (datetime.now() - timedelta(hours=1),))
    
    last_hour = cursor.fetchone()[0]
    
    if last_hour == 0:
        print("✅ Нагрузка: МИНИМАЛЬНАЯ - семафор 5")
    elif last_hour < 10:
        print("✅ Нагрузка: НИЗКАЯ - семафор 10 (текущий)")
    elif last_hour < 30:
        print("⚠️  Нагрузка: СРЕДНЯЯ - рекомендуется семафор 15")
    elif last_hour < 60:
        print("🔥 Нагрузка: ВЫСОКАЯ - рекомендуется семафор 20")
    else:
        print("🚨 Нагрузка: КРИТИЧЕСКАЯ - рекомендуется семафор 30+")
    
    # Пиковые часы
    print("\n⏰ Анализ пиковых часов:")
    cursor.execute('''
        SELECT 
            strftime('%H', timestamp) as hour,
            COUNT(*) as count
        FROM user_actions 
        WHERE timestamp > ? AND action LIKE '%generate%'
        GROUP BY hour
        ORDER BY count DESC
        LIMIT 5
    ''', (datetime.now() - timedelta(days=7),))
    
    peak_hours = cursor.fetchall()
    for hour, count in peak_hours:
        print(f"🕐 {hour}:00 - {count} генераций")
    
    conn.close()
    
    print("\n" + "=" * 50)
    print("💡 Совет: Запускайте этот скрипт регулярно для мониторинга!")

if __name__ == "__main__":
    check_semaphore_load()
