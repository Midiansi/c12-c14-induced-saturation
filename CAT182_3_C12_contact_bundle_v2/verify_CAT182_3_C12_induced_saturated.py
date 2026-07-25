#!/usr/bin/env python3
"""Exhaustive verifier that CAT(182,3) is C12-induced-saturated.

Uses only the Python standard library.

Construction (LCF notation):
- vertices 0,...,181;
- Hamilton-cycle edges i--(i+1 mod 182);
- chord i--(i+s_i mod 182), where s_i is the i-th entry of SHIFTS.
"""

from collections import Counter
from itertools import combinations

N = 182
SHIFTS = [15, 62, 90, -28, 22, 59, -85, 21, 35, -62, -88, -61, -87, -79, -62, -15, 45, -63, -60, 40, 20, 90, -63, -30, -48, 87, -22, 54, -21, 16, 53, -76, 15, 62, -62, 73, 12, -53, 72, 49, -20, 87, 16, -35, 11, -16, 6, -15, -12, -63, -60, -57, -6, -56, 64, -11, 14, 17, -16, -40, 16, -45, -75, -62, -59, -80, 36, -85, 31, 50, -14, -90, 87, 82, -17, 77, -16, -89, 72, 43, 33, -54, 67, -53, 51, 77, 62, 78, -49, 38, 57, 89, -90, 33, 62, -62, 42, 28, 23, -31, 39, 42, -36, 85, 88, 39, 47, 87, -73, 6, -72, -90, -87, -33, 6, -6, 79, 64, -64, -50, -6, -23, -43, 48, 6, -28, -33, -38, -87, 62, -6, 42, 61, 28, 62, -51, 63, 76, -42, -39, 60, 63, 35, -42, -39, 6, 32, -57, -62, -67, -72, -6, -77, -47, 62, -82, -62, 28, 48, -87, 14, -28, -77, 90, 85, -78, 53, 80, 63, 75, 89, -48, 60, -42, -14, 30, 57, -35, -32, 56, -89, -64]


def build_graph():
    edges = set()
    for i in range(N):
        edges.add(tuple(sorted((i, (i + 1) % N))))
        edges.add(tuple(sorted((i, (i + SHIFTS[i]) % N))))
    adj = [set() for _ in range(N)]
    for u, v in edges:
        if u == v:
            raise AssertionError("loop")
        adj[u].add(v)
        adj[v].add(u)
    assert len(edges) == 273
    assert all(len(adj[v]) == 3 for v in range(N))
    return adj, edges


def enumerate_12_cycles(adj):
    """Enumerate every simple 12-cycle exactly once.

    The least vertex is fixed as the start, and reversal is broken by requiring
    the second vertex to be smaller than the last vertex.
    """
    cycles = []
    for start in range(N):
        visited = {start}
        for second in sorted(adj[start]):
            if second <= start:
                continue
            path = [start, second]
            visited.add(second)

            def dfs(cur):
                if len(path) == 12:
                    if start in adj[cur] and path[1] < path[-1]:
                        cycles.append(tuple(path))
                    return
                for nxt in adj[cur]:
                    if nxt == start or nxt in visited or nxt < start:
                        continue
                    visited.add(nxt)
                    path.append(nxt)
                    dfs(nxt)
                    path.pop()
                    visited.remove(nxt)

            dfs(second)
            visited.remove(second)
    return cycles


def cycle_chords(cycle, adj):
    cycle_edges = {
        tuple(sorted((cycle[i], cycle[(i + 1) % 12])))
        for i in range(12)
    }
    vertex_set = set(cycle)
    induced_edges = {
        tuple(sorted((u, v)))
        for u in cycle
        for v in adj[u]
        if v in vertex_set and u < v
    }
    return induced_edges - cycle_edges


def enumerate_induced_p12_endpairs(adj):
    """Enumerate induced 12-vertex paths and retain one witness per endpoint pair."""
    witnesses = {}
    path_count = 0

    for start in range(N):
        visited = {start}
        path = [start]

        def dfs(cur):
            nonlocal path_count
            if len(path) == 12:
                end = path[-1]
                if start < end:  # identify a path with its reverse
                    path_count += 1
                    witnesses.setdefault((start, end), tuple(path))
                return

            for nxt in adj[cur]:
                if nxt in visited:
                    continue
                # The new endpoint may meet only the previous endpoint.
                if any(nxt in adj[old] for old in path[:-1]):
                    continue
                visited.add(nxt)
                path.append(nxt)
                dfs(nxt)
                path.pop()
                visited.remove(nxt)

        dfs(start)

    return path_count, witnesses


def verify():
    adj, edges = build_graph()
    all_pairs = set(combinations(range(N), 2))
    nonedges = all_pairs - edges

    cycles = enumerate_12_cycles(adj)
    chord_histogram = Counter()
    deletion_witnesses = {}

    for cycle in cycles:
        chords = cycle_chords(cycle, adj)
        chord_histogram[len(chords)] += 1
        if len(chords) == 1:
            chord = next(iter(chords))
            deletion_witnesses.setdefault(chord, cycle)

    # No induced C12, and every edge is the sole chord of a 12-cycle.
    assert chord_histogram.get(0, 0) == 0
    assert set(deletion_witnesses) == edges

    induced_path_count, addition_witnesses = enumerate_induced_p12_endpairs(adj)

    # Every nonedge is the endpoint pair of an induced P12.
    assert set(addition_witnesses) == nonedges

    print("VERIFIED: CAT(182,3) is C12-induced-saturated")
    print(f"vertices: {N}")
    print(f"edges: {len(edges)}")
    print(f"nonedges: {len(nonedges)}")
    print(f"simple 12-cycles: {len(cycles)}")
    print(f"12-cycle chord histogram: {dict(sorted(chord_histogram.items()))}")
    print(f"edges covered by deletion witnesses: {len(deletion_witnesses)}")
    print(f"induced 12-vertex paths: {induced_path_count}")
    print(f"nonedges covered by addition witnesses: {len(addition_witnesses)}")

    return adj, edges, deletion_witnesses, addition_witnesses


if __name__ == "__main__":
    verify()
