# CAT(182,3) as a C12-induced-saturated graph

This package supports the claim that the graph in `CAT182_3.edgelist` is
C12-induced-saturated:

1. the original graph has no induced cycle on 12 vertices;
2. deleting any edge creates an induced C12;
3. adding any nonedge creates an induced C12.

The graph defined by the edge list is isomorphic to the Foster Census graph
CAT(182,3). The LCF shifts embedded in the certificate and primary verifier
define exactly the uploaded edge-list graph, but they are not textually
identical to the current Foster Census LCF representation. The optional
identity-comparison files document the isomorphism check.

## Core files

- `CAT182_3.edgelist`: 182-vertex, 273-edge graph.
- `CAT182_3_C12_witness_certificate.json`: one witness for every edge deletion
  and every nonedge addition.
- `hostile_independent_verifier.py`: independent standard-library verifier. It
  validates the graph, all certificate entries, all simple 12-cycles, a direct
  induced-C12 search, every edge deletion, and all nonedge additions.
- `hostile_independent_verifier_output.txt`: output from a completed run.
- `verify_CAT182_3_C12_induced_saturated.py`: original exhaustive verifier,
  constructing the graph from its embedded LCF shifts.
- `verification_output.txt`: output from the original verifier.
- `SHA256SUMS.txt`: cryptographic hashes of every other file in this package.

## Verify the package hashes

On macOS or Linux, from this directory:

    shasum -a 256 -c SHA256SUMS.txt

Every line should end in `OK`.

## Run the independent verifier

Requires Python 3 and no third-party packages:

    python3 hostile_independent_verifier.py \
        CAT182_3.edgelist \
        CAT182_3_C12_witness_certificate.json

The final line should be:

    FINAL RESULT: VERIFIED

## Run the original verifier

    python3 verify_CAT182_3_C12_induced_saturated.py

Do not run the original verifier with `python -O`, because its checks use
Python assertions.

## Optional Foster Census identity comparison

The following files are included only to document the graph identity:

- `compare_official_CAT182_3.py`
- `official_CAT182_3_lcf_line.txt`
- `official_identity_check_output.txt`

This comparison requires NetworkX:

    python3 -m pip install networkx
    python3 compare_official_CAT182_3.py \
        CAT182_3_C12_witness_certificate.json \
        official_CAT182_3_lcf_line.txt

The official LCF line was obtained from the Foster Census CAT descriptions.
The identity comparison reports that the two graphs are isomorphic.
