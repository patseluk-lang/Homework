# Тестування функції додавання

Завдання: написати тестовий випадок для функції `add_numbers(a, b)`, яка приймає два аргументи та повертає їх суму, а також зробити аналогічне тестування для функції, що отримує дані з інтернету (погода з [openweathermap.com](https://openweathermap.org/)).

## Склад роботи

| Файл | Опис |
|---|---|
| `test_add_numbers.py` | Функція `add_numbers(a, b)` та тестовий випадок для неї |
| `test_weather.py` | Функція `get_weather(city, api_key)` та тести запиту погоди з OpenWeatherMap |

## 1. `test_add_numbers.py`

Функція `add_numbers(a, b)` повертає суму двох аргументів. Тест `test_add_numbers()` перевіряє її роботу за допомогою `assert`:

- додавання додатних чисел — `3 + 5 == 8`;
- додавання від'ємних чисел — `-2 + (-3) == -5`;
- додавання додатного та від'ємного — `5 + (-3) == 2`;
- додавання нуля — `0 + 7 == 7`;
- додавання до нуля — `10 + 0 == 10`.

## 2. `test_weather.py`

Функція `get_weather(city, api_key)` робить GET-запит до `https://api.openweathermap.org/data/2.5/weather` і повертає словник з назвою міста, температурою та описом погоди.

Основні тести побудовані на моках (`unittest.mock.patch`) — вони швидкі й не залежать від мережі та API-ключа:

- `test_get_weather_success` — правильний розбір відповіді сервера;
- `test_get_weather_negative_temp` — від'ємна температура;
- `test_get_weather_request_params` — запит іде на правильну адресу з правильними параметрами (`q`, `appid`, `units`);
- `test_get_weather_city_not_found` — помилка 404 для неіснуючого міста;
- `test_get_weather_invalid_key` — помилка 401 для невірного API-ключа;
- `test_get_weather_connection_error` — помилка з'єднання;
- `test_get_weather_real_request` — справжній запит в інтернет; автоматично пропускається, якщо не задано змінну оточення `OWM_API_KEY`.

Клас `FakeResponse` імітує `requests.Response`: віддає підготовлений JSON і піднімає `requests.HTTPError` для статусів 400+.

## Запуск

Прямий запуск (виводить «Всі тести пройдено успішно!»):

```bash
python test_add_numbers.py
python test_weather.py
```

Через pytest:

```bash
pytest -v
```

Щоб виконати ще й справжній запит в інтернет, треба задати API-ключ:

```bash
# Linux / macOS
export OWM_API_KEY=ваш_ключ

# Windows (PowerShell)
$env:OWM_API_KEY="ваш_ключ"
```

## Вимоги

- Python 3.8+
- `requests`
- `pytest`

```bash
pip install requests pytest
```
