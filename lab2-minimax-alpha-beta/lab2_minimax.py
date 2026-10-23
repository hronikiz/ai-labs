"""
Лабораторная работа №2. Вариант 19.
Глубина 6, ширина 3, значения листьев [0; 40].
Эксперимент: случайная перестановка потомков - 10 запусков, разброс числа узлов.

Допущения:
  * глубина 6 = 6 уровней рёбер: корень (уровень 0) и 6 уровней потомков,
    листья лежат на уровне 6 -> 3^6 = 729 листьев, 1093 узла всего;
  * корень - MAX, уровни чередуются MAX, MIN, MAX, MIN, MAX, MIN;
  * "посещённый узел" = любой вызов функции (и внутренний узел, и лист);
  * "отсечение" = одно срабатывание условия beta <= alpha (остальные потомки узла не смотрятся).

Запуск:  python lab2_minimax.py
Создаёт: lab2_results.csv, lab2_chart.png
"""
import csv
import random
import statistics
import time

DEPTH = 6
WIDTH = 3
LO, HI = 0, 40
TREE_SEED = 19
RUNS = 10
TIMING_REPEATS = 200


def build_tree(depth, width, lo, hi, rng):
    if depth == 0:
        return rng.randint(lo, hi)
    return [build_tree(depth - 1, width, lo, hi, rng) for _ in range(width)]


def shuffled(tree, rng):
    """Копия дерева со случайно переставленными потомками в КАЖДОМ узле."""
    if isinstance(tree, int):
        return tree
    kids = [shuffled(c, rng) for c in tree]
    rng.shuffle(kids)
    return kids


# Счётчики
class Stats:
    __slots__ = ("nodes", "leaves", "cutoffs", "cut_max", "cut_min")

    def __init__(self):
        self.nodes = self.leaves = self.cutoffs = self.cut_max = self.cut_min = 0


# Обычный мини-макс
def minimax(node, is_max, st):
    """Возвращает (значение, путь из индексов потомков)."""
    st.nodes += 1
    if isinstance(node, int):
        st.leaves += 1
        return node, []
    best_val = float("-inf") if is_max else float("inf")
    best_path = []
    for i, child in enumerate(node):
        val, path = minimax(child, not is_max, st)
        if (is_max and val > best_val) or (not is_max and val < best_val):
            best_val, best_path = val, [i] + path
    return best_val, best_path



# Мини-макс с альфа-бета отсечением (рекурсивно)
def alphabeta(node, is_max, alpha, beta, st):
    st.nodes += 1
    if isinstance(node, int):
        st.leaves += 1
        return node, []
    best_path = []
    if is_max:
        best_val = float("-inf")
        for i, child in enumerate(node):
            val, path = alphabeta(child, False, alpha, beta, st)
            if val > best_val:
                best_val, best_path = val, [i] + path
            alpha = max(alpha, best_val)
            if beta <= alpha:
                st.cutoffs += 1
                st.cut_max += 1
                break
    else:
        best_val = float("inf")
        for i, child in enumerate(node):
            val, path = alphabeta(child, True, alpha, beta, st)
            if val < best_val:
                best_val, best_path = val, [i] + path
            beta = min(beta, best_val)
            if beta <= alpha:
                st.cutoffs += 1
                st.cut_min += 1
                break
    return best_val, best_path


def leaf_at(tree, path):
    for i in path:
        tree = tree[i]
    return tree


def timed(fn, repeats=TIMING_REPEATS):
    t0 = time.perf_counter()
    for _ in range(repeats):
        fn()
    return (time.perf_counter() - t0) / repeats * 1000.0  # мс


def measure(tree):
    """Один замер на одном дереве: оба алгоритма, счётчики, время, проверка корректности."""
    s1, s2 = Stats(), Stats()
    v1, p1 = minimax(tree, True, s1)
    v2, p2 = alphabeta(tree, True, float("-inf"), float("inf"), s2)
    assert v1 == v2, f"значения корня не совпали: {v1} != {v2}"
    assert leaf_at(tree, p1) == v1 and leaf_at(tree, p2) == v2, "путь не ведёт к значению корня"
    t1 = timed(lambda: minimax(tree, True, Stats()))
    t2 = timed(lambda: alphabeta(tree, True, float("-inf"), float("inf"), Stats()))
    return dict(value=v1, path_mm=p1, path_ab=p2, nodes_mm=s1.nodes, nodes_ab=s2.nodes,
                leaves_ab=s2.leaves, cutoffs=s2.cutoffs, cut_max=s2.cut_max, cut_min=s2.cut_min,
                t_mm=t1, t_ab=t2)


def main():
    base = build_tree(DEPTH, WIDTH, LO, HI, random.Random(TREE_SEED))
    total_nodes = sum(WIDTH ** d for d in range(DEPTH + 1))
    total_leaves = WIDTH ** DEPTH
    # Теоретический минимум листьев при идеальном порядке: b^ceil(d/2) + b^floor(d/2) - 1
    min_leaves = WIDTH ** ((DEPTH + 1) // 2) + WIDTH ** (DEPTH // 2) - 1

    rows = []
    r = measure(base)
    r["label"] = "исходный порядок (seed=19)"
    rows.append(r)

    for run in range(1, RUNS + 1):
        rng = random.Random(1000 + run)
        r = measure(shuffled(base, rng))
        r["label"] = f"перестановка #{run} (seed={1000 + run})"
        rows.append(r)

    # Вывод таблицы 
    print(f"Дерево: глубина {DEPTH}, ширина {WIDTH}, значения [{LO};{HI}], "
          f"узлов всего {total_nodes}, листьев {total_leaves}\n")
    head = ("| Условие эксперимента | Узлов (мини-макс) | Узлов (α-β) | Листьев (α-β) | Отсечений | "
            "Время мини-макс, мс | Время α-β, мс | Значение корня |")
    print(head)
    print("|" + "|".join(["---"] * 8) + "|")
    for r in rows:
        print(f"| {r['label']} | {r['nodes_mm']} | {r['nodes_ab']} | {r['leaves_ab']} | {r['cutoffs']} | "
              f"{r['t_mm']:.3f} | {r['t_ab']:.3f} | {r['value']} |")

    perm = rows[1:]
    nodes = [r["nodes_ab"] for r in perm]
    cuts = [r["cutoffs"] for r in perm]
    leaves = [r["leaves_ab"] for r in perm]
    t_ab = [r["t_ab"] for r in perm]
    saving = [(1 - r["nodes_ab"] / r["nodes_mm"]) * 100 for r in perm]

    print("\nСводка по 10 случайным перестановкам (α-β):")
    print(f"  узлов:     min={min(nodes)}  max={max(nodes)}  среднее={statistics.mean(nodes):.1f}  "
          f"ст.откл.={statistics.pstdev(nodes):.1f}  размах={max(nodes) - min(nodes)}")
    print(f"  листьев:   min={min(leaves)}  max={max(leaves)}  среднее={statistics.mean(leaves):.1f}")
    print(f"  отсечений: min={min(cuts)}  max={max(cuts)}  среднее={statistics.mean(cuts):.1f}")
    print(f"  время, мс: min={min(t_ab):.3f}  max={max(t_ab):.3f}  среднее={statistics.mean(t_ab):.3f}")
    print(f"  экономия узлов: min={min(saving):.1f}%  max={max(saving):.1f}%  среднее={statistics.mean(saving):.1f}%")
    print(f"  мини-макс всегда: {rows[0]['nodes_mm']} узлов (из {total_nodes}); "
          f"теор. минимум листьев при идеальном порядке: {min_leaves} из {total_leaves}")
    cm = sum(r["cut_max"] for r in perm) / len(perm)
    cn = sum(r["cut_min"] for r in perm) / len(perm)
    print(f"  отсечений в среднем: на уровнях MAX {cm:.1f}, на уровнях MIN {cn:.1f}")

    b = rows[0]
    print("\nОптимальный путь (исходное дерево), индексы потомков с 0 от корня:")
    print(f"  мини-макс: {b['path_mm']} -> лист {leaf_at(base, b['path_mm'])}")
    print(f"  α-β:       {b['path_ab']} -> лист {leaf_at(base, b['path_ab'])}")
    print(f"  значение корня = {b['value']}; уровни: " +
          " -> ".join(f"{'MAX' if i % 2 == 0 else 'MIN'}({p})" for i, p in enumerate(b['path_mm'])) + " -> лист")

    # CSV
    with open("lab2_results.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Условие эксперимента", "Узлов (мини-макс)", "Узлов (альфа-бета)", "Листьев (альфа-бета)",
                    "Отсечений", "Время мини-макс, мс", "Время альфа-бета, мс", "Значение корня"])
        for r in rows:
            w.writerow([r["label"], r["nodes_mm"], r["nodes_ab"], r["leaves_ab"], r["cutoffs"],
                        f"{r['t_mm']:.4f}", f"{r['t_ab']:.4f}", r["value"]])

    # График
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    xs = list(range(1, RUNS + 1))
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(xs, nodes, color="#4c78a8", label="Альфа-бета")
    ax.axhline(rows[0]["nodes_mm"], color="#e45756", ls="--", label=f"Мини-макс ({rows[0]['nodes_mm']} узлов)")
    ax.axhline(statistics.mean(nodes), color="#222", ls=":", label=f"Среднее α-β ({statistics.mean(nodes):.0f})")
    for x, n in zip(xs, nodes):
        ax.text(x, n + 8, str(n), ha="center", fontsize=9)
    ax.set_xticks(xs)
    ax.set_xlabel("Номер запуска (случайная перестановка потомков)")
    ax.set_ylabel("Число посещённых узлов")
    ax.set_title("Вариант 19: разброс числа узлов при случайном порядке потомков")
    ax.set_ylim(0, rows[0]["nodes_mm"] * 1.12)
    ax.legend()
    fig.tight_layout()
    fig.savefig("lab2_chart.png", dpi=150)


if __name__ == "__main__":
    main()
