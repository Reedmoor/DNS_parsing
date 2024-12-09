import sys
import json
import scrapy

from tqdm import tqdm
from random import randint
from time import sleep as pause
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
TEST_URL = "https://www.dns-shop.ru/product/a67afeaff7bbd9cb/robot-pylesos-dreame-x40-ultra-complete-belyj/"

def save_to_json(data, filename="items.json"):
    """Save data to JSON file."""
    try:
        # Создаем копию данных для сериализации
        serializable_data = []
        for item in data:
            serializable_item = {}
            for key, value in item.items():
                # Пропускаем несериализуемые объекты
                if not callable(value) and value is not None:
                    # Для списков проверяем вложенные элементы
                    if isinstance(value, list):
                        serializable_list = []
                        for subitem in value:
                            if not callable(subitem) and subitem is not None:
                                serializable_list.append(subitem)
                        serializable_item[key] = serializable_list
                    else:
                        serializable_item[key] = value
            serializable_data.append(serializable_item)

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(serializable_data, f, ensure_ascii=False, indent=4)
        print(f"Data successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving data to JSON: {e}")
        # Для отладки можно вывести более подробную информацию
        import traceback
        traceback.print_exc()

def clean_price(price_str):

    if not price_str:
        return None

# Remove non-digit characters
    cleaned_price = ''.join(char for char in price_str if char.isdigit())

    try:
        return int(cleaned_price)
    except ValueError:
        return None

def parse_breadcrumbs(driver):
    soup = BeautifulSoup(driver.page_source, 'lxml')

    # Find the breadcrumb list
    breadcrumb_list = soup.find('ol', class_='breadcrumb-list')

    # If no breadcrumb list found, return empty list
    if not breadcrumb_list:
        return []

    # Parse categories
    categories = []
    for item in breadcrumb_list.find_all('li', class_='breadcrumb-list__item'):
        # Skip the last item (current page)
        if 'breadcrumb_last' in item.get('class', []):
            continue

        # Find the link
        link = item.find('a', class_='ui-link')
        if link:
            categories.append({
                'url': f"https://www.dns-shop.ru{link.get('href', '')}",
                'name': link.find('span').text.strip()
            })

    if len(categories) > 2:
        categories = categories[1:-1]

    return categories


def parse_characteristics(driver):
    soup = BeautifulSoup(driver.page_source, 'lxml')
    characteristics = []

    # Поиск групп характеристик
    groups = soup.find_all('div', class_='product-characteristics__group')
    for group in groups:
        group_name = group.find('div', class_='product-characteristics__group-title').text.strip()
        items = group.find_all('li', class_='product-characteristics__spec')

        group_data = {"group": group_name, "characteristics": []}

        for item in items:
            title_element = item.find('div', class_='product-characteristics__spec-title-content')
            value_element = item.find('div', class_='product-characteristics__spec-value')

            if title_element and value_element:
                characteristic = {
                    "characteristics": title_element.text.strip(),
                    "value": value_element.text.strip()
                }
                group_data["characteristic"].append(characteristic)

        characteristics.append(group_data)

    return characteristics


def extract_tns_srcset(soup):
    # Find all elements with tns-item class
    tns_items = soup.find_all('div', class_='tns-item')

    # Extract data-srcset values, ordered by ID
    srcset_list = []
    for item in tns_items:
        if item.has_attr('data-srcset'):
            srcset_list.append(item['data-srcset'])

    return srcset_list
def parse_characteristics_page(driver, url):
    """Parse product page details."""
    driver.get(url)
    pause(randint(9, 11))

    soup = BeautifulSoup(driver.page_source, 'lxml')
    selector = scrapy.Selector(text=driver.page_source)

    def logo():
        json_ld_scripts = selector.xpath(
            "//script[@type='application/ld+json' and contains(text(), 'Product')]/text()").getall()
        brand_name = None
        for script_text in json_ld_scripts:
            try:
                json_data = json.loads(script_text)
                if 'brand' in json_data and isinstance(json_data['brand'], dict):
                    brand_name = json_data['brand'].get('name')
                    break
            except json.JSONDecodeError:
                continue
        return brand_name

    def safe_text(soup, tag, class_=None, attribute=None):
        """Safely extract text or attribute from an element."""
        element = soup.find(tag, class_=class_)
        return element.get(attribute).strip() if element and attribute else element.text.strip() if element else None

    def safe_list(soup, tag, class_=None, attribute=None):
        """Safely extract list of texts or attributes from elements."""
        elements = soup.find_all(tag, class_=class_)
        return [element.get(attribute).strip() if attribute else element.text.strip() for element in elements if element]

    categories = parse_breadcrumbs(driver)
    images = extract_tns_srcset(soup)
    characteristics = parse_characteristics(driver)

    # Extract product details
    item = {
        "id": selector.xpath("//div[@class='product-card-top__code']/text()").get(),
        "url": url,
        "categories": categories,
        "images": images,
        "name": safe_text(soup, 'div', class_="product-card-top__name"),
        "price_discounted": clean_price(selector.xpath("//div[contains(@class, 'product-buy__price_active')]/text()").get()) or None,
        "price_original": clean_price(selector.xpath("//span[@class='product-buy__prev']/text()").get()) or
                          clean_price(selector.xpath("//div[@class='product-buy__price']/text()").get()),
        "rating": float(safe_text(soup, 'a', class_="product-card-top__rating product-card-top__rating_exists",
                             attribute='data-rating')),
        "number_of_reviews": int(safe_text(soup, 'a', class_="product-card-top__rating product-card-top__rating_exists")),
        "brand_logo": logo(),
        "description": safe_text(soup, 'div', class_="product-card-description-text"),
        "characteristics": characteristics,
        "drivers": safe_list(soup, 'a', class_="product-card-description-drivers__item-link", attribute='href'),
        # "profile_names": safe_list(soup, 'div', class_="profile-info__name"),
        # "tab_rating": safe_list(soup, 'div', class_="opinion-rating-slider__tab"),
        # "review": bool(soup.find('div', class_="opinion-multicard-slider")),
        # "review_dates": safe_list(soup, 'div', class_="ow-opinion__date"),
        # "review_texts": safe_list(soup, 'div', class_="ow-opinion__texts"),
        # "votes": safe_text(soup, 'span', class_="vote-widget__sum"),
    }

    return item

def main():
    driver = uc.Chrome()

    # Read URLs from file
    with open('urls.txt', 'r') as file:
        urls = list(map(lambda line: line.strip(), file.readlines()))

    # Parse product details
    parsed_data = []
    # for url in tqdm(urls, ncols=70, unit='товаров', colour='blue', file=sys.stdout):
    try:
        #url
        parsed_data.append(parse_characteristics_page(driver, TEST_URL))
    except Exception as e:
        print(f"Error parsing #url: {e}")

    # Save parsed data
    save_to_json(parsed_data)
    driver.quit()
    print('Product parsing complete!')

if __name__ == '__main__':
    main()