# Coxeter graph \(C_{14}\)-induced-saturation verification package

## Claim and definition

This package verifies the following finite claim:

> The Coxeter graph is \(C_{14}\)-induced-saturated.

A graph is \(C_{14}\)-induced-saturated when it has no induced cycle on 14
vertices, deleting any existing edge creates one, and adding any missing edge
creates one.

## Canonical graph construction

Let the ground set be \(\mathbb Z_7=\{0,\ldots,6\}\), and let

\[
L_i=\{i,i+1,i+3\}\pmod 7,\qquad i=0,\ldots,6.
\]

The vertices are the 28 three-element subsets of \(\mathbb Z_7\) that are not
Fano lines. They are assigned labels 0 through 27 in lexicographic order. Two
vertices are adjacent exactly when their triples are disjoint. The Python and
C++ programs reconstruct the graph from this definition; the stored edge list
is not treated as the definition.

## Certificate logic

The strict JSON certificate contains graph metadata, the complete label map,
one witness for every edge deletion, and one witness for every nonedge
addition. Keys have the canonical form `"u,v"` with `u < v`.

- A deletion witness lists a 14-cycle in cyclic order. In the original graph,
  its indexed edge is the unique chord and is not a cycle-order edge. Deleting
  that chord leaves an induced \(C_{14}\).
- An addition witness lists an induced 14-vertex path in path order, with the
  indexed nonedge as its ordered endpoint pair. Adding that endpoint edge
  closes an induced \(C_{14}\).
- The absence of an induced \(C_{14}\) in the original graph is verified by
  exhaustive cycle enumeration and separately by examining every 14-vertex
  subset in C++.

The JSON readers reject duplicate raw object keys, noncanonical pair keys, and
key-normalization collisions.

## Verified counts

| Quantity | Result |
|---|---:|
| Vertices | 28 |
| Edges | 42 |
| Nonedges | 336 |
| Degree | 3 at every vertex |
| Connected | yes |
| Girth | 7 |
| Diameter | 4 |
| Simple 14-cycles | 420 |
| 14-cycles with 0 chords | 0 |
| 14-cycles with 1 chord | 252 |
| 14-cycles with 2 chords | 168 |
| One-chord cycles per edge | 6 for each of 42 edges |
| Induced 14-vertex paths, reversal identified | 5,040 |
| Valid deletion cases | 42 / 42 |
| Valid addition cases | 336 / 336 |
| 14-vertex subsets checked in C++ | 40,116,600 |

The induced-path endpoint table is:

| Endpoint distance | Nonedges | Paths per pair |
|---:|---:|---:|
| 2 | 84 | 4 |
| 3 | 168 | 18 |
| 4 | 84 | 20 |

## Independent verification methods

`verify_coxeter_C14.py` uses an adjacency-set representation. It enumerates
simple 14-cycles by rooted depth-first search with minimum-vertex and reversal
symmetry breaking. It separately grows induced paths as ordered vertex lists.

`verify_coxeter_C14_independent.py` does not import the primary verifier. It
uses integer adjacency masks, builds every simple 14-cycle by joining two
internally vertex-disjoint 7-edge paths with common endpoints, and deduplicates
cycles by an independent rotation/reversal canonicalization. Its induced-path
search also uses bit-mask state. Both programs independently reconstruct the
Fano graph, parse the input files, validate all 378 certificate witnesses,
reproduce the cycle histogram, and reproduce the 5,040-path endpoint table.

`verify_no_induced_C14.cpp` supplies a third negative check. It enumerates
exactly \(\binom{28}{14}=40,116,600\) subsets. For every subset it computes the
complete induced degree sequence and reports an induced \(C_{14}\) only if all
14 degrees are two and the induced subgraph is connected.

## Files

- `coxeter_edges.txt` — the 42 canonical edges, one `u v` pair per line.
- `vertex_labels.txt` — labels 0 through 27 and their nonline triples.
- `coxeter_C14_witnesses.json` — strict deletion and addition certificate.
- `verify_coxeter_C14.py` — primary standard-library-only Python verifier.
- `verify_coxeter_C14_independent.py` — materially independent Python verifier.
- `verify_no_induced_C14.cpp` — portable C++20 all-subsets negative checker.
- `python_verification_output.txt` — clean-room primary run, command, version,
  and timing.
- `independent_python_output.txt` — clean-room independent run and timing.
- `cpp_verification_output.txt` — strict optimized build and run record.
- `cpp_sanitized_output.txt` — AddressSanitizer/UndefinedBehaviorSanitizer build
  and run record.
- `TECHNICAL_SUMMARY.md` — short researcher-facing account of the computation.
- `SHA256SUMS.txt` — SHA-256 identities for every other included file.

Compiled binaries are intentionally excluded.

## Requirements and commands

The Python programs require Python 3 and only the standard library. They were
tested with Python 3.9.6. The C++ checker requires a C++20 implementation; the
recorded build used Apple clang 17.0.0 on arm64 macOS.

From this directory, verify file identities on macOS:

```sh
shasum -a 256 -c SHA256SUMS.txt
```

On systems providing GNU Coreutils:

```sh
sha256sum -c SHA256SUMS.txt
```

Run both Python verifiers:

```sh
python3 -B verify_coxeter_C14.py
python3 -B verify_coxeter_C14_independent.py
```

Compile and run the strict optimized C++ checker:

```sh
c++ -std=c++20 -O2 -Wall -Wextra -Wpedantic \
    -Wconversion -Wshadow \
    verify_no_induced_C14.cpp -o verify_no_induced_C14
./verify_no_induced_C14
```

When the compiler supports AddressSanitizer and UndefinedBehaviorSanitizer:

```sh
c++ -std=c++20 -O1 -g \
    -fsanitize=address,undefined \
    -fno-omit-frame-pointer \
    verify_no_induced_C14.cpp -o verify_no_induced_C14_sanitized
./verify_no_induced_C14_sanitized
```

Sanitizers were supported in the recorded environment; the sanitized run
completed without a diagnostic. Stored output logs are audit records, not
substitutes for rerunning the programs. SHA-256 hashes establish file identity,
not mathematical truth.

## Scope and disclosure

The candidate construction and portions of the verification software were
developed during AI-assisted computational exploration. The accompanying
programs and certificates are provided to make every mathematical claim
independently checkable.

This package addresses mathematical correctness only. It does not establish
novelty, priority, minimality, or publication status.
