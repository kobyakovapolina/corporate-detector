# 01_scraping.py - ПАРСИНГ С РЕАЛЬНЫМИ ОПИСАНИЯМИ
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from tqdm import tqdm

# Создаем папки
os.makedirs('data/raw', exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
}


def parse_vacancies(query, pages=5):
    """
    Парсинг вакансий с hh.ru
    query: поисковый запрос
    pages: количество страниц
    """
    vacancies = []
    base_url = 'https://hh.ru/search/vacancy'

    for page in tqdm(range(pages), desc=f"Парсинг '{query}'"):
        try:
            params = {
                'text': query,
                'area': 113,
                'page': page
            }

            time.sleep(1)  # Задержка между страницами

            response = requests.get(base_url, params=params, headers=HEADERS, timeout=15)

            if response.status_code != 200:
                print(f"⚠️ Ошибка {response.status_code} на странице {page}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')

            # Ищем карточки вакансий
            vacancy_cards = soup.find_all('div', {'data-qa': 'vacancy-serp__vacancy'})

            if not vacancy_cards:
                vacancy_cards = soup.find_all('div', class_='vacancy-card--z_UXteNo7bRGzxWVcL7y')

            for card in vacancy_cards:
                try:
                    # Название вакансии
                    title_elem = card.find('a', {'data-qa': 'serp-item__title'})
                    title = title_elem.get_text(strip=True) if title_elem else 'Не указано'

                    # Ссылка на вакансию
                    link = title_elem['href'] if title_elem else ''

                    # Зарплата
                    salary_elem = card.find('span', {'data-qa': 'vacancy-serp__vacancy-compensation'})
                    salary = salary_elem.get_text(strip=True) if salary_elem else None

                    # Компания
                    company_elem = card.find('a', {'data-qa': 'vacancy-serp__vacancy-employer'})
                    company = company_elem.get_text(strip=True) if company_elem else 'Не указана'

                    # Город
                    city_elem = card.find('span', {'data-qa': 'vacancy-serp__vacancy-address'})
                    city = city_elem.get_text(strip=True) if city_elem else 'Не указан'

                    vacancies.append({
                        'title': title,
                        'link': link,
                        'salary': salary,
                        'company': company,
                        'city': city,
                        'category': query
                    })

                except Exception as e:
                    print(f"Ошибка при парсинге карточки: {e}")
                    continue

        except Exception as e:
            print(f"Ошибка на странице {page}: {e}")
            continue

    return vacancies


def get_descriptions(vacancies_df):
    """
    Получает полное описание для каждой вакансии из div class="vacancy-description"
    """
    descriptions = []

    for idx, row in tqdm(vacancies_df.iterrows(), total=len(vacancies_df), desc="Загрузка описаний"):
        link = row['link']
        description = ''

        if link and isinstance(link, str) and link.startswith('http'):
            try:
                time.sleep(0.5)  # Задержка между запросами
                response = requests.get(link, headers=HEADERS, timeout=15)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Ищем div с классом vacancy-description (как на вашем скриншоте)
                    desc_div = soup.find('div', class_='vacancy-description')

                    # Если не нашли, пробуем другие варианты
                    if not desc_div:
                        desc_div = soup.find('div', {'data-qa': 'vacancy-description'})

                    if desc_div:
                        # Получаем текст, удаляем лишние пробелы
                        description = desc_div.get_text(strip=True)

            except Exception as e:
                print(f"Ошибка при загрузке {link[:50]}: {e}")

        descriptions.append(description)

    vacancies_df['description'] = descriptions
    return vacancies_df


def main():
    print("\n" + "=" * 60)
    print(" ДЕТЕКТОР КОРПОРАТИВНЫХ КАНЦЕЛЯРИЗМОВ")
    print("ШАГ 1: ПАРСИНГ ВАКАНСИЙ")
    print("=" * 60)

    # Парсим IT-вакансии
    print("\n Парсинг IT-вакансий...")
    it_vacancies = parse_vacancies("аналитик данных", pages=3)

    # Парсим Sales-вакансии
    print("\n Парсинг вакансий в продажах...")
    sales_vacancies = parse_vacancies("менеджер по продажам", pages=3)

    # Объединяем
    all_vacancies = it_vacancies + sales_vacancies

    if not all_vacancies:
        print("\n Не удалось собрать вакансии!")
        return False

    df = pd.DataFrame(all_vacancies)

    # Сохраняем без описаний
    df.to_csv('data/raw/vacancies_raw_no_desc.csv', index=False)

    # Получаем описания
    print("\n Загрузка детальных описаний вакансий...")
    print("   (используем div class='vacancy-description')")
    df_with_desc = get_descriptions(df)

    # Сохраняем с описаниями
    df_with_desc.to_csv('data/raw/vacancies_raw.csv', index=False)

    # Статистика
    desc_count = df_with_desc['description'].apply(lambda x: len(x) > 100).sum()

    print(f"\n Результаты парсинга:")
    print(f"   Всего вакансий: {len(df_with_desc)}")
    print(f"   IT: {len(it_vacancies)}")
    print(f"   Sales: {len(sales_vacancies)}")
    print(f"   Загружено описаний: {desc_count}")

    # Показываем пример описания
    first_desc = df_with_desc[df_with_desc['description'].str.len() > 100]['description'].iloc[
        0] if desc_count > 0 else None
    if first_desc:
        print(f"\n Пример описания вакансии:")
        print(f"   {first_desc[:300]}...")

    print("\n data/raw/vacancies_raw.csv - сохранен")
    return True


if __name__ == "__main__":
    main()