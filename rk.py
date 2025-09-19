"""
Реалізація Рабіна–Карпа з параметрами base і modulus.

Є два варіанти обчислення поліноміального хешу:
1) _polynomial_hash_pow — оригінальний (повільніший) варіант з pow(...)
2) _polynomial_hash_fast — ефективний варіант через поступове множення

За замовчуванням у search() використовується pow-варіант, щоб
зберегти відповідність конспекту; поруч залишено закоментовані рядки
(ALTERNATIVE), щоб швидко переключатися на швидкий варіант.
"""
from __future__ import annotations


# -------------------------------
# ОБЧИСЛЕННЯ ХЕШІВ (ДВА ВАРІАНТИ)
# -------------------------------
def _polynomial_hash_pow(s: str, base: int, modulus: int) -> int:
    """## Повільніший варіант хешування через pow(base, ...)

    ---
    #### Цей варіант прямо відповідає класичному конспектному опису
    > 🔰 Його логіка: `h = sum(ord(s[i]) * base^(n-i-1)) % modulus`.

    👇🏻 _Нижче більш ефективний алгоритм:_ `h = (h * base + ord(ch)) % modulus`  
    для застосування в методі `search()`. _(див. докстрінги і коментарі)_
    """
    n = len(s)
    hash_value = 0
    for i, ch in enumerate(s):
        power_of_base = pow(base, n - i - 1, modulus)
        hash_value = (hash_value + ord(ch) * power_of_base) % modulus
    return hash_value


def _polynomial_hash_fast(s: str, base: int, modulus: int) -> int:
    """## Ефективніший поліноміальний хеш через поступове накопичення.

    ---
    #### Розробка з рекомендаціями ШІ, що виявилась помітно швидшою.
    > 🔰 Його логіка: `h = (h * base + ord(ch)) % modulus`

    ☝🏻 _Вище варіант з конспекту (більш повільний):_ `h = sum(ord(s[i]) * base^(n-i-1)) % modulus`  
    для застосування в методі `search()`. _(див. докстрінги і коментарі)_
    """
    h = 0
    for ch in s:
        h = (h * base + ord(ch)) % modulus
    return h


# Сам метод пошуку
def search(text: str, pattern: str, base: int = 257, modulus: int = 1000003) -> int:
    """## Повертає індекс першого входження `pattern` у `text` або `-1`.

    #### _Зауваження:_
    - Змінна`modulus` має бути простим великим числом, щоб зменшити ймовірність колізій;
    - За замовчуванням використовується pow-варіант (конспектний).  
      _(можна також протестувати швидкий варіант, дивись помітку **"АЛЬТЕРНАТИВА"** нижче)_
    """
    n = len(text)
    m = len(pattern)
    if m == 0:
        return 0
    if m > n:
        return -1

    # За замовчуванням використовуємо pow-варіант, який прямо відповідає конспекту.
    # -----------------------------------------------------------------------------
    # АЛЬТЕРНАТИВА! Щоб переключитися на швидкий варіант потрібно розкоментувати
    # два рядки коду нижче, а ці закоментувати.
    # pattern_hash = _polynomial_hash_fast(pattern, base, modulus)
    # window_hash = _polynomial_hash_fast(text[:m], base, modulus)
    pattern_hash = _polynomial_hash_pow(pattern, base, modulus)
    window_hash = _polynomial_hash_pow(text[:m], base, modulus)


    # Множник для відкидання старого символу: base^(m-1) % modulus
    h_multiplier = pow(base, m - 1, modulus)

    for i in range(n - m + 1):
        if pattern_hash == window_hash:
            # при збігу хешів перевіряємо точно
            if text[i:i + m] == pattern:
                return i
        if i < n - m:
            # Оновлення ролінг-хешу для наступного вікна
            left = (ord(text[i]) * h_multiplier) % modulus
            window_hash = (window_hash - left) % modulus
            window_hash = (window_hash * base + ord(text[i + m])) % modulus

    return -1