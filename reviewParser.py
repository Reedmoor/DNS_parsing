import os
import json
import sys
from datetime import datetime
import re

import undetected_chromedriver as uc
from random import randint
from time import sleep as pause

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from tqdm import tqdm


def _safe_element_text(element, by, selector):
    """Safely extract text from an element using various locators."""
    try:
        found_elem = element.find_element(by, selector)
        return found_elem.text.strip() if found_elem else None
    except (NoSuchElementException, AttributeError):
        return None

def convert_date(raw_date):
    date_iso = datetime.strptime(raw_date, "%d.%m.%Y").strftime("%Y-%m-%d")
    return date_iso

def parse_product_details(driver, review_element):
    """Parse additional product details (color, size, etc.) from a specific review element."""
    additions = {}
    try:
        detail_tabs = review_element.find_elements(By.XPATH, './/div[contains(@class, "opinion-multicard-slider__tab")]')

        for tab in detail_tabs:
            try:
                tab_text = tab.text.strip()
                if ':' in tab_text:
                    category, value = tab_text.split(':', 1)
                    category = category.strip()
                    value = value.strip()
                    additions[category] = value
            except Exception as e:
                print(f"Error parsing detail tab: {e}")

    except Exception as e:
        print(f"Error in parse_product_details: {e}")

    return additions

def parse_opinion_ratings(driver, review_element, opinion_id):
    """Parse ratings from a specific review element."""
    ratings = {}
    try:
        # Find rating tabs within this specific review
        rating_tabs = review_element.find_elements(By.XPATH, './/div[contains(@class, "opinion-rating-slider__tab")]')

        for tab in rating_tabs:
            try:
                # Extract category name
                category_name = tab.find_element(By.XPATH,
                                                 './/span[contains(@class, "opinion-rating-slider__tab-title_name")]').text.strip().rstrip(
                    ': ')

                # Extract rating value
                rating_value = tab.find_element(By.XPATH, './/span').text.strip()

                # Handle star rating separately

                if category_name == 'Общая':
                    begins_xpath = './/span[@data-state="selected"]'
                    other_ratings_xpath = './/div[@data-state="selected"]'

                    # Условие для выбора XPath
                    if len(f4rating_elements := tab.find_elements(By.XPATH, begins_xpath)) > 0:
                        rating_value = len(f4rating_elements)
                    else:
                        star_rating_elems = tab.find_elements(By.XPATH, other_ratings_xpath)
                        rating_value = len(star_rating_elems)

                ratings[category_name] = int(rating_value)
            except Exception as e:
                print(f"Error parsing rating tab: {e}")

    except Exception as e:
        print(f"Error in parse_opinion_ratings: {e}")

    return ratings

def parse_review_photos(review_elem):
    """ Parse photo links from review's ow-photos-and-videos section. """
    photo_urls = []

    # Find all img elements within ow-photos-and-videos that have data-src
    photo_elems = review_elem.find_elements(By.XPATH,
                                            './/a[contains(@class, "ow-photos__link")]//img[@data-src]')

    for img in photo_elems:
        original_url = img.get_attribute('data-src')
        url = original_url.replace('crop', 'fit')
        url = url.replace('100/100', '0/0')
        url += ".webp"

        photo_urls.append(url)

    return photo_urls

def load_existing_reviews(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
                else:
                    print(f"Warning: {filename} is empty. Starting with an empty list.")
                    return []
        except json.JSONDecodeError:
            print(f"Warning: {filename} contains invalid JSON. Starting with an empty list.")
            return []
    else:
        print(f"Info: {filename} does not exist. Starting with an empty list.")
        return []

def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_comments(driver, opinion_id):
    tag = driver.find_element(
        By.XPATH,
        f"//div[@data-opinion-id='{opinion_id}']//div[@data-role='opinion-comments']//a",
    )

    text = tag.find_element(By.XPATH, "./span").text.strip()

    matches = re.search(r"\d+", text)

    if not matches:
        return False
    driver.execute_script("arguments[0].scrollIntoView();", tag)
    driver.execute_script("arguments[0].click();", tag)
    pause(randint(1, 2))
    return True


def get_review_container(driver, opinion_id):
    soup = BeautifulSoup(driver.page_source, "html.parser")
    review_container = soup.select_one(
        f'div.ow-opinion.ow-opinions__item[data-opinion-id="{opinion_id}"]'
    )

    if not review_container:
        return None

    return review_container


def parse_comments(driver, opinion_id):
    """Parse comments from the comments list section."""
    review_container = get_review_container(driver, opinion_id)
    if not review_container:
        return []

    if not load_comments(driver, opinion_id):
        return []

    review_container = get_review_container(driver, opinion_id)
    comment_containers = review_container.select("div.comment")

    if not comment_containers:
        return []

    parsed_comments = []

    for comment in comment_containers:
        try:
            comment_content = comment.select_one('.comment__content')

            if comment_content:
                username_elem = comment_content.select_one('.profile-info__name')
                username = username_elem.get_text(strip=True) if username_elem else None

                date_elem = comment_content.find('span', class_=['comment__date', 'time-info'])
                date_text = date_elem.get_text(strip=True) if date_elem else None

                parsed_date = convert_full_date(date_text)

                comment_text_elem = comment_content.find('div', class_=['comment__message', 'message'])
                comment_text = comment_text_elem.get_text(strip=True) if comment_text_elem else None

                likes_elem = comment_content.find('span', class_=['vote-widget__sum'])
                likes = int(likes_elem.get_text(strip=True)) if likes_elem and likes_elem.get_text(
                    strip=True).strip() else 0

                parsed_comments.append({
                    'username': username,
                    'date': parsed_date,
                    'comment_text': comment_text,
                    'likes': likes
                })

        except Exception as comment_error:
            print(f"Error parsing individual comment: {comment_error}")

    return parsed_comments


def convert_full_date(date_string):
    """ Convert Russian full date to a custom datetime format. """
    month_map = {
        'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04',
        'мая': '05', 'июня': '06', 'июля': '07', 'августа': '08',
        'сентября': '09', 'октября': '10', 'ноября': '11', 'декабря': '12'
    }

    try:
        match = re.match(r'(\d{1,2})\s+(\w+)\s+(\d{4})\s+г\.\s+(\d{1,2}):(\d{2})', date_string)
        if match:
            day, month_name, year, hour, minute = match.groups()

            month = month_map.get(month_name, '01')

            return f"{year}-{day.zfill(2)}-{month} {hour.zfill(2)}:{minute}"

        return date_string

    except Exception as e:
        print(f"Error converting date: {e}")
        return date_string


def extract_media_urls(review_elem):
    """ Extract media URLs from image elements with class 'ow-photos__image loaded' """
    try:
        media_xpath = ('.//div[contains(@class, "ow-photos-and-videos")]'
                       '//a[contains(@class, "ow-photos__link")]'
                       '//img[contains(@class, "ow-photos__image")]')
        media_elements = review_elem.find_elements(By.XPATH, media_xpath)

        media_urls = [
            elem.get_attribute('data-src')
            for elem in media_elements
            if elem.get_attribute('data-src')
        ]

        return media_urls
    except Exception as e:
        print(f"Error extracting media URLs: {e}")
        return []

def parse_reviews(driver, json_filename="reviews.json", existing_reviews=None):
    """Parse reviews from the current page."""
    all_reviews = load_existing_reviews(json_filename)
    existing_opinion_ids = {review.get('opinion_id') for review in all_reviews if review.get('opinion_id')}
    try:
        review_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'ow-opinion  ow-opinions__item')]")

        for review_elem in review_elements:
            try:
                opinion_id = review_elem.get_attribute('data-opinion-id')

                if opinion_id in existing_opinion_ids:
                    continue

                opinion_texts = {}
                text_sections = review_elem.find_elements(By.XPATH,
                                                          './/div[contains(@class, "ow-opinion__text")]')
                for section in text_sections:
                    try:
                        title_elem = section.find_element(By.XPATH,
                                                          ".//div[@class='ow-opinion__text-title']")

                        text_elems = section.find_elements(By.XPATH, ".//div[@class='ow-opinion__text-desc']/p")

                        if title_elem and text_elems:
                            title = title_elem.text.strip()

                            # Combine all text elements into a single string
                            text = ' '.join([elem.text.strip() for elem in text_elems])

                            if title == 'Достоинства':
                                opinion_texts['advantages'] = text
                            elif title == 'Недостатки':
                                opinion_texts['disadvantages'] = text
                            elif title == 'Комментарий':
                                opinion_texts['comment'] = text
                    except Exception as e:
                        print(f"Error parsing text section: {e}")

                # Collect review data
                review_data = {
                    'opinion_id': opinion_id,
                    'username': _safe_element_text(review_elem, By.XPATH,
                                                   './/div[contains(@class, "profile-info__name")]'),
                    'date': convert_date(_safe_element_text(review_elem, By.XPATH, './/span[contains(@class, "ow-opinion__date")]')),
                    'rating': parse_opinion_ratings(driver, review_elem, opinion_id),
                    'additions': parse_product_details(driver, review_elem),
                    'advantages': opinion_texts.get('advantages'),
                    'disadvantages': opinion_texts.get('disadvantages'),
                    'comment': opinion_texts.get('comment'),
                    'media': extract_media_urls(review_elem),
                    'likes': int(_safe_element_text(review_elem, By.XPATH, './/span[contains(@class, "vote-widget__sum")]')),
                    'comments': parse_comments(driver, opinion_id)
                }
                print(review_data)

                if opinion_id not in existing_opinion_ids:
                    all_reviews.append(review_data)
                    existing_opinion_ids.add(opinion_id)
                    save_to_json(all_reviews, json_filename)
                    print(f"Added new review with ID {opinion_id} to {json_filename}")
            except Exception as e:
                print(f"Error parsing review: {e}")

    except Exception as e:
        print(f"Error in parse_reviews: {e}")

    return all_reviews

def parse_urls_from_file(urls="urls.txt"):
    with open(urls, 'r') as file:
        return [line.strip() for line in file.readlines() if line.strip()]

def main():

    # Set up the webdriver with additional options for stability
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = None
    with open('urls.txt','r') as text:
        urls = [line.strip() for line in text.readlines() if line.strip()]
        for url in tqdm(urls, ncols=70, unit='товар', colour='blue', file=sys.stdout):
            try:
                driver = uc.Chrome(options=options)
                driver.get(url)
                pause(randint(1, 2))  # Random pause to simulate human behavior

                # Find and extract the reviews page URL
                rating_link = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//a[contains(@class, "product-card-top__rating_exists")]'))
                )
                reviews_url = rating_link.get_attribute("href")
                print(f"Reviews URL: {reviews_url}")



                # Navigate directly to reviews page
                driver.get(reviews_url)
                pause(randint(1, 2))  # Wait for the reviews page to load

                all_reviews = parse_reviews(driver)

                # Click "Load More" button to get additional reviews
                while True:
                    try:

                        load_more_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH,
                                                        '//button[contains(@class, "button-ui_lg") and contains(@class, "paginator-widget__more")]'))
                        )
                        load_more_button.click()
                        pause(randint(2, 4))  # Wait for new reviews to load

                        parse_reviews(driver)

                    except TimeoutException:
                        # No more "Load More" button, exit the loop
                        break

                # Save reviews to JSON
                save_to_json(all_reviews)
                print(f'Total reviews parsed: {len(all_reviews)}')

            except Exception as e:
                print(f"An error occurred: {e}")
                import traceback
                traceback.print_exc()
            finally:
                # Ensure driver is closed properly
                if driver:
                    try:
                        driver.quit()
                    except Exception as quit_error:
                        print(f"Error closing driver: {quit_error}")


if __name__ == '__main__':
    main()