import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
import math


CLUSTER_EDGES = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 1),
                 (1, 5), (2, 6), (3, 7), (4, 8)]
CLUSTER_SIZE = 8
DRAW_GRAPH = True
CLUSTER_LAYOUT = {v: (math.cos(math.radians(90 - 45 * (v - 1))),
                      math.sin(math.radians(90 - 45 * (v - 1))))
                  for v in range(1, CLUSTER_SIZE + 1)}
CLUSTER_SPACING = 3.5
LEVEL_GAP = 4.5


def level(k):
    return int(math.log2(k))

def internal_links(n):
    return [((k, u), (k, v)) for k in range(1, n + 1) for u, v in CLUSTER_EDGES]

def regular_links(n):
    """
    Батько кластера c: p = c // 2
    ліва дитина  (c парне):   (p, 7) - (c, 8),  (p, 6) - (c, 2)
    права дитина (c непарне): (p, 4) - (c, 8),  (p, 3) - (c, 2)
    """
    edges = []
    for c in range(2, n + 1):
        p = c // 2
        if c % 2 == 0:
            edges += [((p, 7), (c, 8)), ((p, 6), (c, 2))]
        else:
            edges += [((p, 4), (c, 8)), ((p, 3), (c, 2))]
    return edges

def same_level_links(n, node, part):
    edges = []
    for k in range(1, n + 1):
        size = 2 ** level(k)
        step = size // part
        if step == 0:
            continue
        pos = k - size  # позиція кластера в рівні: 0, 1, 2, ...
        if pos % (2 * step) < step and k + step <= n:
            edges.append(((k, node), (k + step, node)))
    return edges


def irregular_half_links(n):
    """
    step = половина рівня
    (k, 5) - (k + step, 5)
    """
    return same_level_links(n, node=5, part=2)


def irregular_quarter_links(n):
    """
    step = чверть рівня
    (k, 1) - (k + step, 1)
    """
    return same_level_links(n, node=1, part=4)


LINK_TYPES = {
    "internal": (internal_links, "black", "solid"),
    "regular": (regular_links, "blue", "solid"),
    "irr_half": (irregular_half_links, "green", "dashed"),
    "irr_quarter": (irregular_quarter_links, "red", "dashed"),
}


def build_topology(n):
    G = nx.Graph()
    for k in range(1, n + 1):
        for v in range(1, CLUSTER_SIZE + 1):
            G.add_node((k, v))

    for kind, (rule, _, _) in LINK_TYPES.items():
        for u, v in rule(n):
            if G.has_edge(u, v):
                continue
            G.add_edge(u, v, kind=kind)
    return G


def characteristics(G):
    """
    N  — кількість процесорів (вершин)
    E  — кількість зв'язків (ребер)
    S  — ступінь: максимальна кількість ребер, інцидентних одній вершині
    D  — діаметр: найбільша з найкоротших відстаней між вершинами
    D̄  — середній діаметр: середня найкоротша відстань між усіма парами
    C  — вартість, C = E
    T  — топологічний трафік, T = N * D̄ / E
    """
    N = G.number_of_nodes()
    E = G.number_of_edges()
    S = max(deg for _, deg in G.degree())
    D = nx.diameter(G)
    D_avg = nx.average_shortest_path_length(G)
    C = E
    T = N * D_avg / E
    return {"N": N, "S": S, "D": D, "D_avg": D_avg, "C": C, "T": T}


def cluster_center(k, n):
    """
    Рівень дерева — це рядок малюнка (корінь зверху).
    Кластери рівня рівномірно ділять ширину нижнього рівня.
    """
    size = 2 ** level(k)  # кластерів на рівні
    pos = k - size  # позиція в рівні
    width = 2 ** level(n) * CLUSTER_SPACING  # ширина нижнього рівня
    x = (pos + 0.5) * width / size
    y = -level(k) * LEVEL_GAP
    return x, y


def node_positions(G, n):
    pos = {}
    for (k, v) in G.nodes:
        cx, cy = cluster_center(k, n)
        dx, dy = CLUSTER_LAYOUT[v]
        pos[(k, v)] = (cx + dx, cy + dy)
    return pos


def draw_topology(G, n, filename):
    pos = node_positions(G, n)
    width = min(max(8, 2 ** level(n) * 1.6), 40)
    height = max(5, (level(n) + 1) * 2.4)
    plt.figure(figsize=(width, height))

    for kind, (_, color, style) in LINK_TYPES.items():
        edges = [(u, v) for u, v, t in G.edges(data="kind") if t == kind]
        if not edges:
            continue

        if kind.startswith("irr"):
            rad = 0.12 if kind == "irr_half" else -0.12
            nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color=color,
                                   style=style, width=1.4, arrows=True,
                                   arrowstyle="-",
                                   connectionstyle=f"arc3,rad={rad}")
        else:
            nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color=color,
                                   style=style, width=1.4)

    nx.draw_networkx_nodes(G, pos, node_size=260, node_color="white",
                           edgecolors="black")
    nx.draw_networkx_labels(G, pos, labels={(k, v): v for k, v in G.nodes},
                            font_size=7)
    for k in range(1, n + 1):
        cx, cy = cluster_center(k, n)
        plt.text(cx, cy, f"К{k}", ha="center", va="center", fontsize=8,
                 fontweight="bold", color="gray",
                 bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"))

    plt.plot([], [], color="black", label="внутрішні")
    plt.plot([], [], color="blue", label="регулярні: ліва дитина (p,7)-(c,8), (p,6)-(c,2); "
                                         "права дитина (p,4)-(c,8), (p,3)-(c,2)")
    plt.plot([], [], color="green", ls="--", label="нерегулярні (k,5)-(k+пів рівня,5)")
    plt.plot([], [], color="red", ls="--", label="нерегулярні (k,1)-(k+чверть рівня,1)")
    plt.legend(loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2,
               fontsize=8, frameon=False)
    plt.title(f"Деревоподібна топологія: n = {n} кластерів, N = {G.number_of_nodes()}")
    plt.axis("off")
    plt.axis("equal")
    plt.tight_layout()
    plt.savefig(filename, dpi=130, bbox_inches="tight")
    plt.close()


def main():
    try:
        n = int(input("Введіть кількість кластерів n: "))
        if n < 1:
            raise ValueError
    except ValueError:
        print("Помилка: n має бути цілим числом >= 1")
        return

    G = build_topology(n)
    r = characteristics(G)

    print(f"\nРезультати для n = {n} кластерів (рівнів дерева: {level(n) + 1}):")
    print(f"  N  (кількість процесорів) = {r['N']}")
    print(f"  S  (ступінь)              = {r['S']}")
    print(f"  D  (діаметр)              = {r['D']}")
    print(f"  D̄  (середній діаметр)     = {r['D_avg']:.3f}")
    print(f"  C  (вартість, C = E)      = {r['C']}")
    print(f"  T  (топологічний трафік)  = {r['T']:.3f}")

    if DRAW_GRAPH:
        filename = f"graph_n{n}.png"
        draw_topology(G, n, filename)
        print(f"\nМалюнок графа збережено: {filename}")


if __name__ == "__main__":
    main()
