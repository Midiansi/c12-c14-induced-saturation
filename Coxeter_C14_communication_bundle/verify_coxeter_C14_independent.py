#!/usr/bin/env python3
"""Independent verifier using bit masks and meet-in-the-middle cycle assembly."""

import argparse
from collections import Counter, defaultdict, deque
from itertools import combinations
import json
from pathlib import Path
import re
import sys


N = 28
K = 14


class CheckFailure(Exception):
    pass


def check(condition, detail):
    if not condition:
        raise CheckFailure(detail)


def make_graph():
    lines = set()
    for i in range(7):
        lines.add(tuple(sorted((i, (i + 1) % 7, (i + 3) % 7))))
    triples = []
    for a in range(7):
        for b in range(a + 1, 7):
            for c in range(b + 1, 7):
                if (a, b, c) not in lines:
                    triples.append((a, b, c))
    masks = [sum(1 << point for point in triple) for triple in triples]
    neighbors = [0] * len(triples)
    edges = set()
    for u in range(len(triples)):
        for v in range(u + 1, len(triples)):
            if masks[u] & masks[v] == 0:
                neighbors[u] |= 1 << v
                neighbors[v] |= 1 << u
                edges.add((u, v))
    return triples, neighbors, edges


def vertices(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


def popcount(mask):
    count = 0
    while mask:
        mask &= mask - 1
        count += 1
    return count


def load_edges(path):
    result = set()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise CheckFailure(f"cannot read {path}: {exc}") from exc
    for number, line in enumerate(lines, 1):
        pieces = line.split()
        check(len(pieces) == 2, f"{path}:{number}: malformed edge")
        try:
            u, v = map(int, pieces)
        except ValueError as exc:
            raise CheckFailure(f"{path}:{number}: noninteger edge") from exc
        check(0 <= u < v < N, f"{path}:{number}: noncanonical edge")
        check((u, v) not in result, f"{path}:{number}: duplicate edge")
        result.add((u, v))
    return result


LABEL_RE = re.compile(r"([0-9]+): \{([0-9]+),([0-9]+),([0-9]+)\}")


def load_labels(path):
    table = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise CheckFailure(f"cannot read {path}: {exc}") from exc
    for number, line in enumerate(lines, 1):
        match = LABEL_RE.fullmatch(line)
        check(match is not None, f"{path}:{number}: malformed label")
        raw = [int(item) for item in match.groups()]
        index, triple = raw[0], tuple(raw[1:])
        check(index not in table, f"{path}:{number}: duplicate label")
        check(
            0 <= index < N and 0 <= triple[0] < triple[1] < triple[2] < 7,
            f"{path}:{number}: noncanonical label",
        )
        table[index] = triple
    check(set(table) == set(range(N)), f"{path}: incomplete label map")
    return [table[i] for i in range(N)]


def unique_object(pairs):
    output = {}
    for key, value in pairs:
        if key in output:
            raise CheckFailure(f"duplicate raw JSON key {key!r}")
        output[key] = value
    return output


def read_certificate(path):
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise CheckFailure(f"cannot read {path}: {exc}") from exc
    try:
        return json.loads(raw, object_pairs_hook=unique_object)
    except json.JSONDecodeError as exc:
        raise CheckFailure(f"malformed JSON in {path}: {exc}") from exc


def pair_from_key(raw):
    check(isinstance(raw, str), "certificate index is not a string")
    components = raw.split(",")
    check(len(components) == 2, f"bad certificate index {raw!r}")
    try:
        u, v = map(int, components)
    except ValueError as exc:
        raise CheckFailure(f"bad certificate index {raw!r}") from exc
    check(0 <= u < v < N and raw == f"{u},{v}", f"nonnormalized certificate index {raw!r}")
    return u, v


def decode_witnesses(raw, kind):
    check(isinstance(raw, dict), f"{kind} certificate section is not an object")
    decoded = {}
    canonical_indices = set()
    for key, sequence in raw.items():
        pair = pair_from_key(key)
        canonical = f"{pair[0]},{pair[1]}"
        check(canonical not in canonical_indices, f"{kind} normalization collision at {key!r}")
        canonical_indices.add(canonical)
        check(isinstance(sequence, list) and len(sequence) == K, f"{kind} {key}: wrong length")
        check(
            all(isinstance(x, int) and not isinstance(x, bool) and 0 <= x < N for x in sequence),
            f"{kind} {key}: invalid vertex",
        )
        check(len(set(sequence)) == K, f"{kind} {key}: repeated vertex")
        decoded[pair] = tuple(sequence)
    return decoded


def inspect_certificate(certificate, triples, edges, nonedges):
    check(
        set(certificate) == {"metadata", "vertex_labels", "deletions", "additions"},
        "certificate sections are not exact",
    )
    metadata = certificate["metadata"]
    check(
        isinstance(metadata, dict)
        and metadata.get("graph_name") == "Coxeter graph"
        and metadata.get("cycle_length") == K
        and metadata.get("vertex_count") == N
        and metadata.get("edge_count") == 42
        and metadata.get("nonedge_count") == 336,
        "certificate metadata is inconsistent",
    )
    label_map = certificate["vertex_labels"]
    check(isinstance(label_map, dict), "certificate vertex_labels is not an object")
    check(set(label_map) == {str(i) for i in range(N)}, "certificate labels are incomplete")
    for i, triple in enumerate(triples):
        check(label_map[str(i)] == list(triple), f"certificate label {i} is wrong")
    deletions = decode_witnesses(certificate["deletions"], "deletion")
    additions = decode_witnesses(certificate["additions"], "addition")
    check(set(deletions) == edges, "deletion certificate coverage is not exact")
    check(set(additions) == nonedges, "addition certificate coverage is not exact")
    return deletions, additions


def has_edge(neighbors, u, v):
    return bool(neighbors[u] & (1 << v))


def check_deletion(pair, order, neighbors):
    cycle_pairs = {
        tuple(sorted((order[i], order[(i + 1) % K]))) for i in range(K)
    }
    check(len(cycle_pairs) == K, f"deletion {pair}: bad cyclic order")
    check(pair not in cycle_pairs, f"deletion {pair}: indexed edge lies on cycle order")
    selected = set(order)
    present = {
        (u, v)
        for u, v in combinations(sorted(selected), 2)
        if has_edge(neighbors, u, v)
    }
    check(present == cycle_pairs | {pair}, f"deletion {pair}: not a unique-chord witness")


def check_addition(pair, order, neighbors):
    check((order[0], order[-1]) == pair, f"addition {pair}: endpoints are wrong")
    path_pairs = {tuple(sorted((order[i], order[i + 1]))) for i in range(K - 1)}
    check(len(path_pairs) == K - 1, f"addition {pair}: bad path order")
    selected = set(order)
    present = {
        (u, v)
        for u, v in combinations(sorted(selected), 2)
        if has_edge(neighbors, u, v)
    }
    check(present == path_pairs, f"addition {pair}: path is not induced")
    check(not has_edge(neighbors, *pair), f"addition {pair}: indexed pair is an edge")


def canonical_cycle(sequence):
    options = []
    forward = tuple(sequence)
    backward = tuple(reversed(sequence))
    for oriented in (forward, backward):
        for shift in range(K):
            options.append(oriented[shift:] + oriented[:shift])
    return min(options)


def meet_in_middle_cycles(neighbors):
    half_paths = defaultdict(list)

    def grow(path, used):
        if len(path) == 8:
            start, end = path[0], path[-1]
            if start < end:
                internal = used ^ (1 << start) ^ (1 << end)
                half_paths[(start, end)].append((tuple(path), internal))
            return
        for nxt in vertices(neighbors[path[-1]] & ~used):
            path.append(nxt)
            grow(path, used | (1 << nxt))
            path.pop()

    for start in range(N):
        grow([start], 1 << start)

    cycles = set()
    for paths in half_paths.values():
        for (first, first_internal), (second, second_internal) in combinations(paths, 2):
            if first_internal & second_internal:
                continue
            assembled = first + tuple(reversed(second))[1:-1]
            check(len(set(assembled)) == K, "internal meet-in-the-middle assembly error")
            cycles.add(canonical_cycle(assembled))
    return cycles


def classify_cycles(cycles, neighbors):
    histogram = Counter()
    unique_chords = Counter()
    for cycle in cycles:
        rim = {
            tuple(sorted((cycle[i], cycle[(i + 1) % K]))) for i in range(K)
        }
        selected = set(cycle)
        present = {
            (u, v)
            for u, v in combinations(sorted(selected), 2)
            if has_edge(neighbors, u, v)
        }
        chords = present - rim
        histogram[len(chords)] += 1
        if len(chords) == 1:
            unique_chords[next(iter(chords))] += 1
    return histogram, unique_chords


def bitmask_induced_paths(neighbors):
    endpoint_counts = Counter()

    def extend(first, last, used, length):
        if length == K:
            if first < last:
                endpoint_counts[(first, last)] += 1
            return
        candidates = neighbors[last] & ~used
        for nxt in vertices(candidates):
            earlier = used ^ (1 << last)
            if neighbors[nxt] & earlier:
                continue
            extend(first, nxt, used | (1 << nxt), length + 1)

    for start in range(N):
        extend(start, start, 1 << start, 1)
    return endpoint_counts


def distance_matrix(neighbors):
    matrix = []
    for source in range(N):
        distance = [-1] * N
        distance[source] = 0
        queue = deque([source])
        while queue:
            vertex = queue.popleft()
            for nxt in vertices(neighbors[vertex]):
                if distance[nxt] == -1:
                    distance[nxt] = distance[vertex] + 1
                    queue.append(nxt)
        matrix.append(distance)
    return matrix


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--edges")
    parser.add_argument("--labels")
    parser.add_argument("--certificate")
    return parser.parse_args()


def choose(raw, name, directory):
    return Path(raw) if raw is not None else directory / name


def verify(options):
    directory = Path(__file__).resolve().parent
    triples, neighbors, edges = make_graph()
    all_pairs = set(combinations(range(N), 2))
    nonedges = all_pairs - edges
    check(len(triples) == 28 and len(edges) == 42 and len(nonedges) == 336, "basic graph counts fail")
    check(all(popcount(neighbors[v]) == 3 for v in range(N)), "graph is not cubic")
    check(load_edges(choose(options.edges, "coxeter_edges.txt", directory)) == edges, "edge list mismatch")
    check(load_labels(choose(options.labels, "vertex_labels.txt", directory)) == triples, "label map mismatch")

    certificate = read_certificate(
        choose(options.certificate, "coxeter_C14_witnesses.json", directory)
    )
    deletions, additions = inspect_certificate(certificate, triples, edges, nonedges)
    for pair, order in deletions.items():
        check_deletion(pair, order, neighbors)
    for pair, order in additions.items():
        check_addition(pair, order, neighbors)

    cycles = meet_in_middle_cycles(neighbors)
    histogram, unique_chords = classify_cycles(cycles, neighbors)
    check(len(cycles) == 420, f"meet-in-the-middle cycle count is {len(cycles)}, not 420")
    check(histogram == Counter({1: 252, 2: 168}), f"wrong chord histogram: {histogram}")
    check(histogram[0] == 0, "an induced C14 exists")
    check(
        set(unique_chords) == edges and all(unique_chords[e] == 6 for e in edges),
        "unique-chord incidence is wrong",
    )

    endpoint_counts = bitmask_induced_paths(neighbors)
    check(sum(endpoint_counts.values()) == 5040, "induced-path total is not 5,040")
    check(set(endpoint_counts) == nonedges, "induced-path endpoint coverage is not exact")
    distances = distance_matrix(neighbors)
    table = defaultdict(Counter)
    for u, v in nonedges:
        table[distances[u][v]][endpoint_counts[(u, v)]] += 1
    check(
        dict(table)
        == {2: Counter({4: 84}), 3: Counter({18: 168}), 4: Counter({20: 84})},
        f"wrong endpoint-distance table: {dict(table)}",
    )

    print("Independent construction and stored-data agreement: yes")
    print("cycle method: two internally disjoint 7-edge paths, canonicalized by rotation/reversal")
    print("simple 14-cycles: 420")
    print("chord histogram: 0=0, 1=252, 2=168")
    print("unique-chord incidence: 6 cycles for each of 42 edges")
    print("path method: bit-mask induced-path search")
    print("induced 14-vertex paths (reversal identified): 5040")
    print("endpoint table: d2: 84 x 4; d3: 168 x 18; d4: 84 x 20")
    print("valid deletion cases: 42 / 42")
    print("valid addition cases: 336 / 336")
    print("INDEPENDENTLY VERIFIED: the Coxeter graph is C14-induced-saturated")


def main():
    try:
        verify(arguments())
    except CheckFailure as exc:
        print(f"INDEPENDENT VERIFICATION FAILED: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"INDEPENDENT VERIFICATION FAILED: operating-system error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
