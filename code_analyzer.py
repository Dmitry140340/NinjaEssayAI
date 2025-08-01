"""
Анализ и валидация кода бота NinjaEssayAI
"""

import ast
import os
import re
from typing import List, Dict, Any


class CodeAnalyzer:
    """Анализатор кода для проверки качества и потенциальных проблем"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.issues = []
        self.warnings = []
        self.suggestions = []
        
    def analyze(self) -> Dict[str, Any]:
        """Выполняет полный анализ кода"""
        print(f"🔍 Анализируем файл: {self.file_path}")
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Парсим AST
            try:
                tree = ast.parse(content)
                self._analyze_ast(tree)
            except SyntaxError as e:
                self.issues.append(f"Синтаксическая ошибка: {e}")
                
            # Анализируем текстовое содержимое
            self._analyze_text(content)
            
            return self._generate_report()
            
        except FileNotFoundError:
            self.issues.append(f"Файл не найден: {self.file_path}")
            return self._generate_report()
        except Exception as e:
            self.issues.append(f"Ошибка при анализе: {e}")
            return self._generate_report()
    
    def _analyze_ast(self, tree: ast.AST):
        """Анализирует AST дерево"""
        
        # Проверяем функции
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        async_functions = [f for f in functions if f.name.startswith('async') or 
                          any(isinstance(d, ast.AsyncFunctionDef) for d in ast.walk(tree))]
        
        # Проверяем длину функций
        for func in functions:
            lines = func.end_lineno - func.lineno if hasattr(func, 'end_lineno') else 0
            if lines > 50:
                self.warnings.append(f"Функция '{func.name}' слишком длинная ({lines} строк)")
        
        # Проверяем обработку исключений
        try_blocks = [node for node in ast.walk(tree) if isinstance(node, ast.Try)]
        if len(try_blocks) < 5:
            self.suggestions.append("Рекомендуется добавить больше обработки исключений")
        
        # Проверяем импорты
        imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        if len(imports) > 15:
            self.suggestions.append("Много импортов - рассмотрите рефакторинг")
    
    def _analyze_text(self, content: str):
        """Анализирует текстовое содержимое"""
        
        lines = content.split('\n')
        
        # Проверяем длину строк
        long_lines = [(i+1, line) for i, line in enumerate(lines) if len(line) > 120]
        if long_lines:
            self.warnings.append(f"Найдено {len(long_lines)} длинных строк (>120 символов)")
        
        # Проверяем TODOs и FIXMEs
        todos = [(i+1, line) for i, line in enumerate(lines) 
                if 'TODO' in line.upper() or 'FIXME' in line.upper()]
        if todos:
            self.suggestions.append(f"Найдено {len(todos)} TODO/FIXME комментариев")
        
        # Проверяем хардкод значения
        hardcoded_patterns = [
            r'YOOKASSA_SHOP_ID.*"1048732"',
            r'YOOKASSA_SECRET_KEY.*"live_.*"',
        ]
        
        for pattern in hardcoded_patterns:
            if re.search(pattern, content):
                self.warnings.append(f"Найдены хардкод значения: {pattern}")
        
        # Проверяем логирование
        logging_calls = len(re.findall(r'logging\.(info|error|warning|debug)', content))
        if logging_calls < 10:
            self.suggestions.append("Рекомендуется добавить больше логирования")
        
        # Проверяем async/await usage
        async_funcs = len(re.findall(r'async def', content))
        await_calls = len(re.findall(r'await ', content))
        
        if async_funcs > 0 and await_calls < async_funcs * 2:
            self.warnings.append("Возможно, не все async функции используют await корректно")
    
    def _generate_report(self) -> Dict[str, Any]:
        """Генерирует отчет об анализе"""
        return {
            'file': self.file_path,
            'issues': self.issues,
            'warnings': self.warnings,
            'suggestions': self.suggestions,
            'total_problems': len(self.issues) + len(self.warnings),
            'status': 'ERROR' if self.issues else 'WARNING' if self.warnings else 'OK'
        }


def check_security_issues(file_path: str) -> List[str]:
    """Проверяет потенциальные проблемы безопасности"""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Проверяем секретные ключи в коде
        if 'live_' in content:
            issues.append("⚠️ Найден продакшн ключ в коде - используйте переменные окружения")
        
        # Проверяем SQL injection возможности
        if 'query' in content.lower() and '%' in content:
            issues.append("⚠️ Возможная SQL injection уязвимость")
        
        # Проверяем небезопасное использование eval/exec
        if 'eval(' in content or 'exec(' in content:
            issues.append("🔴 Небезопасное использование eval/exec")
        
        # Проверяем открытие файлов без контроля пути
        if 'open(' in content and '..' in content:
            issues.append("⚠️ Возможная path traversal уязвимость")
            
    except Exception as e:
        issues.append(f"Ошибка при проверке безопасности: {e}")
    
    return issues


def check_performance_issues(file_path: str) -> List[str]:
    """Проверяет потенциальные проблемы производительности"""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем синхронные операции в async функциях
        async_funcs = re.findall(r'async def.*?(?=async def|\Z)', content, re.DOTALL)
        for func in async_funcs:
            if 'sleep(' in func and 'await asyncio.sleep' not in func:
                issues.append("⚠️ Использование time.sleep в async функции")
            
            if 'requests.' in func:
                issues.append("⚠️ Синхронные HTTP запросы в async функции")
        
        # Проверяем множественные API вызовы без батчинга
        api_calls = len(re.findall(r'client\.chat\.completions', content))
        if api_calls > 3:
            issues.append("ℹ️ Много API вызовов - рассмотрите батчинг")
        
        # Проверяем файловые операции без async
        if 'open(' in content and 'aiofiles' not in content:
            issues.append("ℹ️ Рассмотрите использование aiofiles для async IO")
            
    except Exception as e:
        issues.append(f"Ошибка при проверке производительности: {e}")
    
    return issues


def run_full_analysis(file_path: str = "bot.py"):
    """Запускает полный анализ кода"""
    print("🔍 Полный анализ кода бота NinjaEssayAI")
    print("=" * 50)
    
    # Основной анализ
    analyzer = CodeAnalyzer(file_path)
    report = analyzer.analyze()
    
    print(f"\n📊 Статус файла: {report['status']}")
    print(f"📈 Всего проблем: {report['total_problems']}")
    
    if report['issues']:
        print("\n🔴 Критические проблемы:")
        for issue in report['issues']:
            print(f"  • {issue}")
    
    if report['warnings']:
        print("\n⚠️ Предупреждения:")
        for warning in report['warnings']:
            print(f"  • {warning}")
    
    if report['suggestions']:
        print("\n💡 Рекомендации:")
        for suggestion in report['suggestions']:
            print(f"  • {suggestion}")
    
    # Проверка безопасности
    print("\n🔒 Анализ безопасности:")
    security_issues = check_security_issues(file_path)
    if security_issues:
        for issue in security_issues:
            print(f"  {issue}")
    else:
        print("  ✅ Серьезные проблемы безопасности не найдены")
    
    # Проверка производительности
    print("\n⚡ Анализ производительности:")
    performance_issues = check_performance_issues(file_path)
    if performance_issues:
        for issue in performance_issues:
            print(f"  {issue}")
    else:
        print("  ✅ Серьезные проблемы производительности не найдены")
    
    # Общая оценка
    print("\n" + "=" * 50)
    total_all_issues = (len(report['issues']) + len(report['warnings']) + 
                       len(security_issues) + len(performance_issues))
    
    if total_all_issues == 0:
        print("🎉 Код выглядит хорошо!")
        grade = "A"
    elif total_all_issues <= 5:
        print("👍 Код в целом хорошего качества")
        grade = "B"
    elif total_all_issues <= 10:
        print("⚠️ Код требует некоторых улучшений")
        grade = "C"
    else:
        print("🔧 Код требует значительных улучшений")
        grade = "D"
    
    print(f"📝 Итоговая оценка: {grade}")
    
    return report


if __name__ == "__main__":
    run_full_analysis()
