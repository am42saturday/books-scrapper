import json
import re
import time

import requests
import schedule
from bs4 import BeautifulSoup


BASE_URL = "http://books.toscrape.com"


def get_book_data(book_url: str) -> dict:
    """
    Считать данные о книге со страницы каталога books.toscrape.com и вернуть их в виде словаря.

    Функция извлекает:
      - title: название книги (str)
      - price: числовую цену (float) и currency: валюту (str, символ/код)
      - rating: целочисленный рейтинг от 1 до 5 (int) по классам вида "star-rating Three"
      - availability_count: количество доступных экземпляров (int | None)
      - availability_text: исходный текст наличия (str)
      - description: описание книги, если есть (str | None)
      - product_info: словарь с полями из таблицы "Product Information" (Dict)
      - url: исходный URL страницы (str)

    Параметры:
        book_url : str
            Полный URL страницы книги.

    Возвращает:
        Dict[str, Any]
            Словарь со структурированными данными (см. перечень выше)
    """

    # НАЧАЛО ВАШЕГО РЕШЕНИЯ
    session = requests.session()
    headers = {"User-Agent": "Mozilla/5.0 (compatible; book-scraper/1.0)"}
    response = session.get(book_url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    def text_or_none(node):
        return node.get_text(strip=True) if node else None

    def parse_price(raw):
        """Извлечь цену"""
        if not raw:
            return None, None, None
        # Пример: "£51.77" или "£ 51.77"
        m = re.search(r"(?P<cur>[^\d\s])\s*(?P<val>\d+(?:\.\d+)?)", raw)
        if not m:
            return None, None, raw
        val = float(m.group("val"))
        cur = m.group("cur")
        return val, cur, raw

    def parse_rating(star_node):
        """Извлечь рейтинг"""
        if not star_node:
            return None
        classes = star_node.get("class", [])
        rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
        for c in classes:
            if c in rating_map:
                return rating_map[c]
        return None

    def parse_availability(raw):
        """Вернуть доступное кол-во"""
        if not raw:
            return None, None
        m = re.search(r"(\d+)", raw)
        return (int(m.group(1)) if m else None, raw.strip())

    title = text_or_none(soup.select_one("div.product_main h1"))

    price_node = soup.select_one("div.product_main p.price_color")
    price_text = text_or_none(price_node)
    price_val, currency_symbol, price_raw = parse_price(price_text)

    rating_node = soup.select_one("p.star-rating")
    rating = parse_rating(rating_node)

    avail_node = soup.select_one("div.product_main p.instock.availability")
    avail_text = " ".join(avail_node.get_text().split()) if avail_node else None
    availability_count, availability_text = parse_availability(avail_text)

    description = None
    desc_anchor = soup.select_one("#product_description")
    if desc_anchor:
        p = desc_anchor.find_next("p")
        description = text_or_none(p)

    product_info = {}
    info_table = soup.select_one("table.table.table-striped")
    if info_table:
        for tr in info_table.select("tr"):
            th = tr.find("th")
            td = tr.find("td")
            if th and td:
                key = th.get_text(strip=True)
                val = td.get_text(strip=True)
                product_info[key] = val

    data = {
        "url": book_url,
        "title": title,
        "price": price_val,
        "currency": currency_symbol,
        "price_text": price_raw,
        "rating": rating,
        "availability_count": availability_count,
        "availability_text": availability_text,
        "description": description,
        "product_info": product_info
    }
    print(data)

    return data
    # КОНЕЦ ВАШЕГО РЕШЕНИЯ


def scrape_books(is_save: bool = False, pages_to_scrape: int = None):
    """
    Пройти по всем страницам books.toscrape.com и спарсить данные всех книг

    Параметры:
        is_save : bool, optional
            Сохранение результата в файл:
            если он будет равен True, то информация сохранится в ту же папку в файл books_data.txt;
            иначе шаг сохранения будет пропущен
        pages_to_scrape : int, optional
            Сколько страниц из каталога спарсить, по порядку

    Возвращает:
        list[dict]
            Список словарей с данными по всем найденным книгам.
    """

    # НАЧАЛО ВАШЕГО РЕШЕНИЯ
    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0 (compatible; book-scraper/1.0)"}

    all_books = []

    page_num = 1
    while True:
        page_url = f"{BASE_URL}/catalogue/page-{page_num}.html"
        resp = session.get(page_url, headers=headers)
        # страница кончилась
        if resp.status_code != 200:
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        book_cards = soup.select("article.product_pod h3 a")

        for a in book_cards:
            href = a.get("href")
            if not href:
                continue

            if href.startswith("../"):
                href = href.replace("../", "")
            book_url = f"{BASE_URL}/catalogue/{href}"

            book_data = get_book_data(book_url)
            all_books.append(book_data)

        if page_num == pages_to_scrape:
            break

        page_num += 1


    if is_save:
        with open("artifacts/books_data.txt", "w", encoding="utf-8") as f:
            for book in all_books:
                f.write(json.dumps(book, ensure_ascii=False) + "\n")

    return all_books
    # КОНЕЦ ВАШЕГО РЕШЕНИЯ


# НАЧАЛО ВАШЕГО РЕШЕНИЯ
def job():
    print("Запускаю сбор данных...")
    scrape_books(is_save=True)
    print("Данные сохранены в books_data.txt")


# каждый день в 19:00
schedule.every().day.at("19:00").do(job)
# schedule.every().day.at("19:42").do(job)  # to check

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(30)
# КОНЕЦ ВАШЕГО РЕШЕНИЯ
