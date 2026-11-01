import networkx as nx
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("Agg")


CLUSTER_EDGES = [(1, 2), (1, 3), (2, 4), (3, 5), (4, 6), (5, 6), (6, 7), (6, 8), (7, 8)]
CLUSTER_SIZE = 8
DRAW_GRAPH = True
CLUSTER_LAYOUT = {1: (0, 3), 2: (-1, 2), 3: (1, 2), 4: (-1, 1),
                  5: (1, 1), 6: (0, 0), 7: (-1, -1), 8: (1, -1)}
CLUSTER_SPACING = 4


def internal_links(n):
    return [((a, u), (a, v)) for a in range(n) for u, v in CLUSTER_EDGES]

def regular_links(n):
    """
    (a, 3) - (a+1, 2)
    (a, 5) - (a+1, 4)
    (a, 8) - (a+1, 7)
    """
    pairs = [(3, 2), (5, 4), (8, 7)]
    return [((a, u), (a + 1, v)) for a in range(n - 1) for u, v in pairs]

def irregular_skip_links(n):
    """
    a + k, де k = 2
    (a, 1) - (a+k, 1)
    """
    k = 2
    return [((a, 1), (a + k, 1)) for a in range(n - k)]

def irregular_half_links(n):
    """
    a + h, де h = n // 2:
    (a, 8) - (a+h, 7)
    """
    h = n // 2
    if h < 2:
        return []
    return [((a, 8), (a + h, 7)) for a in range(n - h)]


LINK_TYPES = {
    "internal":  (internal_links, "black", "solid"),
    "regular":   (regular_links, "blue",  "solid"),
    "irr_skip":  (irregular_skip_links, "green", "dashed"),
    "irr_half":  (irregular_half_links, "red",   "dashed"),
}

def build_topology(n):
    G = nx.Graph()
    for a in range(n):
        for v in range(1, CLUSTER_SIZE + 1):
            G.add_node((a, v))

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


def node_positions(G):
    return {(a, v): (a * CLUSTER_SPACING + x, y)
            for (a, v) in G.nodes
            for x, y in [CLUSTER_LAYOUT[v]]}

def draw_topology(G, n, filename):
    pos = node_positions(G)
    plt.figure(figsize=(min(max(6, 2.2 * n), 40), 10))

    for kind, (_, color, style) in LINK_TYPES.items():
        edges = [(u, v) for u, v, k in G.edges(data="kind") if k == kind]
        if not edges:
            continue

        if kind.startswith("irr"):
            rad = -0.35 if kind == "irr_skip" else 0.25
            nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color=color,
                                   style=style, width=1.6, arrows=True,
                                   arrowstyle="-",
                                   connectionstyle=f"arc3,rad={rad}")
        else:
            nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color=color,
                                   style=style, width=1.6)

    nx.draw_networkx_nodes(G, pos, node_size=330, node_color="white",
                           edgecolors="black")
    nx.draw_networkx_labels(G, pos, labels={(a, v): v for a, v in G.nodes},
                            font_size=8)
    for a in range(n):
        plt.text(a * CLUSTER_SPACING, 1.5, f"К{a}", ha="center", va="center",
                 fontsize=11, fontweight="bold", color="gray")

    plt.plot([], [], color="black", label="внутрішні")
    plt.plot([], [], color="blue", label="регулярні (a,3)-(a+1,2), (a,5)-(a+1,4), (a,8)-(a+1,7)")
    plt.plot([], [], color="green", ls="--", label=f"нерегулярні (a,1)-(a+2,1)")
    plt.plot([], [], color="red", ls="--", label="нерегулярні (a,8)-(a+n//2,7)")
    plt.legend(loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2,
               fontsize=8, frameon=False)
    plt.title(f"Лінійна топологія: n = {n} кластерів, N = {G.number_of_nodes()}")
    plt.axis("off")
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

    print(f"\nРезультати для n = {n} кластерів:")
    print(f"  N  (кількість процесорів) = {r['N']}")
    print(f"  S  (ступінь)              = {r['S']}")
    print(f"  D  (діаметр)              = {r['D']}")
    print(f"  D̄  (середній діаметр)     = {r['D_avg']:.3f}")
    print(f"  C  (вартість, C = E)      = {r['C']}")
    print(f"  T  (топологічний трафік)  = {r['T']:.3f}")

    if DRAW_GRAPH and n <= 15:
        filename = f"graph_n{n}.png"
        draw_topology(G, n, filename)
        print(f"\nМалюнок графа збережено: {filename}")


if __name__ == "__main__":
    main()