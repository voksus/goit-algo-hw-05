"""
Спрощена реалізація алгоритму Боєра–Мура.
застосовано лише підхід з поганим символом.
Гарна для природних текстів. у гіршому випадку може вести себе повільно.
"""
from __future__ import annotations


def build_last_occurrence(pattern: str) -> dict[str, int]:
    """## Побудова таблиці останніх позицій символів у патерні

    ---
    #### Якщо символу в патерні немає, значення за замовчуванням буде `-1`.
    """
    table: dict[str, int] = {}
    for idx, ch in enumerate(pattern):
        table[ch] = idx
    return table


def search(text: str, pattern: str) -> int:
    """## Повертає індекс першого входження pattern у text або `-1`

    ---
    #### Імплементовано лише підхід з таблицею поганого символу щоб зберегти простоту (і достатність для ДЗ).
    > ☝🏻 _Таблиці доброго суфіксу не було реалізовано._
    """
    n = len(text)
    m = len(pattern)
    if m == 0:
        return 0
    if m > n:
        return -1

    last = build_last_occurrence(pattern)
    i = 0
    while i <= n - m:
        j = m - 1
        while j >= 0 and text[i + j] == pattern[j]:
            j -= 1
        if j < 0:
            return i
        # Зсув: якщо символу text[i+j] немає у pattern, last.get(...) дасть None -> -1
        lo = last.get(text[i + j], -1)
        shift = max(1, j - lo)
        i += shift
    return -1