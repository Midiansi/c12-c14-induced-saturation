# Technical summary: the Coxeter graph and \(C_{14}\)-induced saturation

Repository or shared package:

**REPOSITORY-OR-DRIVE-LINK-HERE**

## Construction and claim

Write the Fano-plane points as \(\mathbb Z_7\), with lines
\(L_i=\{i,i+1,i+3\}\pmod 7\). Take as vertices the 28 three-element subsets of
\(\mathbb Z_7\) that are not Fano lines, in lexicographic order, and join two
vertices exactly when the corresponding triples are disjoint. This is the
Coxeter graph.

The checked claim is that the graph is \(C_{14}\)-induced-saturated:

1. it contains no induced \(C_{14}\);
2. deleting any one of its 42 edges creates an induced \(C_{14}\);
3. adding any one of its 336 nonedges creates an induced \(C_{14}\).

The package addresses this finite correctness claim only. It makes no claim
about novelty, priority, minimality, or publication status.

## Negative condition and cycle enumeration

The primary verifier exhaustively enumerates simple 14-cycles using a
minimum-rooted depth-first search with reversal symmetry removed. It finds 420
cycles. Their chord histogram in the original graph is:

| Number of chords | Cycles |
|---:|---:|
| 0 | 0 |
| 1 | 252 |
| 2 | 168 |

Thus none of the 420 simple 14-cycles is induced. Moreover, every graph edge
is the unique chord of exactly six of the one-chord cycles:
\(42\cdot6=252\).

A materially different Python verifier assembles cycles by matching pairs of
internally vertex-disjoint 7-edge paths with common endpoints. It
canonicalizes each assembled cycle under rotations and reversal, again
obtaining 420 cycles and the same chord histogram.

The C++20 checker supplies a subset-based negative test independent of both
cycle-generation schemes. It examines all
\(\binom{28}{14}=40,116,600\) vertex subsets. For each subset it computes the
complete induced degree sequence and then tests connectedness whenever every
degree is two. No subset induces a connected 2-regular graph.

## Edge deletions

For each of the 42 edges, the certificate supplies a 14-vertex cyclic order.
In the original induced subgraph, the indexed edge is the unique chord and is
not one of the cycle-order edges. Deleting it therefore leaves precisely an
induced \(C_{14}\). Both Python programs parse and validate every listed order,
check exact edge coverage, and report 42 valid cases out of 42.

The exhaustive cycle count provides a useful aggregate cross-check: the 252
unique-chord cycles are distributed uniformly, six per edge.

## Nonedge additions

An induced path on 14 vertices becomes an induced \(C_{14}\) when an edge is
added between its endpoints. With reversal identified, both Python programs
enumerate 5,040 such induced paths. Every nonedge is an endpoint pair, with the
following exact distribution:

| Original endpoint distance | Nonedges | Induced paths per pair |
|---:|---:|---:|
| 2 | 84 | 4 |
| 3 | 168 | 18 |
| 4 | 84 | 20 |

The certificate chooses one path for each of the 336 nonedges. Each stored path
has 13 consecutive graph edges, no chord, 14 distinct vertices, and the
canonical indexed nonedge as its ordered endpoints. Adding that nonedge closes
the path into an induced \(C_{14}\). Both Python implementations validate 336
cases out of 336.

## Reproducibility design

The Fano-plane construction is implemented independently in all three source
files. The stored 42-edge list and 28-entry label map are checked for exact
agreement rather than trusted. The JSON parser rejects duplicate raw keys,
noncanonical pair keys, and normalization collisions. The primary Python
program uses no third-party packages, network access, subprocesses, absolute
paths, or correctness-critical assertions.

The two Python programs share data formats but not code: one uses adjacency
sets and rooted depth-first cycle enumeration; the other uses integer masks and
meet-in-the-middle cycle assembly. The C++ program uses exhaustive fixed-size
subset enumeration. The recorded strict and sanitized builds and complete
outputs are included, but rerunning the programs is the relevant verification
step.

The candidate construction and portions of the verification software were
developed during AI-assisted computational exploration. The accompanying
programs and certificates are provided to make every mathematical claim
independently checkable.
