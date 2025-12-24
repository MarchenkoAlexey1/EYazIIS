import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse
import time
import hashlib

DATA_DIR = 'data'
CRAWLED_FILES_DIR = os.path.join(DATA_DIR, 'crawled')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

content_hashes = set()


def extract_meaningful_content_and_links(soup):
    main_content = soup.find(id='mw-content-text')
    links = []
    text = ""

    if main_content:
        for tag in main_content.find_all(['table', 'div'],
                                         class_=['infobox', 'toc', 'thumb', 'gallery', 'reflist', 'navbox']):
            tag.decompose()
        for tag in main_content.find_all('span', class_='mw-editsection'):
            tag.decompose()

        text = main_content.get_text(separator=' ', strip=True)

        for link in main_content.find_all('a', href=True):
            href = link['href']
            if href.startswith('/wiki/') and ':' not in href:
                links.append(href)

        return text, links

    body = soup.body
    if body:
        text = body.get_text(separator=' ', strip=True)
        links = [link['href'] for link in body.find_all('a', href=True)]

    return text, links


def crawl(start_urls, max_pages=20):
    os.makedirs(CRAWLED_FILES_DIR, exist_ok=True)

    queue = list(start_urls)
    visited = set(start_urls)
    crawled_count = 0

    print(f"Начинаем тематический обход. Максимум страниц: {max_pages}")

    while queue and crawled_count < max_pages:
        url = queue.pop(0)

        parsed_url = urlparse(url)
        path_segments = parsed_url.path.split('/')
        if (any(':' in segment for segment in
                path_segments) and not url in start_urls) or 'action=' in parsed_url.query:
            print(f"\nПропускаем служебный URL: {url}")
            continue

        print(f"\n[{crawled_count + 1}/{max_pages}] Попытка скачивания: {url}")

        try:
            response = requests.get(url, headers=HEADERS, timeout=10)

            if response.status_code != 200 or 'text/html' not in response.headers.get('Content-Type', ''):
                continue

            soup = BeautifulSoup(response.text, 'html.parser')

            text, internal_links = extract_meaningful_content_and_links(soup)

            if len(text) < 1000:
                print(f"-> Пропускаем URL: слишком мало полезного текста ({len(text)} символов).")
                continue

            content_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            if content_hash in content_hashes:
                print("-> Пропускаем URL: контент является дубликатом.")
                continue
            content_hashes.add(content_hash)

            filename = f"doc_{crawled_count}.txt"
            filepath = os.path.join(CRAWLED_FILES_DIR, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(url + '\n')
                f.write(text)

            print(f"-> УСПЕХ! Страница сохранена в {filepath}")
            crawled_count += 1

            for link_path in internal_links:
                abs_link = urljoin(url, link_path)
                if abs_link not in visited:
                    visited.add(abs_link)
                    queue.append(abs_link)

            time.sleep(1)

        except requests.RequestException as e:
            print(f"-> ОШИБКА! Не удалось скачать {url}: {e}")


if __name__ == '__main__':
    initial_urls = ['https://en.wikipedia.org/wiki/Information_retrieval']
    crawl(initial_urls, max_pages=20)
    print("\nОбход завершен.")