"""Пошук простих чисел: однопотоковий та багатопотоковий варіанти."""

import math
import threading
import time


def is_prime(n):
    """Повертає True, якщо n — просте число, інакше False."""
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False
    # Парні дільники вже відсіяні, тому перевіряємо лише непарні до sqrt(n).
    limit = math.isqrt(n) + 1
    for i in range(3, limit, 2):
        if n % i == 0:
            return False
    return True


def find_primes_single_thread(start, end):
    """Знаходить усі прості числа в діапазоні [start, end] в одному потоці."""
    return [n for n in range(start, end + 1) if is_prime(n)]


def find_primes_multi_thread(start, end):
    """Те саме, але діапазон ділиться на дві частини й рахується у двох потоках."""
    middle = (start + end) // 2
    results = [None, None]

    def worker(index, low, high):
        results[index] = find_primes_single_thread(low, high)

    threads = [
        threading.Thread(target=worker, args=(0, start, middle)),
        threading.Thread(target=worker, args=(1, middle + 1, end)),
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # Перша половина завжди менша за другу, тому просте склеювання зберігає зростаючий порядок.
    return results[0] + results[1]


def measure(func, start, end):
    """Повертає (результат, час виконання у секундах)."""
    begin = time.perf_counter()
    result = func(start, end)
    return result, time.perf_counter() - begin


def run_tests():
    """Тестові випадки: перевірка is_prime і збігу результатів обох функцій."""
    print("=== Тестування ===")

    assert is_prime(2) is True
    assert is_prime(3) is True
    assert is_prime(17) is True
    assert is_prime(1) is False
    assert is_prime(0) is False
    assert is_prime(-7) is False
    assert is_prime(9) is False
    assert is_prime(100) is False
    print("is_prime(): усі перевірки пройдено")

    assert find_primes_single_thread(1, 30) == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    print("find_primes_single_thread(1, 30): результат правильний")

    test_ranges = [(1, 1), (2, 2), (1, 30), (1, 100), (500, 1000), (10000, 20000)]
    for start, end in test_ranges:
        single = find_primes_single_thread(start, end)
        multi = find_primes_multi_thread(start, end)
        assert single == multi, f"Розбіжність у діапазоні {start}-{end}"
        print(f"Діапазон {start}-{end}: результати збігаються, знайдено {len(single)} простих чисел")

    print("Усі тести пройдено успішно\n")


def compare_performance():
    """Вимірювання та порівняння часу виконання для різних діапазонів."""
    print("=== Порівняння швидкодії ===")
    print(f"{'Діапазон':>22} | {'Простих':>8} | {'1 потік, с':>11} | {'2 потоки, с':>12} | {'Прискорення':>11}")
    print("-" * 78)

    ranges = [(1, 10000), (1, 100000), (1, 500000), (100000, 1000000)]
    for start, end in ranges:
        single, single_time = measure(find_primes_single_thread, start, end)
        multi, multi_time = measure(find_primes_multi_thread, start, end)
        assert single == multi, f"Розбіжність у діапазоні {start}-{end}"
        speedup = single_time / multi_time
        print(
            f"{f'{start}-{end}':>22} | {len(single):>8} | {single_time:>11.4f} | "
            f"{multi_time:>12.4f} | {speedup:>10.2f}x"
        )


ANALYSIS = """
=== Аналіз результатів ===

Багатопотоковий варіант майже не дає виграшу, а часто працює навіть повільніше
за однопотоковий. Причини:

1. GIL (Global Interpreter Lock). У CPython лише один потік одночасно виконує
   байткод Python. Пошук простих чисел — це чисто обчислювальна задача (CPU-bound),
   тому два потоки не рахують паралельно, а по черзі отримують GIL. Сумарний обсяг
   обчислень той самий, тому й час залишається приблизно однаковим.

2. Накладні витрати. Створення потоків, перемикання контексту між ними та
   об'єднання результатів забирають додатковий час. На малих діапазонах ці витрати
   помітно перевищують будь-яку користь, і багатопотокова версія програє.

3. Нерівномірний розподіл роботи. Діапазон ділиться навпіл за значенням, але не за
   складністю: перевірка більших чисел вимагає більше ітерацій (цикл до sqrt(n)).
   Тому другий потік завершує роботу пізніше, і загальний час визначається саме ним.

Коли багатопотоковість була б ефективною:
— для задач вводу-виводу (мережеві запити, робота з файлами, база даних), бо під час
  очікування потік звільняє GIL і інший потік працює;
— якщо обчислення виконує бібліотека на C (NumPy), яка звільняє GIL.

Що дало б реальне прискорення тут: модуль multiprocessing — кожен процес має власний
інтерпретатор і власний GIL, тому обчислення справді розподіляються між ядрами.
"""


if __name__ == "__main__":
    run_tests()
    compare_performance()
    print(ANALYSIS)