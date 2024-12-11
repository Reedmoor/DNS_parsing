import sys
import json
import undetected_chromedriver as uc
from random import randint
from time import sleep as pause
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def _safe_element_text(element, by, selector):
    """Safely extract text from an element using various locators."""
    try:
        found_elem = element.find_element(by, selector)
        return found_elem.text.strip() if found_elem else None
    except (NoSuchElementException, AttributeError):
        return None


def parse_opinion_ratings(driver, review_element):
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
                    star_rating_elems = tab.find_elements(By.XPATH,
                                                          './/div[contains(@class, "star-rating")]//span[@data-state="selected"]')
                    rating_value = len(star_rating_elems)

                ratings[category_name] = rating_value
            except Exception as e:
                print(f"Error parsing rating tab: {e}")

    except Exception as e:
        print(f"Error in parse_opinion_ratings: {e}")

    return ratings


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


def parse_reviews(driver):
    """Parse reviews from the current page."""
    reviews = []
    try:
        # Find all review elements
        review_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'ow-opinion  ow-opinions__item')]")

        for review_elem in review_elements:
            try:
                # Parse opinion texts
                opinion_texts = {}
                text_sections = review_elem.find_elements(By.XPATH,
                                                          './/div[contains(@class, "ow-opinion__text")]')
                for section in text_sections:
                    try:
                        title_elem = section.find_element(By.XPATH,
                                                          ".//div[@class='ow-opinion__text-title']")

                        text_elem = section.find_element(By.XPATH, ".//div[@class='ow-opinion__text-desc']/p")


                        if title_elem and text_elem:
                            title = title_elem.text.strip()
                            text = text_elem.text.strip()

                            if title == 'Достоинства':
                                opinion_texts['advantages'] = text
                            elif title == 'Недостатки':
                                opinion_texts['disadvantages'] = text
                            elif title == 'Комментарий':
                                opinion_texts['comment'] = text
                    except Exception as e:
                        print(f"Error parsing text section: {e}")

                    print(opinion_texts.get('advantages'))
                    print(opinion_texts.get('disadvantages'))
                    print(opinion_texts.get('comment'))

                # Collect review data
                review_data = {
                    'username': _safe_element_text(review_elem, By.XPATH,
                                                   './/div[contains(@class, "profile-info__name")]'),
                    'date': _safe_element_text(review_elem, By.XPATH, './/span[contains(@class, "ow-opinion__date")]'),
                    'rating': parse_opinion_ratings(driver, review_elem),
                    'advantages': opinion_texts.get('advantages'),
                    'disadvantages': opinion_texts.get('disadvantages'),
                    'comment': opinion_texts.get('comment'),
                    'likes': _safe_element_text(review_elem, By.XPATH, './/span[contains(@class, "vote-widget__sum")]'),
                }
                print(review_data)

                reviews.append(review_data)
            except Exception as e:
                print(f"Error parsing review: {e}")

    except Exception as e:
        print(f"Error in parse_reviews: {e}")

    return reviews


def main():
    # URL of the product to scrape
    TEST_URL = "https://www.dns-shop.ru/product/a67afeaff7bbd9cb/robot-pylesos-dreame-x40-ultra-complete-belyj/"

    # Set up the webdriver with additional options for stability
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = None
    try:
        driver = uc.Chrome(options=options)
        driver.get(TEST_URL)
        pause(randint(2, 4))  # Random pause to simulate human behavior

        # Find and extract the reviews page URL
        rating_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//a[contains(@class, "product-card-top__rating_exists")]'))
        )
        reviews_url = rating_link.get_attribute("href")
        print(f"Reviews URL: {reviews_url}")

        # Navigate directly to reviews page
        driver.get(reviews_url)
        pause(randint(2, 4))  # Wait for the reviews page to load

        all_reviews = []

        # Collect initial reviews
        all_reviews.extend(parse_reviews(driver))

        # Click "Load More" button to get additional reviews
        while True:
            try:
                load_more_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH,
                                                '//button[contains(@class, "button-ui_lg") and contains(@class, "paginator-widget__more")]'))
                )
                load_more_button.click()
                pause(randint(4, 6))  # Wait for new reviews to load

                # Parse newly loaded reviews
                new_reviews = parse_reviews(driver)

                # Check if we've already seen these reviews
                new_unique_reviews = [
                    review for review in new_reviews
                    if review not in all_reviews
                ]

                all_reviews.extend(new_unique_reviews)

                # If no new reviews, break the loop
                if not new_unique_reviews:
                    break

            except TimeoutException:
                # No more "Load More" button, exit the loop
                break

        # Save reviews to JSON
        if all_reviews:
            save_to_json(all_reviews)
            print(f'Total reviews parsed: {len(all_reviews)}')
        else:
            print("No reviews found.")

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