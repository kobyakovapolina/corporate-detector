# 02_preprocessing.py - БЕЗ ВНЕШНИХ ЗАВИСИМОСТЕЙ
import pandas as pd
import re
import os
import warnings

warnings.filterwarnings('ignore')

os.makedirs('data/processed', exist_ok=True)

# Загрузка данных
df = pd.read_csv('data/raw/vacancies_raw.csv')
print(f"Загружено {len(df)} вакансий")


# ====================
# 1. ОЧИСТКА ТЕКСТА
# ====================
def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'[^а-яё\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


df['cleaned_description'] = df['description'].apply(clean_text)

print(f"\n🔍 Пример текста после очистки:")
print(df['cleaned_description'].iloc[0][:300])

# ====================
# 2. ПРОСТЫЕ ПРАВИЛА ДЛЯ ОПРЕДЕЛЕНИЯ КАНЦЕЛЯРИЗМОВ
# ====================
# Словарь канцеляризмов и "пустых" слов
bureaucracy_words = {
    'стрессоустойчивость', 'коммуникабельность', 'обучаемость', 'ответственность',
    'исполнительность', 'клиентоориентированность', 'пунктуальность', 'динамичный',
    'развивающийся', 'проактивный', 'гибкость', 'ориентация', 'результат',
    'ведение', 'переговоры', 'команда', 'самоорганизация', 'многозадачность',
    'дружный', 'коллектив', 'целеустремленный', 'амбициозный', 'списание',
    'учет', 'потери', 'алгоритм', 'методика', 'крупнейший', 'ритейлер',
    'возможности', 'роста', 'развития', 'продвижения', 'карьерный'
}

# Слова для определения частей речи (примитивный, но работает)
adjectives_suffixes = ['ый', 'ий', 'ой', 'ая', 'яя', 'ое', 'ее', 'ые', 'ие',
                       'ого', 'его', 'ому', 'ему', 'ым', 'им', 'ом', 'ем',
                       'ная', 'няя', 'нное', 'тичный', 'льный', 'ческий']

adverbs_suffixes = ['о', 'е', 'ски', 'цки', 'ому', 'ему']


def simple_pos_tag(word):
    """Простое определение части речи по окончанию"""
    if len(word) < 3:
        return 'unknown'

    # Проверяем на прилагательное
    for suffix in adjectives_suffixes:
        if word.endswith(suffix):
            return 'ADJ'

    # Проверяем на наречие
    for suffix in adverbs_suffixes:
        if word.endswith(suffix):
            return 'ADV'

    return 'NOUN'  # всё остальное считаем существительным


def process_simple(text: str) -> dict:
    """
    Простая обработка текста без лемматизации
    """
    if not text or len(text) < 10:
        return {'words': [], 'adjs': [], 'advs': [], 'nouns': []}

    words = text.split()

    adjs = []
    advs = []
    nouns = []

    for word in words:
        if len(word) < 3:
            continue

        pos = simple_pos_tag(word)

        if pos == 'ADJ':
            adjs.append(word)
        elif pos == 'ADV':
            advs.append(word)
        else:
            nouns.append(word)

    return {
        'words': words,
        'nouns': nouns,
        'adjs': adjs,
        'advs': advs
    }


# Тест на первой вакансии
print("\n🔍 ТЕСТ на первой вакансии:")
test_text = df['cleaned_description'].iloc[0][:500]
test_result = process_simple(test_text)
print(f"   Всего слов: {len(test_result['words'])}")
print(f"   Существительных: {len(test_result['nouns'])}")
print(f"   Прилагательных: {len(test_result['adjs'])}")
print(f"   Наречий: {len(test_result['advs'])}")
print(f"\n   Пример прилагательных: {test_result['adjs'][:10]}")

# ====================
# 3. ОБРАБОТКА ВСЕХ ВАКАНСИЙ
# ====================
print("\n Обработка всех вакансий...")
from tqdm import tqdm

tqdm.pandas()
df['linguistic'] = df['cleaned_description'].progress_apply(process_simple)

# Разворачиваем результаты
df['words'] = df['linguistic'].apply(lambda x: x['words'])
df['nouns'] = df['linguistic'].apply(lambda x: x['nouns'])
df['adjectives'] = df['linguistic'].apply(lambda x: x['adjs'])
df['adverbs'] = df['linguistic'].apply(lambda x: x['advs'])

# ====================
# 4. ПРОВЕРКА РЕЗУЛЬТАТОВ
# ====================
print("\n ПРОВЕРКА РЕЗУЛЬТАТОВ:")
total_words = df['words'].apply(len).sum()
total_adjs = df['adjectives'].apply(len).sum()
total_advs = df['adverbs'].apply(len).sum()

print(f"   Всего слов во всех вакансиях: {total_words}")
print(f"   Всего прилагательных: {total_adjs}")
print(f"   Всего наречий: {total_advs}")
print(f"   Среднее слов на вакансию: {total_words / len(df):.1f}")

# ====================
# 5. РАСЧЁТ МЕТРИК
# ====================
# Индекс "воды" (прилагательные + наречия)
df['water_index'] = df.apply(
    lambda row: (len(row['adjectives']) + len(row['adverbs'])) / max(len(row['words']), 1),
    axis=1
)


# Подсчёт канцеляризмов (простое вхождение в словарь)
def count_bureaucracy(words_list):
    if not isinstance(words_list, list):
        return 0
    return sum(1 for word in words_list if word in bureaucracy_words)


df['bureaucracy_count'] = df['words'].apply(count_bureaucracy)
df['bureaucracy_index'] = df.apply(
    lambda row: row['bureaucracy_count'] / max(len(row['words']), 1),
    axis=1
)

# ====================
# 6. ИТОГОВЫЙ ОТЧЁТ
# ====================
print("\n" + "=" * 60)
print(" ПРЕДОБРАБОТКА ЗАВЕРШЕНА!")
print("=" * 60)

print(f"\n ИНДЕКСЫ ПО КАТЕГОРИЯМ:")
for cat in df['category'].unique():
    cat_df = df[df['category'] == cat]
    water = cat_df['water_index'].mean()
    bur = cat_df['bureaucracy_index'].mean()
    print(f"\n{cat.upper()}:")
    print(f"Индекс воды: {water:.4f}")
    print(f"Индекс канцеляризмов: {bur:.4f}")

# Топ прилагательных по категориям
print("\n" + "=" * 60)
print("ТОП-10 ПРИЛАГАТЕЛЬНЫХ ПО КАТЕГОРИЯМ:")
print("=" * 60)

from collections import Counter

for cat in df['category'].unique():
    cat_df = df[df['category'] == cat]
    all_adjs = []
    for adjs in cat_df['adjectives']:
        if isinstance(adjs, list):
            all_adjs.extend(adjs)

    top_adjs = Counter(all_adjs).most_common(10)
    print(f"\n{cat.upper()}:")
    for word, count in top_adjs:
        print(f"   {word}: {count}")

# Сохраняем
df.to_csv('data/processed/vacancies_processed.csv', index=False)
print(f"\n Сохранено: data/processed/vacancies_processed.csv")