import json
import os
import sys
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from random import randint
from time import sleep as pause


def get_urls_from_page(driver):
    """ Collects all product links on the current page. """
    soup = BeautifulSoup(driver.page_source, 'lxml')
    elements = soup.find_all('a', class_="catalog-product__name ui-link ui-link_black")
    return list(map(
        lambda element: 'https://www.dns-shop.ru' + element.get("href"),
        elements
    ))


def get_all_category_page_urls(driver, url_to_parse):
    """ Get category URL and parse links from it. """
    page = 1
    urls = []

    while True:
        url = url_to_parse.format(page=page)
        driver.get(url)
        pause(randint(2, 4))

        soup = BeautifulSoup(driver.page_source, 'lxml')

        # Get links from current page
        page_urls = get_urls_from_page(driver)
        with open('urls.txt', 'a') as file:
            for link in page_urls:
                file.write(link + "\n")
        urls += page_urls

        # Check for "Next page" button
        next_button = soup.find('a', class_="pagination-widget__page-link pagination-widget__page-link_next")
        if not next_button or 'disabled' in next_button.get('class', []):
            break

        page += 1

    print(f'Total {len(urls)} links collected from category.')
    return urls


def get_links_from_json(file_path="categories.json"):
    """Extracts links from categories.json."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} not found. Make sure the JSON file exists.")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Adjust the key depending on your `categories.json` structure
    links = [f"https://www.dns-shop.ru{item['url']}" for item in data if "url" in item]
    return links


def generate_urls_from_json(json_data):
    urls_to_parse = []

    def process_item(item):
        # Если у элемента нет childs или childs - пустой список
        if not item.get('childs'):
            base_url = 'https://www.dns-shop.ru'
            full_url = base_url + item['url'] + '?p={page}'
            urls_to_parse.append(full_url)

    def process_childs(data):
        # Если data - список, обрабатываем каждый элемент
        if isinstance(data, list):
            for item in data:
                # Сначала обрабатываем текущий элемент
                process_item(item)

                # Затем рекурсивно обрабатываем его вложенные подкатегории
                if item.get('childs'):
                    process_childs(item['childs'])
        # Если data - словарь, обрабатываем его как элемент
        elif isinstance(data, dict):
            process_item(data)
            if data.get('childs'):
                process_childs(data['childs'])

    # Начинаем обработку с корня JSON
    process_childs(json_data)

    return urls_to_parse

def main():
    driver = uc.Chrome()

    # Parse the JSON data from the provided document
    with open('categories.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Generate URLs
    urls_to_parse = generate_urls_from_json(data)

    # Print the generated URLs
    print("URLs to parse:")
    for url in urls_to_parse:
        print(url)

    # Example of how you might use these URLs in your scraping script
    all_product_urls = []
    for index, url in enumerate(urls_to_parse):
        print(f'Getting all links from category {index + 1}:')
        parsed_url = get_all_category_page_urls(driver, url)
        all_product_urls.extend(parsed_url)

    print("Writing all links to urls.txt:")
    # with open('urls.txt', 'w') as file:
    #     for link in all_product_urls:
    #         file.write(link + "\n")

    driver.quit()
    print('Link parsing complete!')


if __name__ == '__main__':
    main()