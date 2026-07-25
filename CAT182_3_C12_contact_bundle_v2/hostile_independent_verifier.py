#!/usr/bin/env python3
"""Hostile, independent audit of a claimed C12-induced-saturated graph.

This program uses only the Python standard library.  It reads the uploaded
edge list and JSON certificate, but it does not import either supplied verifier.
The all-cycle and all-path searches below were written independently.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import sys
import time
from collections import Counter, deque
from itertools import combinations
from pathlib import Path
from typing import Iterable

N = 182
EXPECTED_TOP_LEVEL_KEYS = {
    "graph",
    "vertices",
    "edge_count",
    "nonedge_count",
    "lcf_shifts",
    "deletion_witnesses",
    "addition_witnesses",
}
KEY_RE = re.compile(r"^(0|[1-9][0-9]*),(0|[1-9][0-9]*)$")


class AuditFailure(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditFailure(message)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_json_rejecting_duplicate_keys(path: Path):
    def reject_duplicates(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise AuditFailure(f"duplicate JSON object key: {key!r}")
            out[key] = value
        return out

    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f, object_pairs_hook=reject_duplicates)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AuditFailure(f"cannot parse certificate JSON: {exc}") from exc


def read_edge_list(path: Path):
    edges: set[tuple[int, int]] = set()
    seen_vertices: set[int] = set()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise AuditFailure(f"cannot read edge list: {exc}") from exc

    for line_number, raw in enumerate(lines, 1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        fields = stripped.split()
        require(len(fields) == 2, f"edge-list line {line_number} has {len(fields)} fields")
        try:
            u, v = (int(fields[0]), int(fields[1]))
        except ValueError as exc:
            raise AuditFailure(f"edge-list line {line_number} is not integral: {raw!r}") from exc
        require(0 <= u < N and 0 <= v < N, f"out-of-range endpoint on line {line_number}: {(u, v)}")
        require(u != v, f"loop on line {line_number}: {(u, v)}")
        edge = (u, v) if u < v else (v, u)
        require(edge not in edges, f"duplicate undirected edge on line {line_number}: {edge}")
        edges.add(edge)
        seen_vertices.update(edge)

    adjacency = [set() for _ in range(N)]
    for u, v in edges:
        adjacency[u].add(v)
        adjacency[v].add(u)
    return edges, adjacency, seen_vertices


def adjacency_masks(adjacency: list[set[int]]) -> list[int]:
    masks = []
    for nbrs in adjacency:
        mask = 0
        for v in nbrs:
            mask |= 1 << v
        masks.append(mask)
    return masks


def connected(adjacency: list[set[int]]) -> bool:
    visited = {0}
    queue = deque([0])
    while queue:
        u = queue.popleft()
        for v in adjacency[u]:
            if v not in visited:
                visited.add(v)
                queue.append(v)
    return len(visited) == N


def parse_certificate_key(raw: object) -> tuple[int, int]:
    require(isinstance(raw, str), f"certificate key is not a string: {raw!r}")
    match = KEY_RE.fullmatch(raw)
    require(match is not None, f"malformed certificate key: {raw!r}")
    u, v = int(match.group(1)), int(match.group(2))
    require(0 <= u < N and 0 <= v < N, f"out-of-range certificate key: {raw!r}")
    require(u < v, f"certificate key is not canonical u<v: {raw!r}")
    return u, v


def parse_witness_map(raw_map: object, label: str) -> dict[tuple[int, int], tuple[int, ...]]:
    require(isinstance(raw_map, dict), f"{label} is not a JSON object")
    result: dict[tuple[int, int], tuple[int, ...]] = {}
    for raw_key, raw_witness in raw_map.items():
        key = parse_certificate_key(raw_key)
        require(key not in result, f"duplicate normalized {label} key: {key}")
        require(isinstance(raw_witness, list), f"{label}[{raw_key!r}] is not a list")
        require(all(type(x) is int for x in raw_witness), f"{label}[{raw_key!r}] has non-integer vertices")
        require(all(0 <= x < N for x in raw_witness), f"{label}[{raw_key!r}] has out-of-range vertices")
        result[key] = tuple(raw_witness)
    return result


def induced_edges_on(vertices: Iterable[int], adjacency: list[set[int]]) -> set[tuple[int, int]]:
    vertex_set = set(vertices)
    return {
        (u, v)
        for u in vertex_set
        for v in adjacency[u]
        if u < v and v in vertex_set
    }


def validate_certificate(
    cert: object,
    edges: set[tuple[int, int]],
    nonedges: set[tuple[int, int]],
    adjacency: list[set[int]],
):
    require(isinstance(cert, dict), "certificate root is not a JSON object")
    require(set(cert) == EXPECTED_TOP_LEVEL_KEYS,
            f"certificate top-level keys differ: missing={EXPECTED_TOP_LEVEL_KEYS-set(cert)}, extra={set(cert)-EXPECTED_TOP_LEVEL_KEYS}")
    require(cert["graph"] == "CAT(182,3)", f"unexpected graph label: {cert['graph']!r}")
    require(cert["vertices"] == list(range(N)), "certificate vertex list is not exactly [0,...,181]")
    require(type(cert["edge_count"]) is int and cert["edge_count"] == len(edges), "declared edge count is wrong")
    require(type(cert["nonedge_count"]) is int and cert["nonedge_count"] == len(nonedges), "declared nonedge count is wrong")

    shifts = cert["lcf_shifts"]
    require(isinstance(shifts, list) and len(shifts) == N, "LCF shift list does not have length 182")
    require(all(type(s) is int for s in shifts), "LCF shifts are not all integers")

    cycle_edges = {(i, i + 1) for i in range(N - 1)} | {(0, N - 1)}
    chord_mentions: Counter[tuple[int, int]] = Counter()
    for i, shift in enumerate(shifts):
        j = (i + shift) % N
        require(i != j, f"LCF shift creates loop at vertex {i}")
        edge = (i, j) if i < j else (j, i)
        require(edge not in cycle_edges, f"LCF chord duplicates Hamilton edge: {edge}")
        chord_mentions[edge] += 1

    require(len(chord_mentions) == N // 2, f"LCF has {len(chord_mentions)} distinct chords rather than 91")
    bad_multiplicity = {e: c for e, c in chord_mentions.items() if c != 2}
    require(not bad_multiplicity, f"LCF chord mention multiplicities are not all two: {list(bad_multiplicity.items())[:5]}")
    lcf_edges = cycle_edges | set(chord_mentions)
    require(lcf_edges == edges,
            f"LCF graph differs from edge list: only_LCF={sorted(lcf_edges-edges)[:5]}, only_edge_list={sorted(edges-lcf_edges)[:5]}")

    deletion = parse_witness_map(cert["deletion_witnesses"], "deletion_witnesses")
    addition = parse_witness_map(cert["addition_witnesses"], "addition_witnesses")
    require(set(deletion) == edges,
            f"deletion keys do not exactly cover edges: missing={sorted(edges-set(deletion))[:5]}, extra={sorted(set(deletion)-edges)[:5]}")
    require(set(addition) == nonedges,
            f"addition keys do not exactly cover nonedges: missing={sorted(nonedges-set(addition))[:5]}, extra={sorted(set(addition)-nonedges)[:5]}")

    deletion_valid = 0
    for edge, cycle in deletion.items():
        require(edge in edges, f"deletion key is not an edge: {edge}")
        require(len(cycle) == 12 and len(set(cycle)) == 12, f"bad deletion witness vertices for {edge}: {cycle}")
        ring = {
            tuple(sorted((cycle[i], cycle[(i + 1) % 12])))
            for i in range(12)
        }
        require(len(ring) == 12 and ring <= edges, f"deletion witness does not list a 12-cycle for {edge}: {cycle}")
        induced = induced_edges_on(cycle, adjacency)
        require(edge not in ring, f"purported deleted edge is itself a ring edge for {edge}")
        require(induced == ring | {edge},
                f"deletion witness induced edges wrong for {edge}: missing={sorted((ring|{edge})-induced)}, extra={sorted(induced-(ring|{edge}))}")
        after_deletion = induced - {edge}
        require(after_deletion == ring and len(after_deletion) == 12,
                f"after deleting {edge}, witness is not exactly C12")
        deletion_valid += 1

    addition_valid = 0
    for nonedge, path in addition.items():
        require(nonedge in nonedges, f"addition key is not a nonedge: {nonedge}")
        require(len(path) == 12 and len(set(path)) == 12, f"bad addition witness vertices for {nonedge}: {path}")
        require({path[0], path[-1]} == set(nonedge),
                f"addition path endpoints do not match key {nonedge}: {(path[0], path[-1])}")
        path_edges = {
            tuple(sorted((path[i], path[i + 1])))
            for i in range(11)
        }
        require(len(path_edges) == 11 and path_edges <= edges,
                f"addition witness has missing/repeated path edges for {nonedge}: {path}")
        induced = induced_edges_on(path, adjacency)
        require(induced == path_edges,
                f"addition witness is not an induced P12 for {nonedge}: extra={sorted(induced-path_edges)}, missing={sorted(path_edges-induced)}")
        toggled = induced | {nonedge}
        degrees = Counter()
        for u, v in toggled:
            degrees[u] += 1
            degrees[v] += 1
        require(len(toggled) == 12 and all(degrees[v] == 2 for v in path),
                f"adding {nonedge} does not yield exactly a C12 on witness vertices")
        addition_valid += 1

    return shifts, deletion_valid, addition_valid


def canonical_cycle(cycle: tuple[int, ...]) -> tuple[int, ...]:
    """Canonicalize by rotating the minimum vertex first, then choosing direction."""
    minimum = min(cycle)
    i = cycle.index(minimum)
    forward = cycle[i:] + cycle[:i]
    reversed_cycle = tuple(reversed(cycle))
    j = reversed_cycle.index(minimum)
    backward = reversed_cycle[j:] + reversed_cycle[:j]
    return min(forward, backward)


def enumerate_all_simple_cycles_12(adjacency: list[set[int]]) -> set[tuple[int, ...]]:
    """Enumerate oriented simple walks and deduplicate only after closure.

    No least-vertex or second-vs-last pruning is used.  Every simple 12-cycle
    appears from each of its 12 starting vertices and in both directions; the
    canonical representation collapses those 24 descriptions to one.
    """
    found: set[tuple[int, ...]] = set()
    for start in range(N):
        for second in adjacency[start]:
            path = [start, second]
            used_mask = (1 << start) | (1 << second)

            def extend(current: int, used: int) -> None:
                if len(path) == 12:
                    if start in adjacency[current]:
                        found.add(canonical_cycle(tuple(path)))
                    return
                for nxt in adjacency[current]:
                    if used & (1 << nxt):
                        continue
                    path.append(nxt)
                    extend(nxt, used | (1 << nxt))
                    path.pop()

            extend(second, used_mask)
    return found


def cycle_chord_histogram(
    cycles: Iterable[tuple[int, ...]], adjacency: list[set[int]]
):
    histogram: Counter[int] = Counter()
    unique_chord_counts: Counter[tuple[int, int]] = Counter()
    induced_cycle_example = None
    for cycle in cycles:
        ring = {
            tuple(sorted((cycle[i], cycle[(i + 1) % 12])))
            for i in range(12)
        }
        internal = induced_edges_on(cycle, adjacency)
        chords = internal - ring
        histogram[len(chords)] += 1
        if not chords and induced_cycle_example is None:
            induced_cycle_example = cycle
        if len(chords) == 1:
            unique_chord_counts[next(iter(chords))] += 1
    return histogram, unique_chord_counts, induced_cycle_example


def direct_induced_c12_search(adjacency: list[set[int]]) -> tuple[int, ...] | None:
    """Direct induced-cycle search with incremental chord rejection."""
    masks = adjacency_masks(adjacency)
    for start in range(N):
        start_bit = 1 << start
        path = [start]

        def extend(current: int, used: int) -> tuple[int, ...] | None:
            if len(path) == 12:
                return tuple(path) if start in adjacency[current] else None
            final_step = len(path) == 11
            for nxt in adjacency[current]:
                bit = 1 << nxt
                if used & bit:
                    continue
                contacts = masks[nxt] & used
                expected = 1 << current
                if final_step:
                    expected |= start_bit
                if contacts != expected:
                    continue
                path.append(nxt)
                result = extend(nxt, used | bit)
                if result is not None:
                    return result
                path.pop()
            return None

        result = extend(start, start_bit)
        if result is not None:
            return result
    return None


def find_induced_c12_after_deleting(
    base_adjacency: list[set[int]], edge: tuple[int, int]
) -> tuple[int, ...] | None:
    """Search G-edge directly, starting at one deleted-edge endpoint.

    Since the independently checked original graph has no induced C12, any
    induced C12 newly present in G-edge must contain both endpoints of edge.
    Starting at u is therefore exhaustive for the toggle check.
    """
    u, v = edge
    adjacency = base_adjacency

    def neighbours(x: int):
        if x == u:
            for y in adjacency[x]:
                if y != v:
                    yield y
        elif x == v:
            for y in adjacency[x]:
                if y != u:
                    yield y
        else:
            yield from adjacency[x]

    def adjacent(x: int, y: int) -> bool:
        if (x == u and y == v) or (x == v and y == u):
            return False
        return y in adjacency[x]

    path = [u]
    used = {u}

    def extend(current: int) -> tuple[int, ...] | None:
        if len(path) == 12:
            if adjacent(current, u) and v in used:
                return tuple(path)
            return None
        final_step = len(path) == 11
        for nxt in neighbours(current):
            if nxt in used:
                continue
            contacts = {old for old in path if adjacent(nxt, old)}
            expected = {current, u} if final_step else {current}
            if contacts != expected:
                continue
            # There must still be room to include the other deleted-edge endpoint.
            new_length = len(path) + 1
            if v not in used and nxt != v and new_length == 12:
                continue
            used.add(nxt)
            path.append(nxt)
            result = extend(nxt)
            if result is not None:
                return result
            path.pop()
            used.remove(nxt)
        return None

    return extend(u)


def enumerate_induced_p12s(adjacency: list[set[int]]):
    """Enumerate every induced 12-vertex path, identifying reversal by endpoints.

    The search starts at every vertex.  A path is counted only when start<end,
    which keeps exactly one of its two orientations.  Incremental contact tests
    guarantee that each completed object is induced.
    """
    masks = adjacency_masks(adjacency)
    endpoint_witness: dict[tuple[int, int], tuple[int, ...]] = {}
    total = 0

    for start in range(N):
        path = [start]
        start_mask = 1 << start

        def extend(current: int, used: int) -> None:
            nonlocal total
            if len(path) == 12:
                end = current
                if start < end:
                    total += 1
                    endpoint_witness.setdefault((start, end), tuple(path))
                return
            for nxt in adjacency[current]:
                bit = 1 << nxt
                if used & bit:
                    continue
                if masks[nxt] & used != (1 << current):
                    continue
                path.append(nxt)
                extend(nxt, used | bit)
                path.pop()

        extend(start, start_mask)
    return total, endpoint_witness


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("edge_list", type=Path)
    parser.add_argument("certificate", type=Path)
    args = parser.parse_args()

    started = time.perf_counter()
    print("HOSTILE INDEPENDENT VERIFIER")
    print("python:", sys.version.replace("\n", " "))
    print("platform:", platform.platform())
    print("third-party packages used: none")
    print("edge-list SHA-256:", sha256(args.edge_list))
    print("certificate SHA-256:", sha256(args.certificate))

    t = time.perf_counter()
    edges, adjacency, seen_vertices = read_edge_list(args.edge_list)
    require(seen_vertices == set(range(N)), f"edge-list vertex set differs: {sorted(set(range(N))-seen_vertices)}")
    require(len(edges) == 273, f"edge count is {len(edges)}, not 273")
    degree_histogram = Counter(map(len, adjacency))
    require(degree_histogram == Counter({3: N}), f"degree histogram is {dict(degree_histogram)}")
    require(connected(adjacency), "graph is disconnected")
    all_pairs = set(combinations(range(N), 2))
    nonedges = all_pairs - edges
    require(len(nonedges) == 16198, f"nonedge count is {len(nonedges)}, not 16198")
    print(f"graph integrity: vertices={len(seen_vertices)}, edges={len(edges)}, nonedges={len(nonedges)}, degrees={dict(degree_histogram)}, connected=yes")
    print(f"graph integrity seconds: {time.perf_counter()-t:.6f}")

    t = time.perf_counter()
    cert = load_json_rejecting_duplicate_keys(args.certificate)
    _, valid_deletions, valid_additions = validate_certificate(cert, edges, nonedges, adjacency)
    print("LCF comparison: exact edge-set match; 91 distinct chords, each mentioned twice")
    print(f"certificate deletion witnesses valid: {valid_deletions}/273")
    print(f"certificate addition witnesses valid: {valid_additions}/16198")
    print(f"certificate audit seconds: {time.perf_counter()-t:.6f}")

    t = time.perf_counter()
    cycles = enumerate_all_simple_cycles_12(adjacency)
    histogram, chord_counts, induced_example = cycle_chord_histogram(cycles, adjacency)
    require(induced_example is None, f"induced C12 found by all-cycle enumeration: {induced_example}")
    require(len(cycles) == 273, f"independent simple-C12 count is {len(cycles)}, not 273")
    require(histogram == Counter({1: 273}), f"independent chord histogram is {dict(histogram)}")
    require(set(chord_counts) == edges, f"unique chords do not cover every edge")
    require(all(count == 1 for count in chord_counts.values()), "some edge is unique chord of more than one enumerated cycle")
    print(f"independent simple 12-cycles: {len(cycles)}")
    print(f"independent 12-cycle chord histogram: {dict(sorted(histogram.items()))}")
    print(f"unique-chord edge coverage: {len(chord_counts)}/273; multiplicity exactly one for every edge")
    print(f"all-cycle enumeration seconds: {time.perf_counter()-t:.6f}")

    t = time.perf_counter()
    direct_original = direct_induced_c12_search(adjacency)
    require(direct_original is None, f"direct induced-C12 search found: {direct_original}")
    print("direct induced-C12 search in G: none")
    print(f"direct induced-C12 search seconds: {time.perf_counter()-t:.6f}")

    t = time.perf_counter()
    deletion_toggle_witnesses = {}
    failed_deletions = []
    for edge in sorted(edges):
        witness = find_induced_c12_after_deleting(adjacency, edge)
        if witness is None:
            failed_deletions.append(edge)
        else:
            deletion_toggle_witnesses[edge] = witness
    require(not failed_deletions, f"deletion toggle failures: {failed_deletions[:10]}")
    print(f"independent deletion toggles successful: {len(deletion_toggle_witnesses)}/273")
    print(f"deletion-toggle search seconds: {time.perf_counter()-t:.6f}")

    t = time.perf_counter()
    induced_path_count, endpoint_witnesses = enumerate_induced_p12s(adjacency)
    missing_additions = sorted(nonedges - set(endpoint_witnesses))
    extraneous_endpoint_pairs = sorted(set(endpoint_witnesses) - nonedges)
    require(not missing_additions, f"addition toggle failures: {missing_additions[:10]}")
    require(not extraneous_endpoint_pairs,
            f"induced P12 endpoints unexpectedly include graph edges: {extraneous_endpoint_pairs[:10]}")
    print(f"independent induced 12-vertex paths: {induced_path_count}")
    print(f"independent addition toggles successful: {len(endpoint_witnesses)}/16198")
    print(f"addition-toggle search seconds: {time.perf_counter()-t:.6f}")

    print(f"TOTAL WALL SECONDS: {time.perf_counter()-started:.6f}")
    print("FINAL RESULT: VERIFIED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AuditFailure as exc:
        print(f"FINAL RESULT: NOT VERIFIED: {exc}", file=sys.stderr)
        raise SystemExit(1)
