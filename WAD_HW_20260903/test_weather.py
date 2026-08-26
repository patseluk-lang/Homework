"""Тестування функції, яка отримує погоду з openweathermap.com.

Основні тести працюють на моках (unittest.mock) — вони швидкі та не залежать
від мережі й API-ключа. Останній тест робить справжній запит в інтернет і
автоматично пропускається, якщо змінна оточення OWM_API_KEY не задана.
"""

import os
from unittest.mock import patch

import pytest
import requests

API_URL = "https://api.openweathermap.org/data/2.5/weather"


def get_weather(city, api_key):
    """Повертає словник з погодою для міста: назва, температура, опис."""
    params = {"q": city, "appid": api_key, "units": "metric", "lang": "uk"}
    response = requests.get(API_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    return {
        "city": data["name"],
        "temp": data["main"]["temp"],
        "description": data["weather"][0]["description"],
    }


class FakeResponse:
    """Підробка requests.Response для тестів."""

    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code

    def json(self):
        return self.data

    def raise_for_status(self):
        if self.status_code >= 400:
            error = requests.HTTPError(f"HTTP {self.status_code}")
            error.response = self
            raise error


FAKE_DATA = {
    "name": "Kyiv",
    "main": {"temp": 21.5},
    "weather": [{"description": "ясно"}],
}


def test_get_weather_success():
    # Перевірка правильного розбору відповіді сервера
    with patch("requests.get", return_value=FakeResponse(FAKE_DATA)):
        weather = get_weather("Kyiv", "test_key")

    assert weather == {"city": "Kyiv", "temp": 21.5, "description": "ясно"}


def test_get_weather_negative_temp():
    # Перевірка від'ємної температури
    data = {"name": "Lviv", "main": {"temp": -7.3}, "weather": [{"description": "сніг"}]}
    with patch("requests.get", return_value=FakeResponse(data)):
        weather = get_weather("Lviv", "test_key")

    assert weather["temp"] == -7.3


def test_get_weather_request_params():
    # Перевірка, що запит іде на правильну адресу з правильними параметрами
    with patch("requests.get", return_value=FakeResponse(FAKE_DATA)) as fake_get:
        get_weather("Odesa", "test_key")

    fake_get.assert_called_once()
    args, kwargs = fake_get.call_args
    assert args[0] == API_URL
    assert kwargs["params"]["q"] == "Odesa"
    assert kwargs["params"]["appid"] == "test_key"
    assert kwargs["params"]["units"] == "metric"


def test_get_weather_city_not_found():
    # Перевірка помилки 404 — неіснуюче місто
    with patch("requests.get", return_value=FakeResponse({}, status_code=404)):
        with pytest.raises(requests.HTTPError) as error:
            get_weather("QwertyCity12345", "test_key")

    assert error.value.response.status_code == 404


def test_get_weather_invalid_key():
    # Перевірка помилки 401 — невірний API-ключ
    with patch("requests.get", return_value=FakeResponse({}, status_code=401)):
        with pytest.raises(requests.HTTPError) as error:
            get_weather("Kyiv", "wrong_key")

    assert error.value.response.status_code == 401


def test_get_weather_connection_error():
    # Перевірка помилки з'єднання
    with patch("requests.get", side_effect=requests.ConnectionError("no network")):
        with pytest.raises(requests.ConnectionError):
            get_weather("Kyiv", "test_key")


@pytest.mark.skipif(
    not os.environ.get("OWM_API_KEY"),
    reason="Не задано змінну оточення OWM_API_KEY — справжній запит пропущено",
)
def test_get_weather_real_request():
    # Справжній запит в інтернет до openweathermap.com
    weather = get_weather("Kyiv", os.environ["OWM_API_KEY"])

    assert weather["city"] == "Kyiv"
    assert isinstance(weather["temp"], (int, float))
    assert -60 < weather["temp"] < 60
    assert len(weather["description"]) > 0


if __name__ == "__main__":
    test_get_weather_success()
    test_get_weather_negative_temp()
    test_get_weather_request_params()
    test_get_weather_city_not_found()
    test_get_weather_invalid_key()
    test_get_weather_connection_error()
    if os.environ.get("OWM_API_KEY"):
        test_get_weather_real_request()
    print("Всі тести пройдено успішно!")
