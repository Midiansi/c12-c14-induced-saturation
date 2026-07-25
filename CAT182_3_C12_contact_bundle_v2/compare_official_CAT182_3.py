#!/usr/bin/env python3
"""Compare the uploaded LCF graph with the official Foster-census CAT(182,3) LCF graph."""
import argparse
import ast
import hashlib
import json
import re
import time
from pathlib import Path

import networkx as nx

N = 182


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def graph_from_lcf(shifts):
    if len(shifts) != N:
        raise ValueError(f"expected {N} shifts, got {len(shifts)}")
    graph = nx.Graph()
    graph.add_nodes_from(range(N))
    for i, shift in enumerate(shifts):
        graph.add_edge(i, (i + 1) % N)
        graph.add_edge(i, (i + shift) % N)
    return graph


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("certificate", type=Path)
    parser.add_argument("official_lcf_file", type=Path)
    args = parser.parse_args()

    certificate = json.loads(args.certificate.read_text(encoding="utf-8"))
    uploaded_shifts = certificate["lcf_shifts"]
    official_line = next(
        line for line in args.official_lcf_file.read_text(encoding="utf-8").splitlines()
        if line.startswith("! 182 3:")
    )
    match = re.fullmatch(r"! 182 3:\s*(\[.*\])\^1", official_line)
    if not match:
        raise ValueError("could not parse official CAT(182,3) line")
    official_shifts = ast.literal_eval(match.group(1))

    uploaded_graph = graph_from_lcf(uploaded_shifts)
    official_graph = graph_from_lcf(official_shifts)

    print("networkx:", nx.__version__)
    print("certificate SHA-256:", sha256(args.certificate))
    print("official CAT_lcf.txt SHA-256:", sha256(args.official_lcf_file))
    print("shift sequences textually equal:", uploaded_shifts == official_shifts)
    print("uploaded graph order/size:", uploaded_graph.number_of_nodes(), uploaded_graph.number_of_edges())
    print("official graph order/size:", official_graph.number_of_nodes(), official_graph.number_of_edges())
    print("uploaded girth/diameter:", nx.girth(uploaded_graph), nx.diameter(uploaded_graph))
    print("official girth/diameter:", nx.girth(official_graph), nx.diameter(official_graph))

    started = time.perf_counter()
    matcher = nx.algorithms.isomorphism.GraphMatcher(uploaded_graph, official_graph)
    isomorphic = matcher.is_isomorphic()
    print("isomorphic:", isomorphic)
    print(f"isomorphism seconds: {time.perf_counter() - started:.6f}")
    if isomorphic:
        mapping = matcher.mapping
        print("mapping entries:", len(mapping))
        print("mapping first 20 by uploaded label:", sorted(mapping.items())[:20])
    else:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
