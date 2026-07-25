#!/usr/bin/env python3
"""Primary exhaustive verifier for Coxeter graph C14-induced saturation."""

import argparse
from collections import Counter, defaultdict, deque
from itertools import combinations
import json
from pathlib import Path
import re
import sys


CYCLE_LENGTH = 14
VERTEX_COUNT = 28


class VerificationError(Exception):
    """Raised when an input or mathematical verification check fails."""


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def construct_fano_graph():
    points = range(7)
    fano_lines = {
        tuple(sorted((i, (i + 1) % 7, (i + 3) % 7)))
        for i in points
    }
    labels = [
        triple
        for triple in combinations(points, 3)
        if triple not in fano_lines
    ]
    adjacency = [set() for _ in labels]
    for u, v in combinations(range(len(labels)), 2):
        if set(labels[u]).isdisjoint(labels[v]):
            adjacency[u].add(v)
            adjacency[v].add(u)
    return labels, adjacency


def graph_edges(adjacency):
    return {
        (u, v)
        for u in range(len(adjacency))
        for v in adjacency[u]
        if u < v
    }


def read_edge_list(path):
    edges = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise VerificationError(f"cannot read edge list {path}: {exc}") from exc
    for line_number, line in enumerate(lines, 1):
        fields = line.split()
        require(
            len(fields) == 2,
            f"{path}:{line_number}: expected exactly two integer fields",
        )
        try:
            u, v = (int(field) for field in fields)
        except ValueError as exc:
            raise VerificationError(
                f"{path}:{line_number}: edge endpoints must be integers"
            ) from exc
        require(0 <= u < v < VERTEX_COUNT, f"{path}:{line_number}: edge is not canonical")
        edges.append((u, v))
    require(len(edges) == len(set(edges)), f"{path}: duplicate edge")
    return set(edges)


LABEL_PATTERN = re.compile(r"([0-9]+): \{([0-9]+),([0-9]+),([0-9]+)\}")


def read_vertex_labels(path):
    labels = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise VerificationError(f"cannot read label map {path}: {exc}") from exc
    for line_number, line in enumerate(lines, 1):
        match = LABEL_PATTERN.fullmatch(line)
        require(match is not None, f"{path}:{line_number}: malformed label line")
        values = tuple(int(value) for value in match.groups())
        index, triple = values[0], values[1:]
        require(index not in labels, f"{path}:{line_number}: duplicate vertex label")
        require(
            0 <= index < VERTEX_COUNT and 0 <= triple[0] < triple[1] < triple[2] <= 6,
            f"{path}:{line_number}: noncanonical vertex label",
        )
        labels[index] = triple
    require(set(labels) == set(range(VERTEX_COUNT)), f"{path}: label coverage is not 0..27")
    return [labels[index] for index in range(VERTEX_COUNT)]


def reject_duplicate_json_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise VerificationError(f"duplicate raw JSON object key: {key!r}")
        result[key] = value
    return result


def load_json(path):
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise VerificationError(f"cannot read certificate {path}: {exc}") from exc
    try:
        return json.loads(text, object_pairs_hook=reject_duplicate_json_keys)
    except json.JSONDecodeError as exc:
        raise VerificationError(f"{path}: malformed JSON: {exc}") from exc


def parse_pair_key(key):
    require(isinstance(key, str), "certificate pair key is not a string")
    parts = key.split(",")
    require(len(parts) == 2, f"malformed certificate pair key: {key!r}")
    try:
        u, v = (int(part) for part in parts)
    except ValueError as exc:
        raise VerificationError(f"noninteger certificate pair key: {key!r}") from exc
    require(0 <= u < v < VERTEX_COUNT, f"noncanonical certificate pair key: {key!r}")
    require(key == f"{u},{v}", f"nonnormalized certificate pair key: {key!r}")
    return u, v


def validate_witness_sequence(value, context):
    require(isinstance(value, list), f"{context}: witness must be a JSON array")
    require(len(value) == CYCLE_LENGTH, f"{context}: witness must contain 14 vertices")
    require(
        all(isinstance(vertex, int) and not isinstance(vertex, bool) for vertex in value),
        f"{context}: witness vertices must be integers",
    )
    require(
        all(0 <= vertex < VERTEX_COUNT for vertex in value),
        f"{context}: witness vertex outside 0..27",
    )
    require(len(set(value)) == CYCLE_LENGTH, f"{context}: repeated witness vertex")
    return tuple(value)


def parse_witness_map(raw, context):
    require(isinstance(raw, dict), f"certificate {context} must be an object")
    parsed = {}
    normalized = set()
    for raw_key, raw_witness in raw.items():
        pair = parse_pair_key(raw_key)
        normalized_key = f"{pair[0]},{pair[1]}"
        require(
            normalized_key not in normalized,
            f"normalization collision in certificate {context}: {raw_key!r}",
        )
        normalized.add(normalized_key)
        parsed[pair] = validate_witness_sequence(raw_witness, f"{context} {raw_key}")
    return parsed


def validate_certificate_structure(certificate, labels, edges, nonedges):
    require(isinstance(certificate, dict), "certificate root must be an object")
    expected_sections = {"metadata", "vertex_labels", "deletions", "additions"}
    require(set(certificate) == expected_sections, "certificate has missing or extra sections")

    metadata = certificate["metadata"]
    expected_metadata = {
        "graph_name": "Coxeter graph",
        "claim": "Coxeter graph is C14-induced-saturated",
        "construction": (
            "Nonline 3-subsets of Z_7, in lexicographic order; "
            "two vertices are adjacent exactly when their triples are disjoint."
        ),
        "cycle_length": 14,
        "vertex_count": 28,
        "edge_count": 42,
        "nonedge_count": 336,
    }
    require(metadata == expected_metadata, "certificate metadata is not exactly canonical")

    raw_labels = certificate["vertex_labels"]
    require(isinstance(raw_labels, dict), "certificate vertex_labels must be an object")
    require(set(raw_labels) == {str(i) for i in range(VERTEX_COUNT)}, "certificate label coverage is not exact")
    for index, expected in enumerate(labels):
        actual = raw_labels[str(index)]
        require(
            isinstance(actual, list) and tuple(actual) == expected,
            f"certificate vertex label {index} does not match the Fano construction",
        )

    deletions = parse_witness_map(certificate["deletions"], "deletion")
    additions = parse_witness_map(certificate["additions"], "addition")
    require(set(deletions) == edges, "certificate deletion coverage is not exactly all 42 edges")
    require(set(additions) == nonedges, "certificate addition coverage is not exactly all 336 nonedges")
    return deletions, additions


def all_distances(adjacency):
    matrix = []
    for source in range(len(adjacency)):
        distance = [-1] * len(adjacency)
        distance[source] = 0
        queue = deque([source])
        while queue:
            vertex = queue.popleft()
            for neighbor in adjacency[vertex]:
                if distance[neighbor] == -1:
                    distance[neighbor] = distance[vertex] + 1
                    queue.append(neighbor)
        matrix.append(distance)
    return matrix


def graph_girth(adjacency):
    best = len(adjacency) + 1
    for source in range(len(adjacency)):
        distance = [-1] * len(adjacency)
        parent = [-1] * len(adjacency)
        distance[source] = 0
        queue = deque([source])
        while queue:
            vertex = queue.popleft()
            for neighbor in adjacency[vertex]:
                if distance[neighbor] == -1:
                    distance[neighbor] = distance[vertex] + 1
                    parent[neighbor] = vertex
                    queue.append(neighbor)
                elif parent[vertex] != neighbor:
                    best = min(best, distance[vertex] + distance[neighbor] + 1)
    return best


def enumerate_simple_14_cycles(adjacency):
    chord_histogram = Counter()
    unique_chord_counts = Counter()
    total = 0
    path = []
    used = set()

    def record_cycle():
        nonlocal total
        total += 1
        cycle_edges = {
            tuple(sorted((path[index], path[(index + 1) % CYCLE_LENGTH])))
            for index in range(CYCLE_LENGTH)
        }
        selected = set(path)
        induced_edges = {
            (u, v)
            for u in selected
            for v in adjacency[u]
            if u < v and v in selected
        }
        chords = induced_edges - cycle_edges
        chord_histogram[len(chords)] += 1
        if len(chords) == 1:
            unique_chord_counts[next(iter(chords))] += 1

    def extend(start, current):
        if len(path) == CYCLE_LENGTH:
            if start in adjacency[current] and path[1] < path[-1]:
                record_cycle()
            return
        for neighbor in adjacency[current]:
            if neighbor == start or neighbor in used or neighbor < start:
                continue
            path.append(neighbor)
            used.add(neighbor)
            extend(start, neighbor)
            used.remove(neighbor)
            path.pop()

    for start in range(len(adjacency)):
        path[:] = [start]
        used.clear()
        used.add(start)
        for neighbor in adjacency[start]:
            if neighbor > start:
                path.append(neighbor)
                used.add(neighbor)
                extend(start, neighbor)
                used.remove(neighbor)
                path.pop()
    return total, chord_histogram, unique_chord_counts


def enumerate_induced_14_paths(adjacency):
    endpoint_counts = Counter()
    total = 0
    path = []
    used = set()

    def extend(current):
        nonlocal total
        if len(path) == CYCLE_LENGTH:
            first, last = path[0], path[-1]
            if first < last:
                total += 1
                endpoint_counts[(first, last)] += 1
            return
        for neighbor in adjacency[current]:
            if neighbor in used:
                continue
            if any(old in adjacency[neighbor] for old in path[:-1]):
                continue
            path.append(neighbor)
            used.add(neighbor)
            extend(neighbor)
            used.remove(neighbor)
            path.pop()

    for start in range(len(adjacency)):
        path[:] = [start]
        used.clear()
        used.add(start)
        extend(start)
    return total, endpoint_counts


def ordered_cycle_edges(sequence):
    return {
        tuple(sorted((sequence[index], sequence[(index + 1) % CYCLE_LENGTH])))
        for index in range(CYCLE_LENGTH)
    }


def ordered_path_edges(sequence):
    return {
        tuple(sorted((sequence[index], sequence[index + 1])))
        for index in range(CYCLE_LENGTH - 1)
    }


def induced_edges_on(sequence, edges):
    selected = set(sequence)
    return {edge for edge in edges if edge[0] in selected and edge[1] in selected}


def connected_two_regular(sequence, modified_edges):
    selected = set(sequence)
    local = {vertex: set() for vertex in selected}
    for u, v in modified_edges:
        if u in selected and v in selected:
            local[u].add(v)
            local[v].add(u)
    if any(len(local[vertex]) != 2 for vertex in selected):
        return False
    reached = set()
    stack = [sequence[0]]
    while stack:
        vertex = stack.pop()
        if vertex in reached:
            continue
        reached.add(vertex)
        stack.extend(local[vertex] - reached)
    return reached == selected


def validate_deletion_witness(edge, cycle, edges):
    cycle_edges = ordered_cycle_edges(cycle)
    require(len(cycle_edges) == CYCLE_LENGTH, f"deletion {edge}: malformed cyclic order")
    require(edge not in cycle_edges, f"deletion {edge}: deleted edge is a cycle-order edge")
    require(cycle_edges <= edges, f"deletion {edge}: cyclic order uses a nonedge")
    original_induced = induced_edges_on(cycle, edges)
    require(
        original_induced == cycle_edges | {edge},
        f"deletion {edge}: indexed edge is not the unique chord",
    )
    modified = edges - {edge}
    require(
        connected_two_regular(cycle, modified),
        f"deletion {edge}: toggle does not create an induced C14",
    )


def validate_addition_witness(nonedge, path, edges):
    require(
        (path[0], path[-1]) == nonedge,
        f"addition {nonedge}: path endpoints are not the indexed ordered pair",
    )
    path_edges = ordered_path_edges(path)
    require(len(path_edges) == CYCLE_LENGTH - 1, f"addition {nonedge}: malformed path order")
    require(path_edges <= edges, f"addition {nonedge}: path order uses a nonedge")
    require(
        induced_edges_on(path, edges) == path_edges,
        f"addition {nonedge}: listed path is not induced",
    )
    require(nonedge not in edges, f"addition {nonedge}: indexed pair is already an edge")
    modified = edges | {nonedge}
    require(
        connected_two_regular(path, modified),
        f"addition {nonedge}: toggle does not create an induced C14",
    )


def resolve_input(argument, default_name, script_directory):
    return Path(argument) if argument is not None else script_directory / default_name


def parse_arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--edges", help="edge-list path (default: coxeter_edges.txt beside this script)")
    parser.add_argument("--labels", help="label-map path (default: vertex_labels.txt beside this script)")
    parser.add_argument(
        "--certificate",
        help="certificate path (default: coxeter_C14_witnesses.json beside this script)",
    )
    return parser.parse_args()


def run_verification(arguments):
    script_directory = Path(__file__).resolve().parent
    edge_path = resolve_input(arguments.edges, "coxeter_edges.txt", script_directory)
    label_path = resolve_input(arguments.labels, "vertex_labels.txt", script_directory)
    certificate_path = resolve_input(
        arguments.certificate, "coxeter_C14_witnesses.json", script_directory
    )

    labels, adjacency = construct_fano_graph()
    constructed_edges = graph_edges(adjacency)
    stored_edges = read_edge_list(edge_path)
    stored_labels = read_vertex_labels(label_path)
    require(stored_edges == constructed_edges, "stored edge list disagrees with Fano construction")
    require(stored_labels == labels, "stored vertex labels disagree with Fano construction")

    all_pairs = set(combinations(range(len(adjacency)), 2))
    nonedges = all_pairs - constructed_edges
    require(len(adjacency) == 28, "graph order is not 28")
    require(len(constructed_edges) == 42, "graph size is not 42")
    require(len(nonedges) == 336, "nonedge count is not 336")
    require(
        Counter(len(neighbors) for neighbors in adjacency) == Counter({3: 28}),
        "degree sequence is not 3-regular",
    )

    distance = all_distances(adjacency)
    require(all(value >= 0 for row in distance for value in row), "graph is disconnected")
    distance_distribution = Counter(
        distance[u][v] for u, v in combinations(range(len(adjacency)), 2)
    )
    require(
        distance_distribution == Counter({1: 42, 2: 84, 3: 168, 4: 84}),
        "distance distribution is incorrect",
    )
    require(max(distance_distribution) == 4, "diameter is not 4")
    require(graph_girth(adjacency) == 7, "girth is not 7")

    certificate = load_json(certificate_path)
    deletion_witnesses, addition_witnesses = validate_certificate_structure(
        certificate, labels, constructed_edges, nonedges
    )
    for edge, cycle in deletion_witnesses.items():
        validate_deletion_witness(edge, cycle, constructed_edges)
    for nonedge, path in addition_witnesses.items():
        validate_addition_witness(nonedge, path, constructed_edges)

    cycle_total, chord_histogram, unique_chord_counts = enumerate_simple_14_cycles(adjacency)
    require(cycle_total == 420, "simple 14-cycle count is not 420")
    require(
        chord_histogram == Counter({1: 252, 2: 168}),
        f"chord histogram is incorrect: {dict(sorted(chord_histogram.items()))}",
    )
    require(chord_histogram[0] == 0, "the original graph contains an induced C14")
    require(
        set(unique_chord_counts) == constructed_edges
        and all(unique_chord_counts[edge] == 6 for edge in constructed_edges),
        "not every edge is the unique chord of exactly six cycles",
    )

    path_total, endpoint_counts = enumerate_induced_14_paths(adjacency)
    require(path_total == 5040, "unoriented induced 14-vertex path count is not 5,040")
    require(set(endpoint_counts) == nonedges, "induced-path endpoint coverage is not exact")
    endpoint_table = defaultdict(Counter)
    for pair in nonedges:
        endpoint_table[distance[pair[0]][pair[1]]][endpoint_counts[pair]] += 1
    expected_endpoint_table = {
        2: Counter({4: 84}),
        3: Counter({18: 168}),
        4: Counter({20: 84}),
    }
    require(dict(endpoint_table) == expected_endpoint_table, "endpoint-distance table is incorrect")

    print("Graph construction and stored data: exact agreement")
    print("vertices: 28")
    print("edges: 42")
    print("nonedges: 336")
    print("degree sequence: 3^28")
    print("connected: yes")
    print("girth: 7")
    print("diameter: 4")
    print("distance distribution: d1=42, d2=84, d3=168, d4=84")
    print("simple 14-cycles: 420")
    print("chord histogram: 0=0, 1=252, 2=168")
    print("unique-chord incidence: 6 cycles for each of 42 edges")
    print("induced 14-vertex paths (reversal identified): 5040")
    print("endpoint table: d2: 84 x 4; d3: 168 x 18; d4: 84 x 20")
    print("valid deletion cases: 42 / 42")
    print("valid addition cases: 336 / 336")
    print("VERIFIED: the Coxeter graph is C14-induced-saturated")


def main():
    try:
        run_verification(parse_arguments())
    except VerificationError as exc:
        print(f"VERIFICATION FAILED: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"VERIFICATION FAILED: operating-system error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
