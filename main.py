import networkx as nx
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("Agg")


CLUSTER_EDGES = [(1, 2), (1, 3), (2, 3), (2, 4), (3, 4), (3, 5),
                 (4, 5), (4, 6), (5, 6), (5, 7), (6, 7)]
CLUSTER_SIZE = 7
DRAW_GRAPH = True
CLUSTER_LAYOUT = {1: (-1.5, 0), 2: (-1, 1), 3: (-0.5, 0), 4: (0, 1),
                  5: (0.5, 0), 6: (1, 1), 7: (1.5, 0)}
SPACING_X = 4.5
SPACING_Y = 3


def clusters(m):
    return [(r, c) for r in range(1, m + 1) for c in range(1, m + 1)]

def internal_links(m):
    return [((r, c, u), (r, c, v)) for r, c in clusters(m) for u, v in CLUSTER_EDGES]

def regular_right_links(m):
    """
    Сусід праворуч:
    (r, c, 7) - (r, c+1, 1)
    """
    return [((r, c, 7), (r, c + 1, 1)) for r, c in clusters(m) if c < m]

def regular_down_links(m):
    """
    Сусід знизу:
    (r, c, 1) - (r+1, c, 2)
    """
    return [((r, c, 1), (r + 1, c, 2)) for r, c in clusters(m) if r < m]

def irregular_diagonal_links(m):
    """
    Сусід по діагоналі праворуч знизу:
    (r, c, 7) - (r+1, c+1, 6)
    """
    return [((r, c, 7), (r + 1, c + 1, 6)) for r, c in clusters(m) if r < m and c < m]

def irregular_first_to_last_links(m):
    """
    З'єднання країв решітки (останній стовпець/рядок з першим):
    (r, m, 7) - (r, 1, 1)
    (m, c, 1) - (1, c, 2)
    """
    if m < 3:
        return []
    rows = [((r, m, 7), (r, 1, 1)) for r in range(1, m + 1)]
    cols = [((m, c, 1), (1, c, 2)) for c in range(1, m + 1)]
    return rows + cols


LINK_TYPES = {
    "internal":  (internal_links, "black", "solid"),
    "reg_right": (regular_right_links, "blue",  "solid"),
    "reg_down":  (regular_down_links, "blue",  "solid"),
    "irr_diag":  (irregular_diagonal_links, "green", "dashed"),
    "irr_first_last":  (irregular_first_to_last_links, "red", "dashed"),
}

def build_topology(m):
    G = nx.Graph()
    for r, c in clusters(m):
        for v in range(1, CLUSTER_SIZE + 1):
            G.add_node((r, c, v))

    for kind, (rule, _, _) in LINK_TYPES.items():
        for u, v in rule(m):
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


def cluster_center(r, c):
    return c * SPACING_X, -r * SPACING_Y

def node_positions(G):
    pos = {}
    for (r, c, v) in G.nodes:
        cx, cy = cluster_center(r, c)
        dx, dy = CLUSTER_LAYOUT[v]
        pos[(r, c, v)] = (cx + dx, cy + dy)
    return pos

def draw_topology(G, m, filename):
    pos = node_positions(G)
    plt.figure(figsize=(max(7, 2.5 * m), max(5, 2 * m + 1)))

    for kind, (_, color, style) in LINK_TYPES.items():
        edges = [(u, v) for u, v, t in G.edges(data="kind") if t == kind]
        if not edges:
            continue

        if kind == "irr_first_last":
            # З'єднання йде через усю решітку — дугами, щоб не перекривати кластери:
            # рядки — дугою вниз, стовпці — дугою вліво
            row_edges = [(u, v) for u, v in edges if u[0] == v[0]]
            col_edges = [(u, v) for u, v in edges if u[0] != v[0]]
            for part, rad in [(row_edges, 0.12), (col_edges, 0.35)]:
                nx.draw_networkx_edges(G, pos, edgelist=part, edge_color=color,
                                       style=style, width=1.25, arrows=True,
                                       arrowstyle="-",
                                       connectionstyle=f"arc3,rad={rad}")
        else:
            nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color=color,
                                   style=style, width=1.5)

    nx.draw_networkx_nodes(G, pos, node_size=230, node_color="white",
                           edgecolors="black")
    nx.draw_networkx_labels(G, pos, labels={(r, c, v): v for r, c, v in G.nodes},
                            font_size=7)
    for r, c in clusters(m):
        cx, cy = cluster_center(r, c)
        plt.text(cx, cy - 0.5, f"К({r},{c})", ha="center", va="center",
                 fontsize=8, fontweight="bold", color="gray")

    plt.plot([], [], color="black", label="внутрішні")
    plt.plot([], [], color="blue", label="регулярні вниз (r,c,1)-(r+1,c,2), праворуч (r,c,7)-(r,c+1,1)")
    plt.plot([], [], color="green", ls="--", label="нерегулярні діагональ (r,c,7)-(r+1,c+1,6)")
    plt.plot([], [], color="red", ls="--", label="нерегулярні замикання (r,1,1)-(r,m,7), (1,c,2)-(m,c,1)")
    plt.legend(loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2,
               fontsize=8, frameon=False)
    plt.title(f"Решітка {m}×{m}: n = {m * m} кластерів, N = {G.number_of_nodes()}")
    plt.axis("off")
    plt.axis("equal")
    plt.tight_layout()
    plt.savefig(filename, dpi=130, bbox_inches="tight")
    plt.close()


def main():
    try:
        m = int(input("Введіть розмір решітки m (решітка m×m кластерів): "))
        if m < 1:
            raise ValueError
    except ValueError:
        print("Помилка: m має бути цілим числом >= 1")
        return

    G = build_topology(m)
    r = characteristics(G)

    print(f"\nРезультати для решітки {m}×{m} (n = {m * m} кластерів):")
    print(f"  N  (кількість процесорів) = {r['N']}")
    print(f"  S  (ступінь)              = {r['S']}")
    print(f"  D  (діаметр)              = {r['D']}")
    print(f"  D̄  (середній діаметр)     = {r['D_avg']:.3f}")
    print(f"  C  (вартість, C = E)      = {r['C']}")
    print(f"  T  (топологічний трафік)  = {r['T']:.3f}")

    if DRAW_GRAPH and m <= 5:
        filename = f"graph_m{m}.png"
        draw_topology(G, m, filename)
        print(f"\nМалюнок графа збережено: {filename}")

if __name__ == "__main__":
    main()