import sys
from pathlib import Path

# add project root to sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scraper import get_book_data, scrape_books

BOOK_URL = "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
CATALOG_PAGE_1 = "http://books.toscrape.com/catalogue/page-1.html"
CATALOG_PAGE_2 = "http://books.toscrape.com/catalogue/page-2.html"


def test_get_book_data_returns_required_keys():
    data = get_book_data(BOOK_URL)
    for key in [
        "url",
        "title",
        "price",
        "currency",
        "rating",
        "availability_text",
        "product_info",
    ]:
        assert key in data, f"{key} not in result"


def test_get_book_data_parses_title():
    data = get_book_data(BOOK_URL)
    assert data["title"] == "A Light in the Attic"


def test_scrape_books_first_page():
    books = scrape_books(pages_to_scrape=1)
    assert isinstance(books, list)
    assert len(books) >= 20  # there are 20 books per page
    first = books[0]
    assert "title" in first
    assert isinstance(first["product_info"], dict)
