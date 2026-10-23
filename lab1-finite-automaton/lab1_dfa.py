"""
Лабораторная работа №1. Вариант 19.
Язык: a^n (bc)^m (de)^k,  n >= 1, m >= 1, k >= 1, m - нечётное.

Эквивалентное регулярное выражение:  a+ bc (bcbc)* (de)+
(m = 1 + 2j  <=>  m нечётное и m >= 1)

Запуск:
    python lab1_dfa.py            # тесты + интерактивный режим
    python lab1_dfa.py abcde      # проверить одно слово
"""
import itertools
import re
import sys

ALPHABET = "abcde"

# ----------------------------------------------------------------------
# Детерминированный конечный автомат
# ----------------------------------------------------------------------
# q0 - начальное состояние
# q1 - прочитано a^n, n >= 1
# q2 - прочитано ...b, число блоков bc станет НЕЧЁТНЫМ (ждём c)
# q3 - прочитано (bc)^m, m нечётно  (можно b или d)
# q4 - прочитано ...b, число блоков bc станет ЧЁТНЫМ (ждём c)
# q5 - прочитано (bc)^m, m чётно    (можно только b)
# q6 - прочитано ...d (ждём e)
# q7 - прочитано (de)^k, k >= 1     (ЗАКЛЮЧИТЕЛЬНОЕ; можно d)
# TRAP - ловушка (недопустимое слово)
START = "q0"
ACCEPTING = {"q7"}
TRAP = "TRAP"

DELTA = {
    "q0": {"a": "q1"},
    "q1": {"a": "q1", "b": "q2"},
    "q2": {"c": "q3"},
    "q3": {"b": "q4", "d": "q6"},
    "q4": {"c": "q5"},
    "q5": {"b": "q2"},
    "q6": {"e": "q7"},
    "q7": {"d": "q6"},
}


def step(state: str, symbol: str) -> str:
    """Функция переходов delta(state, symbol). Все не заданные переходы ведут в ловушку."""
    if state == TRAP:
        return TRAP
    return DELTA.get(state, {}).get(symbol, TRAP)


def run(word: str, trace: bool = False):
    """Прогоняет слово через автомат. Возвращает (принято?, путь по состояниям)."""
    state = START
    path = [state]
    for ch in word:
        state = step(state, ch)
        path.append(state)
        if state == TRAP:
            break
    accepted = state in ACCEPTING
    return (accepted, path) if trace else accepted

_PARSE = re.compile(r"^(a+)((?:bc)+)((?:de)+)$")


def oracle(word: str) -> bool:
    """Разбирает слово на n, m, k и проверяет условия варианта напрямую."""
    mt = _PARSE.match(word)
    if not mt:
        return False
    n = len(mt.group(1))
    m = len(mt.group(2)) // 2
    k = len(mt.group(3)) // 2
    return n >= 1 and m >= 1 and k >= 1 and m % 2 == 1


def make(n: int, m: int, k: int) -> str:
    return "a" * n + "bc" * m + "de" * k


# Тесты
VALID = [
    make(1, 1, 1),          # abcde (минимум)
    make(5, 1, 1),          # aaaaabcde
    make(1, 3, 1),          # m = 3 (нечётное)
    make(2, 5, 4),          # m = 5, k = 4
    make(10, 7, 10),        # большие степени
    make(1000, 1001, 1000), # длинное слово
]

INVALID = [
    ("",                 "пустое слово"),
    ("a",                "только a"),
    ("abc",              "нет блока (de)"),
    ("bcde",             "нет начального a (n = 0)"),
    ("abcdd",            "после d нет e"),
    ("abcd",             "обрывается на d"),
    ("ade",              "нет блока (bc), m = 0"),
    (make(1, 2, 1),      "m = 2 - чётное"),
    (make(3, 4, 2),      "m = 4 - чётное"),
    (make(1, 1, 0),      "k = 0"),
    ("abcdea",           "a после (de)"),
    ("abcdebc",          "(bc) после (de) - нарушен порядок"),
    ("abcbde",           "b d вместо bc"),
    ("abbcde",           "лишняя b"),
    ("abccde",           "лишняя c"),
    ("aabcdee",          "лишняя e"),
    ("abcdeabcde",       "блоки повторены целиком"),
    ("acde",             "нет b"),
    ("abcde!",           "посторонний символ"),
    ("abxcde",           "посторонний символ внутри"),
    ("ABCDE",            "другой регистр"),
    ("abcde ",           "пробел в конце"),
]


def run_tests() -> bool:
    ok = True
    print("=== Корректные слова (ожидается: принято) ===")
    for w in VALID:
        res = run(w)
        shown = w if len(w) <= 30 else w[:12] + "..." + w[-12:] + f" (длина {len(w)})"
        print(f"  {'OK ' if res else 'ОШИБКА'} {shown!r:50} -> {'принято' if res else 'отвергнуто'}")
        ok &= res

    print("\n=== Некорректные слова (ожидается: отвергнуто) ===")
    for w, why in INVALID:
        res = run(w)
        print(f"  {'OK ' if not res else 'ОШИБКА'} {w!r:16} {why:38} -> {'принято' if res else 'отвергнуто'}")
        ok &= not res

    # Полный перебор: все слова длины 0..9 над алфавитом {a,b,c,d,e}
    print("\n=== Сверка с эталоном: полный перебор слов длины 0..9 ===")
    total = accepted = 0
    for length in range(0, 10):
        for tup in itertools.product(ALPHABET, repeat=length):
            w = "".join(tup)
            r1, r2 = run(w), oracle(w)
            total += 1
            accepted += r1
            if r1 != r2:
                print(f"  РАСХОЖДЕНИЕ на слове {w!r}: автомат={r1}, эталон={r2}")
                ok = False
    print(f"  проверено слов: {total}, из них принято: {accepted}")

    # Все допустимые комбинации (n, m, k) и их ближайшие нарушители
    print("\n=== Сетка параметров n, m, k = 0..6 ===")
    bad = 0
    for n, m, k in itertools.product(range(7), repeat=3):
        expected = n >= 1 and m >= 1 and k >= 1 and m % 2 == 1
        if run(make(n, m, k)) != expected:
            bad += 1
            print(f"  ошибка при (n,m,k) = {(n, m, k)}")
    print(f"  расхождений: {bad}")
    ok &= bad == 0

    print("\nИТОГ:", "все тесты пройдены" if ok else "ЕСТЬ ОШИБКИ")
    return ok


def print_table():
    print("Таблица переходов:")
    print(f"{'':6}" + "".join(f"{c:>7}" for c in ALPHABET))
    for s in list(DELTA) + [TRAP]:
        row = "".join(f"{step(s, c):>7}" for c in ALPHABET)
        mark = ("->" if s == START else "  ") + ("*" if s in ACCEPTING else " ")
        print(f"{mark}{s:4}" + row)


def main():
    if len(sys.argv) > 1:
        for w in sys.argv[1:]:
            acc, path = run(w, trace=True)
            print(f"{w!r}: {'принадлежит' if acc else 'НЕ принадлежит'} языку   путь: {' -> '.join(path)}")
        return
    print_table()
    print()
    run_tests()
    print("\nИнтерактивный режим (пустая строка - выход, слово из одного символа '-' = пустое слово)")
    while True:
        try:
            w = input("слово> ")
        except EOFError:
            break
        if w == "":
            break
        w = "" if w == "-" else w
        acc, path = run(w, trace=True)
        print(f"  {'принадлежит' if acc else 'НЕ принадлежит'} языку   путь: {' -> '.join(path)}")


if __name__ == "__main__":
    main()
