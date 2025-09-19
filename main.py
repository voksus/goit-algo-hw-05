"""
Контролер для запуску бенчмарків.

- Імпортує DATA з data_const.py (вже нормалізоване при імпорті).
- Імпортує алгоритми з kmp, bm, rk.
- Виконує Timer.repeat(repeat, number) для кожної комбінації,
  збирає per-call times, обчислює min/max/avg і зберігає у results.
- Перед виміром вимикає GC, після вимірів вмикає GC і викликає gc.collect().
- Після timeit заміряє пам'ять через tracemalloc та виводить її у консоль
  (поточне та пікове значення), потім вимикає tracemalloc.
"""
from __future__ import annotations

import gc
import re
import time
import timeit
import tracemalloc
from typing import Callable

import kmp
import bm
import rk
from data_const import DATA

# Список імен алгоритмів
KMP       = "kmp"
BM        = "bm"
RK        = "rk"
PY_FIND   = "py_find"
RE_SEARCH = "re_search"
ALG = {KMP       : ("Кнута-Морріса-Пратта", 0),
       BM        : ("Бойера-Мура"         , 1),
       RK        : ("Рабіна-Карпа"        , 2),
       PY_FIND   : ("str.find(..)"        , 3),
       RE_SEARCH : ("re.search(..)"       , 4) }
ALG_NAME_LEN = max(max(len(name) for name, _ in ALG.values()), 15)

# Декорування виводу
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
ITALIC  = "\033[3m"
ULINE   = "\033[4m"
RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
BLUE    = "\033[34m"
MAGENTA = "\033[35m"
CYAN    = "\033[36m"
WHITE   = "\033[37m"

REPEATS = 5

# Шаблон для виводу прогресу бенчмарку
BENCHMARK_PROGRESS_TEMPLATE = (
    f"{BOLD+GREEN+'{stl_placeholder}'}{{alg_name_placeholder:20}}{RESET+'{stl_placeholder}'} : "
    f"Текст № {BLUE}{{text_idx_placeholder}}{RESET+'{stl_placeholder}'}, довжина = {BLUE}{{text_len_placeholder:6,}}{RESET+'{stl_placeholder}'}, "
    f"підрядок № {BLUE}{{pat_idx_placeholder}}{RESET+'{stl_placeholder}'}, довжина = {BLUE}{{pat_len_placeholder:5,}}{RESET}"
)


# -------------------------------
# Очищаємо консоль перед запуском
print("\033[H\033[J", end="")


def _py_find(text: str, pattern: str) -> int:
    """
    Простий еталон: метод `str.find` (C-реалізація)
    Повертає індекс першого входження pattern у text або -1.
    """
    return text.find(pattern)


def _re_search(text: str, pattern: str) -> int:
    """
    Використовуємо `re.search` з екрануванням патерну з модулю регулярних виразів.
    Повертає індекс першого входження pattern у text або -1.
    """
    m = re.search(re.escape(pattern), text)
    return m.start() if m is not None else -1


def _choose_number_for_pattern_length(length: int) -> int:
    """
    Правила для кількості повторень `number` у `timeit` в залежності від довжини патерна.
    """
    if length <= 5:
        return 3000
    if length <= 15:
        return 1000
    if length <= 50:
        return 200
    if length <= 200:
        return 50
    return 10


def launch_benchmark(repeat: int = REPEATS):
    """# Головна функція запуску бенчмарків.

    ---

    ### > _Повертає словник `results` у форматі:_
    - `Рядок для пошуку` :
        - {`Код алгоритму` :
             - {`Патерн` :
                  - {`Мін.час`, `Макс.час`, `Середн.час`, [`Список часу для кожної спроби`], `Позиція підрядка`}
             - }
        - }
    """

    # Лічильний текстів для пошуку підрядка і змінна збору результатів замірів
    text_idx = 0
    results: dict[str, dict[str, dict[str, dict[float, float, float, list[float], int ]]]] = {}

    print(f"{BOLD + CYAN}## Початок замірювання часу роботи алгортимів:{RESET}\n")
    print(f"  {DIM + ITALIC + YELLOW}- Застосовано відключення GC (Garbage Collector) для мінімізації впливу зиміни стану пам'яті на результати замірювань.\n{RESET}")
    for text_key, patterns in DATA.items():
        text_idx += 1
        text = text_key
        results[text_key] = {KMP: {}, BM: {}, RK: {}, PY_FIND: {}, RE_SEARCH: {}}

        text_len = len(text)

        for pat_idx, pattern in enumerate(patterns, start=1):
            pat_len = len(pattern)

            # Warmup виклики
            _ = kmp.search(text, pattern)
            _ = bm.search(text, pattern)
            _ = rk.search(text, pattern)
            _ = _py_find(text, pattern)
            _ = _re_search(text, pattern)

            # Визначаємо number залежно від довжини патерна
            number = _choose_number_for_pattern_length(pat_len)

            # Словник алгоритмів для запуску
            algs: dict[str, Callable[[str, str], int]] = {
                KMP       : kmp.search,
                BM        : bm.search,
                RK        : rk.search,
                PY_FIND   : _py_find,
                RE_SEARCH : _re_search,
            }

            for alg_name, alg_func in algs.items():
                # Перший виклик для отримання позиції (перевірка на оректність)
                pos = alg_func(text, pattern)

                # Вимикаємо GC перед серією замірів
                gc.disable()

                # Готуємо Timer
                timer = timeit.Timer(lambda: alg_func(text, pattern))
                raw_times = timer.repeat(repeat, number)

                # Увімкнути GC і очистити — після серії
                gc.enable()
                gc.collect()

                # Обчислюємо per-call times
                per_call_times: list[float] = [t / number for t in raw_times]

                avg = sum(per_call_times) / len(per_call_times)
                mn = min(per_call_times)
                mx = max(per_call_times)

                # Вивід інформації про пам'ять (ти хотів бачити це прямо після замірів)
                print(BENCHMARK_PROGRESS_TEMPLATE.format(
                    alg_name_placeholder = ALG[alg_name][0],
                    text_idx_placeholder = text_idx,
                    text_len_placeholder = text_len,
                    pat_idx_placeholder  = pat_idx,
                    pat_len_placeholder  = pat_len,
                    stl_placeholder      = ULINE if alg_name == RE_SEARCH else "" # Для розділення підкреслюванням блоків замірювань
                ))

                # Запис у results
                results[text_key][alg_name][pattern] = {
                    "min": mn,
                    "max": mx,
                    "avg": avg,
                    "samples": per_call_times,
                    "pos": pos,
                }

    return results


def format_results_for_print(results: dict) -> list[tuple[str, str, str, int, float, float, float, list[float]]]:
    """Розпаковка results у список кортежів для подальшого форматованого друку.

    Повертає список строкових рядків-рядків або структур, які твій друк-блок
    може форматувати у кольори/ASCII-таблиці.

    Тут лише логіка розпаковки: не форматуємо кольорами — це ти зробиш.
    """
    rows = []
    for text_key, algs in results.items():
        for alg_name, patterns in algs.items():
            for pattern, stats in patterns.items():
                # Тут змінні, які ти можеш використовувати у print-блоці
                text_key_local = text_key
                alg_local      = alg_name
                pat_local      = pattern
                pos_local      = stats.get("pos")
                min_local      = stats.get("min")
                max_local      = stats.get("max")
                avg_local      = stats.get("avg")
                samples_local  = stats.get("samples")

                # Додаємо у результуючий список (ти його форматуватимеш)
                rows.append((text_key_local, alg_local, pat_local, pos_local, min_local, max_local, avg_local, samples_local))
    return rows


if __name__ == "__main__":
    # Налаштування бенчмарку і 'включення' секундоміру
    REPEATS = 20
    time_spent = time.perf_counter()

    """@@@@@@@@@@@@@@@@@@@@@@@@@@"""
    """ Запуск бенчмарків """
    res = launch_benchmark()
    """@@@@@@@@@@@@@@@@@@@@@@@@@@"""

    time_spent = time.perf_counter() - time_spent

    # Розпаковка для друку і сортування результатів для зручності
    rows = format_results_for_print(res)
    rows.sort(key=lambda x: (-len(x[0]), -len(x[2]), ALG[x[1]][1], len(x[2])))

    # Вивід результатів замірів
    print(f"\n\n{BOLD + CYAN}## Результати бенчмарків:{RESET}\n")
    print(f"  {DIM + ITALIC + GREEN}- Кількість повторів для `timeit` = {YELLOW}{REPEATS}{RESET}")
    print(f"  {DIM + ITALIC + GREEN}- Загальний час бенчмарку {YELLOW}{time_spent:.2f}{GREEN} секунд{RESET}")
    print(f"""{DIM + ITALIC + MAGENTA}
За основу текстів взято деякі абзаци зі Статті №1, запропонованої в ДЗ.
Розміри текстів для обробки пошуковими алгоритмами і патернів пошуку вказані в таблиці.
В усіх них обрано 1 невеликий патерн, 1 середній і 1 довгий, які взяті безпосередньо з тексту,
щоб гарантовано знайти ці патерни алгоритмами. Останній патерн створений завідомо таким, якого
в текрсі немає, щоб змусити алгоритми шукати його у всьому зразку.
Дивіться реалізацію у файлі 'data_const.py'.
{RESET}""")

    print(f"| {BOLD}{'Назва алгоритму':^{ALG_NAME_LEN}}{RESET} | {BOLD}Позиція патерну{RESET} | {BOLD}Мінімум{RESET} (с) "
          f"| {BOLD}Максимум{RESET} (С)| {BOLD}Середнє{RESET} (С) | {BOLD}Довжина тексту{RESET} | {BOLD}Довжина підрядка{RESET} |")
    print(f"|{ '-'  *  (ALG_NAME_LEN + 2) }|-----------------|-------------|-------------|-------------|----------------|------------------|")
    data_template = (f"| {{stl_placeholder}}{{alg_name_placeholder}} | {{stl_placeholder}}{{pos_local_placeholder}} "
              f"|  {{stl_placeholder}}{{min_local_placeholder}}  |  {{stl_placeholder}}{{max_local_placeholder}}  |  {{stl_placeholder}}{{avg_local_placeholder}}  "
              f"| {DIM + CYAN}{{stl_placeholder}}{{text_key_local_placeholder:^14,}}{RESET} | {DIM + CYAN}{{stl_placeholder}}{{pat_local_placeholder:^16,}}{RESET} |")

    for r in rows:
        text_key_local, alg_local, pat_local, pos_local, min_local, max_local, avg_local, samples_local = r
        # Форматування значень для виводу
        style     = f"{BOLD}" if ALG[alg_local][1] < 3 else f"{DIM}"
        pos_local = f"{DIM + ITALIC + RED}{'<не знайдено>':^15}{RESET}" if pos_local == -1 else f"{style}{pos_local:^15,}{RESET}"
        min_local = f"{min_local:.6f}" ; min_local = f"{style + GREEN}{min_local[:5]}{DIM}{min_local[5:]}с{RESET}"
        max_local = f"{max_local:.6f}" ; max_local = f"{style + RED  }{max_local[:5]}{DIM}{max_local[5:]}с{RESET}"
        avg_local = f"{avg_local:.6f}" ; avg_local = f"{style + BLUE }{avg_local[:5]}{DIM}{avg_local[5:]}с{RESET}"
        text_key_local = len(text_key_local)
        pat_local = len(pat_local)
        alg_name  = f"{style + MAGENTA}{ALG[alg_local][0]:{ALG_NAME_LEN}}{RESET}"
        print(data_template.format(
            alg_name_placeholder       = alg_name,
            pos_local_placeholder      = pos_local,
            min_local_placeholder      = min_local,
            max_local_placeholder      = max_local,
            avg_local_placeholder      = avg_local,
            text_key_local_placeholder = text_key_local,
            pat_local_placeholder      = pat_local,
            stl_placeholder            = ULINE if ALG[RE_SEARCH][0] in alg_name else "" # Для розділення підкреслюванням блоків замірювань
        ))

    # === ДОДАТКОВІ ПОЯСНЕННЯ ===
    # PS cпроба підсумувати і зробити загальні висновки... трохи недороблена, але можна проаналізувати самостійно з виведеною таблицею 😉
    print(f"\n{DIM + BOLD + GREEN}Назви додаткових вбудованих алгоритмів пошуку приховано темнішим кольором.{RESET}")
    print(f"{DIM + ITALIC + GREEN}Значення замірів добре демонструють швидкість цих алгоритмів проти власної реалізації.")

    # === ВИБІРКА ДАНИХ ===
    # Мінімальна затримка еталонних (вбудованих) алгоритмів
    ref_rows_min = min((r for r in rows if ALG[r[1]][1] > 2), key=lambda r: r[5], default=None)
    ref_time_min = round(ref_rows_min[5], 6)
    ref_info_min = " 😏" if ref_time_min < 2e-6 else ""
    # Максимальна затримка еталонних (вбудованих) алгоритмів
    ref_rows_max = max((r for r in rows if ALG[r[1]][1] > 2), key=lambda r: r[5], default=None)
    ref_time_max = round(ref_rows_max[5], 6)
    ref_info_max = " (що меньше 1 мілісекунди 😎)" if ref_time_max < 1e-3 else ""
    # Мінімальна затримка серед алгоритмів власної реалізації
    alg_rows_min = min((r for r in rows if ALG[r[1]][1] < 3), key=lambda r: r[5], default=None)
    alg_time_min = round(alg_rows_min[5], 6)
    # Максимальна затримка серед алгоритмів власної реалізації
    alg_rows_max = max((r for r in rows if ALG[r[1]][1] < 3), key=lambda r: r[5], default=None)
    alg_time_max = round(alg_rows_max[5], 6)

    print(f"""
Одним з реалізованих власних алгоритмів найшвидше впорався алгоритм '{YELLOW}{ALG[alg_rows_min[1]][0]}{GREEN}'.
Швидкість його роботи з найкращим результатом поміж повторів витратила {YELLOW}{alg_time_min:.6f}{GREEN} сек.
Це було з текстом довжиною {YELLOW}{len(alg_rows_min[0]):,}{GREEN} символів і патерном на {YELLOW}{len(alg_rows_min[2]):,}{GREEN} символів.
Але наймповільнише серед них працював алгоритм '{YELLOW}{ALG[alg_rows_max[1]][0]}{GREEN}' з текстом довжиною {YELLOW}{len(alg_rows_max[0]):,}{GREEN}
символів і патерном на {YELLOW}{len(alg_rows_max[2]):,}{GREEN} символів.

Найдовший витрачений час серед замірів поміж еталонних алгоритмів це {YELLOW}{ref_time_max:.6f}{GREEN} сек.{ref_info_max}, для якого
був застосований метод '{YELLOW}{ALG[ref_rows_max[1]][0]}{GREEN}'. Довжина тексту {YELLOW}{len(ref_rows_max[0]):,}{GREEN} символів і довжина патерну {YELLOW}{len(ref_rows_max[2]):,}{GREEN} символів.

А найшвидше впорався вбудований алгоритм '{YELLOW}{ALG[ref_rows_min[1]][0]}{GREEN}', витративши {YELLOW}{ref_time_min:.6f}{GREEN} сек.{ref_info_min},
опрацювавши текст довжиною {YELLOW}{len(ref_rows_min[0]):,}{GREEN} символів і патерн на {YELLOW}{len(ref_rows_min[2]):,}{GREEN} символів.{RESET}""")