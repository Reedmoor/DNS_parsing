import pickle
import sys

from tqdm import tqdm
from random import randint
from datetime import datetime
from time import sleep as pause
from bs4 import BeautifulSoup
import undetected_chromedriver as uc


def parse_characteristics_page(driver, url):
    """ Парсит страницу товара по ссылке."""
    driver.get(url)
    pause(randint(7, 11))
    soup = BeautifulSoup(driver.page_source, 'lxml')
    print(soup.prettify())

    # TODO:заменить классы
    name = soup.find('div', class_="product-card-description__title")
    price = soup.find('div', class_="product-buy__price")
    desc = soup.find('div', class_="product-card-description-text")
    avail = soup.find('a', class_="order-avail-wrap__link ui-link ui-link_blue")
    charcs = soup.find_all('div', class_="product-characteristics__spec-title")
    cvalue = soup.find_all('div', class_="product-characteristics__spec-value")
    main_picture = soup.find('img', class_="product-images-slider__main-img")
    pictures_soup = soup.find_all('img', class_="product-images-slider__img loaded tns-complete")

    pictures_list = []
    for i in pictures_soup:
        _ = pictures_list.append(i.get('data-src'))
        if _ is not None:
            pictures_list.append(_)

    span_tags = soup.find_all('span')
    for i in span_tags:
        if bool(str(i).find('data-go-back-catalog') != -1):
            category = i

    tech_spec = {}
    for f1, f2 in zip(charcs, cvalue):
        tech_spec[f1.text.rstrip().lstrip()] = f2.text.rstrip().lstrip()

    item = {}

    item["Категория"] = category.text.lstrip(': ')
    item["Наименование"] = name.text[15:]
    item["Цена"] = int(price.text.replace(' ', '')[:-1])
    item["Доступность"] = avail.text if avail is not None else 'Товара нет в наличии'
    item["Ссылка на товар"] = url
    item["Описание"] = desc.text
    item["Главное изображение"] = main_picture.get('src') if main_picture is not None else 'У товара нет картинок'
    item["Лист с картинками"] = pictures_list
    item["Характеристики"] = list(tech_spec.items())

    # for i, j in notebook.items():
    #     print(i, j)
    return item


def get_all_category_page_urls(driver, url_to_parse):
    """ Получаем URL категории и парсим ссылки с неё."""
    page = 1
    urls = []

    while True:
        url = url_to_parse.format(page=page)
        driver.get(url)
        pause(randint(6, 9))

        soup = BeautifulSoup(driver.page_source, 'lxml')

        # Получение ссылок с текущей страницы
        page_urls = get_urls_from_page(driver)
        urls += page_urls

        # Проверка наличия кнопки "Следующая страница"
        next_button = soup.find('a', class_="pagination-widget__page-link pagination-widget__page-link_next")
        if not next_button or 'disabled' in next_button.get('class', []):
            break

        page += 1

    print(f'Всего собрано {len(urls)} ссылок из категории.')
    return urls

def get_urls_from_page(driver):
    """ Собирает все ссылки на текущей странице. """
    soup = BeautifulSoup(driver.page_source, 'lxml')
    elements = soup.find_all('a', class_="catalog-product__name ui-link ui-link_black")
    return list(map(
        lambda element: 'https://www.dns-shop.ru' + element.get("href") + 'characteristics/',
        elements
    ))

def main():

    driver = uc.Chrome()
    urls_to_parse = [
        'https://www.dns-shop.ru/search/?q=%D0%BF%D1%8B%D0%BB%D0%B5%D1%81%D0%BE%D1%81+%D1%80%D0%BE%D0%B1%D0%BE%D1%82+dreame&category=17a8face16404e77&p={page}',
    ]

    urls = []
    for index, url in enumerate(urls_to_parse):
        print(f'Получение списка всех ссылок из {index+1} категории:')
        parsed_url = get_all_category_page_urls(driver, url)
        urls.append(parsed_url)

    print("Запись всех ссылок в файл url.txt:")
    with open('urls.txt', 'w') as file:
        for url in urls:
            for link in url:
                file.write(link + "\n")

    with open('urls.txt', 'r') as file:
        urls = list(map(lambda line: line.strip(), file.readlines()))
        print(urls)
        info_dump = []
        for url in tqdm(urls, ncols=70, unit='товаров',
                        colour='blue', file=sys.stdout):
            info_dump.append(parse_characteristics_page(driver, url))


if __name__ == '__main__':
    main()
    print('=' * 20)
    print('Все готово!')