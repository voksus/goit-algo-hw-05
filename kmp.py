from __future__ import annotations


def compute_lps(pattern: str) -> list[int]:
    """## Побудова LPS-масиву (longest proper suffix)

    ---
    #### `lps[i]` = довжина найдовшого префікса, який одночасно є суфіксом для підрядка `pattern[0..i]`.
    > _Часова складність: `O(m)`, пам'ять: `O(m)`._
    """
    m = len(pattern)
    lps = [0] * m
    length = 0
    i = 1
    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        else:
            if length != 0:
                length = lps[length - 1]
            else:
                lps[i] = 0
                i += 1
    return lps


def search(text: str, pattern: str) -> int:
    """## Повертає індекс першого входження pattern у text або `-1` якщо не знайдено.

    ---
    > ☝🏻 _Робота: `O(n + m)` по часу, `O(m)` додаткової пам'яті для `lps`._
    """
    n = len(text)
    m = len(pattern)
    if m == 0:
        return 0
    if m > n:
        return -1

    lps = compute_lps(pattern)
    i = j = 0
    while i < n:
        if text[i] == pattern[j]:
            i += 1
            j += 1
            if j == m:
                return i - j
        else:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1
    return -1