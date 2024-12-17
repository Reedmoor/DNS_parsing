# Ситилинк

Сбор данных о товарах и отзывах с сайта dns-shop.ru

## Расположение

- **Сервер**: IP сервера / Домен
- **Путь к проекту**: /.../.../.../parser

## Запуск

- Локально
    1. Клонировать репозиторий `git clone https://github.com/Reedmoor/DNS_parsing`
    2. Установить зависимости `pip install -r requirements.txt`
    3. `py main.py`

## Конфигурация

Конфиг указывается в файле `.env` (Или в любом другом)

```env
CATEGORY = "frezery"
```

## Модели/Структуры данных

### Товар

```json
{
        "id": "",
        "url": "",
        "categories": [],
        "images": [],
        "name": "",
        "price_discounted": 0,
        "price_original": 0,
        "rating": 0,
        "number_of_reviews": 0,
        "brand_name": "",
        "characteristics": {},
        "drivers": []
    }
```

### Отзыв

```json
{
        "opinion_id": "",
        "username": "",
        "date": "",
        "rating": {},
        "additions": {},
        "advantages": "",
        "disadvantages": "",
        "comment": "",
        "media": [],
        "likes": 0,
        "comments": []
}
```

## Основные зависимости

| Название      | Ссылка                                            |
| ------------- | ------------------------------------------------- |
| selenium      | [Ссылка](https://pypi.org/project/selenium/)      |
| beautifulsoup4| [Ссылка](https://pypi.org/project/beautifulsoup4/)|
| Scrapy        | [Ссылка](https://pypi.org/project/Scrapy/)        | 
