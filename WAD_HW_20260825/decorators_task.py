"""Декоратори для перевірки функцій на можливі помилки під час виконання."""

import sys
from functools import wraps


def check_division_error(func):
    """Перехоплює ділення на нуль і завершує виконання програми."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ZeroDivisionError:
            print(f"Помилка: ділення на нуль у функції '{func.__name__}'.")
            sys.exit(1)

    return wrapper


def check_index_error(func):
    """Перехоплює вихід індексу за межі списку і завершує виконання програми."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IndexError:
            print(f"Помилка: індекс поза межами списку у функції '{func.__name__}'.")
            sys.exit(1)

    return wrapper


@check_division_error
def divide(a, b):
    """Повертає результат ділення a на b."""
    return a / b


@check_index_error
def get_element(lst, idx):
    """Повертає елемент списку lst за індексом idx."""
    return lst[idx]


if __name__ == "__main__":
    # Коректні виклики divide
    print("divide(10, 2)   =", divide(10, 2))
    print("divide(-9, 3)   =", divide(-9, 3))
    print("divide(7, 0.5)  =", divide(7, 0.5))

    # Коректні виклики get_element
    numbers = [10, 20, 30]
    print("get_element(numbers, 0)  =", get_element(numbers, 0))
    print("get_element(numbers, 2)  =", get_element(numbers, 2))
    print("get_element(numbers, -1) =", get_element(numbers, -1))

    # Помилкові виклики. Декоратор завершує програму на першому ж з них,
    # тому перевіряти їх треба по черзі: один рядок розкоментувати,
    # інший — закоментувати.
    print("get_element(numbers, 5) =", get_element(numbers, 5))
    # print("divide(5, 0) =", divide(5, 0))

    print("Цей рядок не виконається — програма завершилась вище.")