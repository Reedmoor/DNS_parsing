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
        urls += page_urls

        # Check for "Next page" button
        next_button = soup.find('a', class_="pagination-widget__page-link pagination-widget__page-link_next")
        if not next_button or 'disabled' in next_button.get('class', []):
            break

        page += 1

    print(f'Total {len(urls)} links collected from category.')
    return urls


def main():
    driver = uc.Chrome()

    # Define search URLs with pagination
    urls_to_parse = [
        'https://www.dns-shop.ru/search/?q=%D0%BF%D1%8B%D0%BB%D0%B5%D1%81%D0%BE%D1%81+%D1%80%D0%BE%D0%B1%D0%BE%D1%82+dreame&category=17a8face16404e77&p={page}'
    ]

    all_product_urls = []
    for index, url in enumerate(urls_to_parse):
        print(f'Getting all links from category {index + 1}:')
        parsed_url = get_all_category_page_urls(driver, url)
        all_product_urls.extend(parsed_url)

    print("Writing all links to urls.txt:")
    with open('urls.txt', 'w') as file:
        for link in all_product_urls:
            file.write(link + "\n")

    driver.quit()
    print('Link parsing complete!')


if __name__ == '__main__':
    main()