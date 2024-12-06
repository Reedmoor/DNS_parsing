import requests

def get_categories():
    url = "https://restapi.dns-shop.ru/v1/get-city-list"

    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "origin": "https://www.dns-shop.ru",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        categories = response.json()
        print(categories)
        return categories
    else:
        print(f"Ошибка: {response.status_code}")
        return None

if __name__ == "__main__":
    categories_data = get_categories()

