import sys
import json
import scrapy
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from random import randint
from time import sleep as pause

def parse_opinion_ratings(driver, url):
    """
    Parse ratings from an HTML file containing opinion ratings.

    Args:
        file_path (str): Path to the HTML file

    Returns:
        dict: A dictionary of ratings for different categories
    """
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'lxml')

    ratings = {}

    # Find all rating tabs
    rating_tabs = soup.find_all('div', class_='opinion-rating-slider__tab')

    for tab in rating_tabs:
        # Extract category name
        category_name = tab.find('span', class_='opinion-rating-slider__tab-title_name').text.strip().rstrip(': ')

        # Extract rating value
        rating_value = tab.find('span').text.strip()

        # Handle star rating separately
        if category_name == 'Общая':
            star_rating_elem = tab.find('div', class_='star-rating')
            if star_rating_elem:
                selected_stars = star_rating_elem.find_all('span', attrs={'data-state': 'selected'})
                rating_value = len(selected_stars)

        ratings[category_name] = rating_value

    return ratings


# Existing functions from the previous script remain the same
TEST_URL = "https://www.dns-shop.ru/product/a67afeaff7bbd9cb/robot-pylesos-dreame-x40-ultra-complete-belyj/"

def save_to_json(data, filename="reviews.json"):
    """Save data to JSON file."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Reviews successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving reviews to JSON: {e}")
        import traceback
        traceback.print_exc()


def parse_reviews(driver, url):
    """Parse reviews from the product page."""
    driver.get(url)
    pause(randint(7, 10))  # Random pause to simulate human behavior

    soup = BeautifulSoup(driver.page_source, 'lxml')
    selector = scrapy.Selector(text=driver.page_source)

    # Find all review elements
    review_elements = soup.find_all('div', class_='ow-opinion ow-opinions__item')

    reviews = []
    for review_elem in review_elements:
        try:
            # Create a dictionary to store additional text sections
            additional_texts = {}

            # Find all text sections with titles
            text_sections = review_elem.find_all('div', class_='ow-opinion__text-section')
            for section in text_sections:
                title_elem = section.find('div', class_='ow-opinion__text-title')
                text_elem = section.find('div', class_='ow-opinion__text-desc')

                if title_elem and text_elem:
                    title = title_elem.text.strip()
                    text = text_elem.text.strip()

                    if title == 'Достоинства':
                        additional_texts['advantages'] = text
                    elif title == 'Недостатки':
                        additional_texts['disadvantages'] = text
                    elif title == 'Комментарий':
                        additional_texts['comment'] = text

            # Extract review details
            review_data = {
                # User details
                'username': _safe_text(review_elem, 'div', class_='profile-info__name'),

                # Review content
                'text': _safe_text(review_elem, 'div', class_='ow-opinion__text'),

                # Date and rating
                'date': _safe_text(review_elem, 'span', class_='ow-opinion__date'),
                'rating': parse_opinion_ratings(driver, TEST_URL),

                # Additional details from text sections
                'advantages': additional_texts.get('advantages'),
                'disadvantages': additional_texts.get('disadvantages'),
                'comment': additional_texts.get('comment'),

                'recommendation': _safe_text(review_elem, 'div', class_='ow-opinion__recommend')
            }

            # Only add non-empty reviews
            if review_data['text']:
                reviews.append(review_data)

        except Exception as e:
            print(f"Error parsing review: {e}")

    # Try to find and click "Load More" button
    try:
        # Use selenium's new method for finding elements
        load_more_button = driver.find_element('button', 'button-ui_lg.paginator-widget__more')

        while load_more_button and load_more_button.is_displayed():
            load_more_button.click()
            pause(randint(4, 6))  # Wait for new reviews to load

            # Re-parse the page to get new reviews
            soup = BeautifulSoup(driver.page_source, 'lxml')
            additional_reviews = soup.find_all('div', class_='ow-opinion ow-opinions__item')

            for review_elem in additional_reviews[len(reviews):]:
                try:
                    # Find additional text sections
                    additional_texts = {}
                    text_sections = review_elem.find_all('div', class_='ow-opinion__text-section')
                    for section in text_sections:
                        title_elem = section.find('div', class_='ow-opinion__text-title')
                        text_elem = section.find('div', class_='ow-opinion__text-desc')

                        if title_elem and text_elem:
                            title = title_elem.text.strip()
                            text = text_elem.text.strip()

                            if title == 'Достоинства':
                                additional_texts['advantages'] = text
                            elif title == 'Недостатки':
                                additional_texts['disadvantages'] = text
                            elif title == 'Комментарий':
                                additional_texts['comment'] = text

                    review_data = {
                        'username': _safe_text(review_elem, 'div', class_='profile-info__name'),
                        'text': _safe_text(review_elem, 'div', class_='ow-opinion__text'),
                        'date': _safe_text(review_elem, 'span', class_='ow-opinion__date'),
                        'rating': parse_opinion_ratings(driver, TEST_URL),
                        'advantages': additional_texts.get('advantages'),
                        'disadvantages': additional_texts.get('disadvantages'),
                        'comment': additional_texts.get('comment'),
                    }

                    if review_data['text']:
                        reviews.append(review_data)
                except Exception as e:
                    print(f"Error parsing additional review: {e}")

            # Find the load more button again using new selenium method
            load_more_button = driver.find_element('button', 'button-ui_lg.paginator-widget__more')

    except Exception as e:
        print("No more reviews to load or error loading reviews")

    return reviews

def _safe_text(element, tag, class_=None):
    """Safely extract text from an element."""
    try:
        # Use CSS selector to match class with potential additional spaces
        found_elem = element.find(tag, class_=lambda x: x and class_ in x.split())
        return found_elem.text.strip() if found_elem else None
    except Exception:
        return None

def main():
    driver = uc.Chrome()
    # Demonstrate new parse_opinion_ratings function
    ratings = parse_opinion_ratings(driver, TEST_URL)
    print("Ratings from the uploaded file:")
    for category, rating in ratings.items():
        print(f"{category}: {rating}")

    try:
        reviews = parse_reviews(driver, TEST_URL)
        save_to_json(reviews)
        print(f'Total reviews parsed: {len(reviews)}')
    except Exception as e:
        print(f"Error during parsing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()


if __name__ == '__main__':
    main()