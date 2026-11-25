# Mini-Courier Planner - DAA Capstone

import heapq
import random
import sys
import time

CAPACITY = 50   # van capacity in kg
DEPOT = 0       # depot is node 0

# parcels: id, destination, weight, priority, deadline
parcels = [
    {"id": "P01", "dest": 3, "weight": 12, "priority": 8,  "deadline": 4},
    {"id": "P02", "dest": 5, "weight": 7,  "priority": 5,  "deadline": 6},
    {"id": "P03", "dest": 2, "weight": 15, "priority": 9,  "deadline": 2},
    {"id": "P04", "dest": 8, "weight": 10, "priority": 6,  "deadline": 8},
    {"id": "P05", "dest": 6, "weight": 5,  "priority": 3,  "deadline": 10},
    {"id": "P06", "dest": 3, "weight": 9,  "priority": 7,  "deadline": 4},
    {"id": "P07", "dest": 9, "weight": 20, "priority": 10, "deadline": 3},
    {"id": "P08", "dest": 4, "weight": 6,  "priority": 4,  "deadline": 9},
    {"id": "P09", "dest": 7, "weight": 8,  "priority": 6,  "deadline": 5},
    {"id": "P10", "dest": 1, "weight": 11, "priority": 5,  "deadline": 7},
    {"id": "P11", "dest": 5, "weight": 14, "priority": 8,  "deadline": 6},
    {"id": "P12", "dest": 8, "weight": 4,  "priority": 2,  "deadline": 12},
]

# roads: (from, to, distance in km)
roads = [
    (0, 1, 4), (0, 2, 3), (0, 3, 7), (1, 2, 2), (1, 4, 5),
    (2, 3, 4), (2, 5, 6), (3, 6, 3), (4, 5, 2), (4, 7, 6),
    (5, 6, 4), (5, 8, 5), (6, 9, 5), (7, 8, 3), (8, 9, 4),
]


# ---------------- graph ----------------

def build_graph(road_list):
    # graph is a dictionary: node -> list of (neighbour, distance)
    graph = {}
    for a, b, d in road_list:
        if a not in graph:
            graph[a] = []
        if b not in graph:
            graph[b] = []
        graph[a].append((b, d))
        graph[b].append((a, d))
    return graph


# ---------------- sorting ----------------

def key(p):
    # earliest deadline first, if same deadline then higher priority first
    return (p["deadline"], -p["priority"])


def merge(left, right):
    result = []
    i = 0
    j = 0
    while i < len(left) and j < len(right):
        if key(left[i]) <= key(right[j]):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result = result + left[i:] + right[j:]
    return result


def merge_sort(items):
    if len(items) <= 1:
        return items
    mid = len(items) // 2
    left = merge_sort(items[:mid])
    right = merge_sort(items[mid:])
    return merge(left, right)


def bubble_sort(items):
    # slow O(n^2) sort, only used to compare with merge sort in the benchmark
    arr = items[:]
    n = len(arr)
    for i in range(n - 1):
        for j in range(n - 1 - i):
            if key(arr[j]) > key(arr[j + 1]):
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


# ---------------- knapsack (dp) ----------------

def knapsack(items, capacity):
    n = len(items)
    # table[i][w] = best priority using first i parcels with capacity w
    table = []
    for i in range(n + 1):
        table.append([0] * (capacity + 1))

    for i in range(1, n + 1):
        weight = items[i - 1]["weight"]
        value = items[i - 1]["priority"]
        for w in range(capacity + 1):
            if weight > w:
                table[i][w] = table[i - 1][w]
            else:
                skip = table[i - 1][w]
                take = table[i - 1][w - weight] + value
                table[i][w] = max(skip, take)

    # go back through the table to find which parcels were taken
    chosen = []
    w = capacity
    for i in range(n, 0, -1):
        if table[i][w] != table[i - 1][w]:
            chosen.append(items[i - 1])
            w = w - items[i - 1]["weight"]
    chosen.reverse()

    return table[n][capacity], chosen, table


# ---------------- dijkstra ----------------

def dijkstra(graph, start):
    dist = {}
    prev = {}
    for node in graph:
        dist[node] = float("inf")
        prev[node] = None
    dist[start] = 0

    heap = [(0, start)]
    while len(heap) > 0:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in graph[u]:
            if d + w < dist[v]:
                dist[v] = d + w
                prev[v] = u
                heapq.heappush(heap, (dist[v], v))
    return dist, prev


def get_path(prev, target):
    path = []
    node = target
    while node is not None:
        path.append(node)
        node = prev[node]
    path.reverse()
    return path


# ---------------- tsp (nearest neighbour) ----------------

def nearest_neighbour(graph, depot, stops):
    remaining = [s for s in stops if s != depot]
    current = depot
    order = [depot]
    full_path = [depot]
    total = 0

    while len(remaining) > 0:
        dist, prev = dijkstra(graph, current)
        # pick the closest stop that is still left
        closest = remaining[0]
        for s in remaining:
            if dist[s] < dist[closest]:
                closest = s
        total += dist[closest]
        full_path += get_path(prev, closest)[1:]
        order.append(closest)
        remaining.remove(closest)
        current = closest

    # back to depot
    dist, prev = dijkstra(graph, current)
    total += dist[depot]
    full_path += get_path(prev, depot)[1:]
    order.append(depot)

    return order, total, full_path


# ---------------- printing ----------------

def print_parcels(title, items):
    print("\n" + title)
    print("ID    Dest  Wt  Prio  Deadline")
    for p in items:
        print(p["id"].ljust(6) + str(p["dest"]).ljust(6) + str(p["weight"]).ljust(4)
              + str(p["priority"]).ljust(6) + str(p["deadline"]))


def print_table(items, table, capacity):
    # only every 5th column so it fits on the screen
    cols = list(range(0, capacity + 1, 5))
    print("parcel".ljust(9) + "".join(("w=" + str(c)).rjust(6) for c in cols))
    for i in range(len(table)):
        name = "(none)" if i == 0 else items[i - 1]["id"]
        print(name.ljust(9) + "".join(str(table[i][c]).rjust(6) for c in cols))


# ---------------- demo ----------------

def demo():
    graph = build_graph(roads)
    print("=" * 55)
    print("MINI-COURIER PLANNER")
    print("=" * 55)
    print("Parcels:", len(parcels), "| Locations:", len(graph), "| Van capacity:", CAPACITY, "kg")

    # step 1 - sort
    sorted_parcels = merge_sort(parcels)
    print_parcels("Parcels sorted by deadline:", sorted_parcels)

    # step 2 - knapsack
    best, chosen, table = knapsack(sorted_parcels, CAPACITY)
    print("\nDP table:")
    print_table(sorted_parcels, table, CAPACITY)
    print_parcels("Selected parcels:", chosen)
    total_weight = sum(p["weight"] for p in chosen)
    print("\nTotal weight:", total_weight, "/", CAPACITY)
    print("Total priority:", best)

    # step 3 - shortest paths
    stops = sorted(set(p["dest"] for p in chosen))
    print("\nDelivery stops:", stops)
    dist, prev = dijkstra(graph, DEPOT)
    print("\nShortest paths from depot (Dijkstra):")
    for s in stops:
        print("  to", s, ": distance", dist[s], "| path", get_path(prev, s))

    # step 4 - route
    order, total, full_path = nearest_neighbour(graph, DEPOT, stops)
    print("\nVisit order:", order)
    print("Full road path:", full_path)
    print("Total route length:", total, "km")


# ---------------- tests ----------------

def make_random_parcels(n, num_nodes, seed=1):
    random.seed(seed)
    result = []
    for i in range(n):
        result.append({
            "id": "P" + str(i + 1),
            "dest": random.randint(1, num_nodes - 1),
            "weight": random.randint(1, 20),
            "priority": random.randint(1, 10),
            "deadline": random.randint(1, 48),
        })
    return result


def make_random_graph(num_nodes, seed=1):
    random.seed(seed)
    road_list = []
    for i in range(1, num_nodes):          # chain so graph is connected
        road_list.append((i - 1, i, random.randint(1, 20)))
    for i in range(num_nodes * 2):         # some extra roads
        a = random.randint(0, num_nodes - 1)
        b = random.randint(0, num_nodes - 1)
        if a != b:
            road_list.append((a, b, random.randint(1, 20)))
    return build_graph(road_list)


def brute_force(items, capacity):
    # try every combination, only for small lists
    best = 0
    n = len(items)
    for mask in range(2 ** n):
        w = 0
        v = 0
        for i in range(n):
            if mask & (1 << i):
                w += items[i]["weight"]
                v += items[i]["priority"]
        if w <= capacity and v > best:
            best = v
    return best


def test_all():
    print("\nRunning tests...")

    # sorting should match python's sorted()
    data = make_random_parcels(200, 20, seed=5)
    assert merge_sort(data) == sorted(data, key=key)
    assert bubble_sort(data) == sorted(data, key=key)
    print("sorting OK")

    # knapsack should match brute force
    for seed in range(15):
        data = make_random_parcels(10, 8, seed=seed)
        best, chosen, table = knapsack(data, 40)
        assert best == brute_force(data, 40)
        assert sum(p["weight"] for p in chosen) <= 40
    print("knapsack OK")

    # dijkstra on a tiny graph
    g = build_graph([(0, 1, 4), (0, 2, 1), (2, 1, 2), (1, 3, 1)])
    dist, prev = dijkstra(g, 0)
    assert dist[1] == 3 and dist[3] == 4
    print("dijkstra OK")

    # route on the sample map
    order, total, full_path = nearest_neighbour(build_graph(roads), 0, [3, 5, 7])
    assert total == 37
    print("route OK")

    print("All tests passed")


# ---------------- benchmark ----------------

def run_time(func, *args):
    # run 3 times and keep the best time (in ms)
    best = 999999
    for i in range(3):
        start = time.perf_counter()
        func(*args)
        t = time.perf_counter() - start
        if t < best:
            best = t
    return best * 1000


def benchmark():
    sizes = [50, 100, 200, 400, 800]
    merge_times = []
    bubble_times = []
    knap_times = []
    dijk_times = []
    route_times = []

    print("\nRuntime in ms")
    print("parcels  merge   bubble  knapsack  dijkstra  route")
    for n in sizes:
        num_nodes = max(10, n // 2)
        data = make_random_parcels(n, num_nodes)
        graph = make_random_graph(num_nodes)
        stops = list(set(p["dest"] for p in data))[:max(5, n // 10)]

        m = run_time(merge_sort, data)
        b = run_time(bubble_sort, data)
        k = run_time(knapsack, data, 200)
        d = run_time(dijkstra, graph, 0)
        r = run_time(nearest_neighbour, graph, 0, stops)

        merge_times.append(m)
        bubble_times.append(b)
        knap_times.append(k)
        dijk_times.append(d)
        route_times.append(r)
        print(str(n).ljust(9) + ("%.2f" % m).ljust(8) + ("%.2f" % b).ljust(8)
              + ("%.2f" % k).ljust(10) + ("%.2f" % d).ljust(10) + "%.2f" % r)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed, skipping chart (pip install matplotlib)")
        return

    plt.figure(figsize=(12, 4.5))

    plt.subplot(1, 2, 1)
    plt.plot(sizes, merge_times, "o-", label="Merge sort")
    plt.plot(sizes, bubble_times, "s-", label="Bubble sort")
    plt.title("Sorting runtime")
    plt.xlabel("Number of parcels")
    plt.ylabel("Time (ms)")
    plt.legend()
    plt.grid(alpha=0.3)

    plt.subplot(1, 2, 2)
    plt.plot(sizes, knap_times, "o-", label="Knapsack")
    plt.plot(sizes, dijk_times, "s-", label="Dijkstra")
    plt.plot(sizes, route_times, "^-", label="Nearest neighbour route")
    plt.title("Other steps runtime")
    plt.xlabel("Number of parcels")
    plt.ylabel("Time (ms)")
    plt.legend()
    plt.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig("runtime_chart.png", dpi=150)
    print("chart saved as runtime_chart.png")


# ---------------- main ----------------

if __name__ == "__main__":
    mode = "all"
    if len(sys.argv) > 1:
        mode = sys.argv[1]

    if mode == "demo" or mode == "all":
        demo()
    if mode == "test" or mode == "all":
        test_all()
    if mode == "bench" or mode == "all":
        benchmark()
