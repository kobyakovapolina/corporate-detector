# 03_analysis.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from wordcloud import WordCloud
import os

# Создаем папку для графиков
os.makedirs('images', exist_ok=True)

# Загрузка
df = pd.read_csv('data/processed/vacancies_processed.csv')
print(f"Загружено {len(df)} вакансий")
print(f"Категории: {df['category'].unique()}")

# Преобразуем строковые колонки обратно в списки
import ast


def safe_eval(x):
    if isinstance(x, str):
        try:
            return ast.literal_eval(x)
        except:
            return []
    return x if isinstance(x, list) else []


df['words'] = df['words'].apply(safe_eval)
df['nouns'] = df['nouns'].apply(safe_eval)
df['adjectives'] = df['adjectives'].apply(safe_eval)
df['adverbs'] = df['adverbs'].apply(safe_eval)


# ====================
# 1. Top-N существительных
# ====================
def get_top_words(df, category, word_type='nouns', n=15):
    words_list = []
    for words in df[df['category'] == category][word_type].dropna():
        if isinstance(words, list):
            words_list.extend(words)
    return Counter(words_list).most_common(n)


print("\n" + "=" * 60)
print("ТОП-15 СУЩЕСТВИТЕЛЬНЫХ В IT:")
print("=" * 60)
for word, count in get_top_words(df, 'аналитик данных', 'nouns'):
    if len(word) > 3:  # фильтруем короткие слова
        print(f"   {word}: {count}")

print("\n" + "=" * 60)
print("ТОП-15 СУЩЕСТВИТЕЛЬНЫХ В Sales:")
print("=" * 60)
for word, count in get_top_words(df, 'менеджер по продажам', 'nouns'):
    if len(word) > 3:
        print(f"   {word}: {count}")

# ====================
# 2. График сравнения индексов
# ====================
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Индекс воды
sns.boxplot(data=df, x='category', y='water_index', ax=axes[0], color='skyblue')
axes[0].set_title('Индекс "воды" по категориям', fontsize=12)
axes[0].set_ylabel('Прилагательные + наречия / всего слов', fontsize=10)
axes[0].set_xlabel('Категория вакансий', fontsize=10)
axes[0].set_ylim(0, 0.8)

# Индекс канцеляризмов
sns.boxplot(data=df, x='category', y='bureaucracy_index', ax=axes[1], color='salmon')
axes[1].set_title('Индекс канцеляризмов по категориям', fontsize=12)
axes[1].set_ylabel('Канцеляризмы / всего слов', fontsize=10)
axes[1].set_xlabel('Категория вакансий', fontsize=10)

plt.tight_layout()
plt.savefig('images/metrics_comparison.png', dpi=150)
plt.show()
print("\nГрафик сохранен: images/metrics_comparison.png")

# ====================
# 3. Гистограмма распределения
# ====================
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Распределение индекса воды
for cat in df['category'].unique():
    cat_df = df[df['category'] == cat]
    axes[0].hist(cat_df['water_index'], alpha=0.5, label=cat, bins=20)
axes[0].set_title('Распределение индекса "воды"', fontsize=12)
axes[0].set_xlabel('Индекс воды')
axes[0].set_ylabel('Количество вакансий')
axes[0].legend()

# Распределение индекса канцеляризмов
for cat in df['category'].unique():
    cat_df = df[df['category'] == cat]
    axes[1].hist(cat_df['bureaucracy_index'], alpha=0.5, label=cat, bins=20)
axes[1].set_title('Распределение индекса канцеляризмов', fontsize=12)
axes[1].set_xlabel('Индекс канцеляризмов')
axes[1].set_ylabel('Количество вакансий')
axes[1].legend()

plt.tight_layout()
plt.savefig('images/distribution.png', dpi=150)
plt.show()
print("📊 График сохранен: images/distribution.png")

# ====================
# 4. WordCloud самых частых прилагательных
# ====================
# Собираем все прилагательные из Sales-вакансий для облака слов
all_adjs_sales = []
for adjs in df[df['category'] == 'менеджер по продажам']['adjectives'].dropna():
    if isinstance(adjs, list):
        all_adjs_sales.extend(adjs)

# Убираем слишком короткие и служебные слова
stop_words = {'его', 'другой', 'какой', 'большой', 'откликом', 'какая',
              'дебиторской', 'свой', 'весь', 'такой', 'новый', 'старый',
              'ее', 'сам', 'этот', 'тот', 'наш', 'ваш'}

adj_freq = Counter([w for w in all_adjs_sales if len(w) > 4 and w not in stop_words])

if adj_freq:
    wordcloud = WordCloud(width=800, height=400, background_color='white',
                          colormap='Reds', max_words=30, font_path=None).generate_from_frequencies(adj_freq)

    plt.figure(figsize=(14, 7))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title('Топ прилагательных в вакансиях Sales (облако слов)', fontsize=16)
    plt.tight_layout()
    plt.savefig('images/top_bullshit.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("WordCloud сохранен: images/top_bullshit.png")
else:
    print("Недостаточно слов для создания WordCloud")

# ====================
# 5. Сравнительная таблица
# ====================
print("\n" + "=" * 60)
print("СРАВНИТЕЛЬНАЯ ТАБЛИЦА")
print("=" * 60)

stats = []
for cat in df['category'].unique():
    cat_df = df[df['category'] == cat]
    stats.append({
        'Категория': cat,
        'Индекс воды (средний)': f"{cat_df['water_index'].mean():.4f}",
        'Индекс воды (медиана)': f"{cat_df['water_index'].median():.4f}",
        'Индекс канцеляризмов': f"{cat_df['bureaucracy_index'].mean():.4f}",
        'Всего слов': cat_df['words'].apply(len).sum(),
        'Прилагательных': cat_df['adjectives'].apply(len).sum()
    })

stats_df = pd.DataFrame(stats)
print(stats_df.to_string(index=False))

# ====================
# 6. Финальный вывод
# ====================
print("\n" + "=" * 60)
print("ВЫВОДЫ ПО ПРОЕКТУ")
print("=" * 60)

it_water = df[df['category'] == 'аналитик данных']['water_index'].mean()
sales_water = df[df['category'] == 'менеджер по продажам']['water_index'].mean()
it_bur = df[df['category'] == 'аналитик данных']['bureaucracy_index'].mean()
sales_bur = df[df['category'] == 'менеджер по продажам']['bureaucracy_index'].mean()

print(f"\n1. Анализ \"воды\" в текстах:")
print(f"IT-вакансии: {it_water:.2%} прилагательных и наречий")
print(f"Sales-вакансии: {sales_water:.2%} прилагательных и наречий")
if sales_water > it_water:
    print(f"Вывод: В Sales-вакансиях на {(sales_water - it_water) * 100:.1f}% больше описательных слов (\"воды\")")

print(f"\n2. Анализ канцеляризмов:")
print(f"IT-вакансии: {it_bur:.2%} слов-канцеляризмов")
print(f"Sales-вакансии: {sales_bur:.2%} слов-канцеляризмов")
if sales_bur > it_bur:
    print(f"Вывод: В Sales-вакансиях канцеляризмов почти в {sales_bur / it_bur:.1f} раза больше")

print("\n Все графики сохранены в папку images/")
print("   - images/metrics_comparison.png")
print("   - images/distribution.png")
print("   - images/top_bullshit.png")