# main.py - Главный файл проекта
# Запускает весь пайплайн: парсинг → обработка → анализ

import subprocess
import sys
import os


def check_requirements():
    """Проверяет, установлены ли нужные библиотеки"""
    try:
        import pandas
        import requests
        import natasha
        print("Все библиотеки установлены")
        return True
    except ImportError as e:
        print(f"Ошибка: отсутствует библиотека {e}")
        print("Установите зависимости: pip install -r requirements.txt")
        return False


def run_script(script_name, step_number):
    """Запускает Python скрипт и обрабатывает ошибки"""
    print("\n" + "=" * 60)
    print(f"шаг {step_number}: {script_name}")
    print("=" * 60)

    try:
        # Запускаем скрипт
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=False,  # Показываем вывод в реальном времени
            text=True
        )

        if result.returncode == 0:
            print(f"{script_name} выполнен успешно")
            return True
        else:
            print(f"{script_name} завершился с ошибкой")
            return False

    except FileNotFoundError:
        print(f"Файл {script_name} не найден!")
        print(f"Убедитесь, что файл существует в папке проекта")
        return False
    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")
        return False


def main():
    """Главная функция"""
    print("\n" + "=" * 60)
    print("ДЕТЕКТОР КОРПОРАТИВНЫХ КАНЦЕЛЯРИЗМОВ")
    print("Анализ вакансий на предмет канцеляризмов")
    print("=" * 60)

    # Проверяем зависимости
    if not check_requirements():
        return

    print("\nЗапуск пайплайна обработки...")

    # Шаг 1: Парсинг
    if not run_script("01_scraping.py", 1):
        print("\nПайплайн остановлен на шаге 1")
        return

    # Шаг 2: Предобработка
    if not run_script("02_preprocessing.py", 2):
        print("\nПайплайн остановлен на шаге 2")
        return

    # Шаг 3: Анализ
    if not run_script("03_analysis.py", 3):
        print("\nПайплайн остановлен на шаге 3")
        return

    # Шаг 4: Визуализация (опционально)
    print("\n" + "=" * 60)
    print("ШАГ 4: Сохранение результатов")
    print("=" * 60)
    print("Все графики сохранены в папку images/")

    # Финальный отчет
    print("\n" + "=" * 60)
    print("pipeline завершен")
    print("=" * 60)
    print("\nРезультаты:")
    print("Данные: data/raw/ и data/processed/")
    print("Графики: images/")
    print("Лог: можно посмотреть выше")

    # Показываем, где найти графики
    if os.path.exists("images"):
        images = os.listdir("images")
        if images:
            print("\nСозданные графики:")
            for img in images:
                print(f"{img}")

    print("\nСовет: откройте папку images/ и посмотрите на графики")


if __name__ == "__main__":
    main()
