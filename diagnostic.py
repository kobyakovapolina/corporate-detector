# diagnostic.py - ДИАГНОСТИКА ПРОБЛЕМЫ
import pandas as pd

df = pd.read_csv('data/raw/vacancies_raw.csv')

print("=" * 60)
print("ДИАГНОСТИКА ДАННЫХ")
print("=" * 60)

print(f"\nВсего вакансий: {len(df)}")
print(f"Колонки: {list(df.columns)}")

# Проверяем колонку description
if 'description' in df.columns:
    sample = df['description'].iloc[0] if len(df) > 0 else "НЕТ ДАННЫХ"
    print(f"\nПример description (первые 500 символов):")
    print(sample[:500] if isinstance(sample, str) else f"НЕ СТРОКА: {type(sample)}")

    # Статистика по заполненности
    desc_count = df['description'].apply(lambda x: isinstance(x, str) and len(x) > 50).sum()
    print(f"\nВакансий с описанием > 50 символов: {desc_count} / {len(df)}")
else:
    print("\n❌ Колонка 'description' отсутствует!")
    print("Доступные колонки:", list(df.columns))

# Проверяем категории
print(f"\nКатегории: {df['category'].unique()}")