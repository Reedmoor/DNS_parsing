import requests
import json

BASE_URL = "https://restapi.dns-shop.ru/v1"
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "origin": "https://www.dns-shop.ru",
}

def get_cities():
    """Получает список городов и их идентификаторы."""
    url = f"{BASE_URL}/get-city-list"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        cities = response.json().get("data", [])
        return cities
    else:
        print(f"Ошибка получения списка городов: {response.status_code}")
        return []

def get_categories(city_id="4186730a-779c-11e0-80d3-001517c526f0"):
    """Получает категории для указанного города."""
    url = f"{BASE_URL}/get-menu"
    headers = {**HEADERS, "cityid": city_id}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        categories = response.json().get("data", [])
        return categories
    else:
        print(f"Ошибка получения категорий для cityId={city_id}: {response.status_code}")
        return []

def save_to_json(data, filename):
    """Сохраняет данные в JSON файл."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Данные сохранены в {filename}")

def main():
    # Получаем список городов
    cities = get_cities()
    save_to_json(cities, "cities.json")
    print("Список городов сохранён в cities.json")

    # Устанавливаем cityId для Москвы
    moscow_city_id = "30b7c1f3-03fb-11dc-95ee-00151716f9f5"

    # Получаем категории для Москвы
    categories = get_categories(city_id=moscow_city_id)
    save_to_json(categories, "categories.json")
    print("Категории сохранены в categories.json")

if __name__ == "__main__":
    main()
