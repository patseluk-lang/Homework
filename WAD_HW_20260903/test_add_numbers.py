def add_numbers(a, b):
    """Приймає два аргументи та повертає їх суму."""
    return a + b


def test_add_numbers():
    # Перевірка додавання додатних чисел
    assert add_numbers(3, 5) == 8

    # Перевірка додавання від'ємних чисел
    assert add_numbers(-2, -3) == -5

    # Перевірка додавання додатнього та від'ємного чисел
    assert add_numbers(5, -3) == 2

    # Перевірка додавання нуля
    assert add_numbers(0, 7) == 7

    # Перевірка додавання до нуля
    assert add_numbers(10, 0) == 10


if __name__ == "__main__":
    test_add_numbers()
    print("Всі тести пройдено успішно!")
