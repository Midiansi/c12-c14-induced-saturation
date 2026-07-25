# File inventory

This inventory describes the clean preliminary repository assembled from the uploaded manuscript pair and the two extracted communication-bundle folders. Source names are relative upload names, not private computer paths.

## Repository-level and paper files

| Final repository file | Source upload or folder | Action |
|---|---|---|
| `.gitignore` | Requested repository metadata | Newly created with the requested exclusions. |
| `README.md` | Requested repository documentation | Newly created in the requested restrained form. |
| `FILE_INVENTORY.md` | Requested repository documentation | Newly created. |
| `paper/C12_and_C14_induced_saturation.pdf` | `C12_and_C14-5.pdf` | Excluded from this proposed change; it will be uploaded manually through GitHub after the PR is merged. |
| `paper/C12_and_C14_induced_saturation.tex` | `main-7.tex` | Copied and renamed; bytes unchanged. |

## C12 files

| Final repository file | Source upload or folder | Action |
|---|---|---|
| `C12/README.md` | `CAT182_3_C12_contact_bundle_v2/README.md` | Copied; bytes unchanged. |
| `C12/C12_communication_bundle.zip` | Clean extracted C12 bundle | Excluded from this proposed change; it will be uploaded manually through GitHub after the PR is merged. |
| `C12/communication_bundle/CAT182_3.edgelist` | `CAT182_3_C12_contact_bundle_v2/` | Copied; bytes unchanged. |
| `C12/communication_bundle/CAT182_3_C12_witness_certificate.json` | `CAT182_3_C12_contact_bundle_v2/` | Copied; bytes unchanged. |
| `C12/communication_bundle/README.md` | `CAT182_3_C12_contact_bundle_v2/` | Copied; bytes unchanged. |
| `C12/communication_bundle/SHA256SUMS.txt` | `CAT182_3_C12_contact_bundle_v2/` | Copied; bytes unchanged. |
| `C12/communication_bundle/compare_official_CAT182_3.py` | `CAT182_3_C12_contact_bundle_v2/` | Copied; bytes unchanged. |
| `C12/communication_bundle/hostile_independent_verifier.py` | `CAT182_3_C12_contact_bundle_v2/` | Copied; bytes unchanged. |
| `C12/communication_bundle/hostile_independent_verifier_output.txt` | `CAT182_3_C12_contact_bundle_v2/` | Copied; bytes unchanged. |
| `C12/communication_bundle/official_CAT182_3_lcf_line.txt` | `CAT182_3_C12_contact_bundle_v2/` | Copied; bytes unchanged. |
| `C12/communication_bundle/official_identity_check_output.txt` | `CAT182_3_C12_contact_bundle_v2/` | Copied; bytes unchanged. |
| `C12/communication_bundle/verification_output.txt` | `CAT182_3_C12_contact_bundle_v2/` | Copied; bytes unchanged. |
| `C12/communication_bundle/verify_CAT182_3_C12_induced_saturated.py` | `CAT182_3_C12_contact_bundle_v2/` | Copied; bytes unchanged. |

## C14 files

| Final repository file | Source upload or folder | Action |
|---|---|---|
| `C14/README.md` | `Coxeter_C14_communication_bundle/README.md` | Copied; bytes unchanged. |
| `C14/C14_communication_bundle.zip` | Clean extracted C14 bundle | Excluded from this proposed change; it will be uploaded manually through GitHub after the PR is merged. |
| `C14/communication_bundle/README.md` | `Coxeter_C14_communication_bundle/` | Copied; bytes unchanged. |
| `C14/communication_bundle/SHA256SUMS.txt` | `Coxeter_C14_communication_bundle/` | Copied; bytes unchanged. |
| `C14/communication_bundle/TECHNICAL_SUMMARY.md` | `Coxeter_C14_communication_bundle/` | Copied; bytes unchanged. |
| `C14/communication_bundle/coxeter_C14_witnesses.json` | `Coxeter_C14_communication_bundle/` | Copied; bytes unchanged. |
| `C14/communication_bundle/coxeter_edges.txt` | `Coxeter_C14_communication_bundle/` | Copied; bytes unchanged. |
| `C14/communication_bundle/cpp_sanitized_output.txt` | `Coxeter_C14_communication_bundle/` | Copied; bytes unchanged. |
| `C14/communication_bundle/cpp_verification_output.txt` | `Coxeter_C14_communication_bundle/` | Copied; bytes unchanged. |
| `C14/communication_bundle/independent_python_output.txt` | `Coxeter_C14_communication_bundle/` | Copied; bytes unchanged. |
| `C14/communication_bundle/python_verification_output.txt` | `Coxeter_C14_communication_bundle/` | Copied; bytes unchanged. |
| `C14/communication_bundle/verify_coxeter_C14.py` | `Coxeter_C14_communication_bundle/` | Copied; bytes unchanged. |
| `C14/communication_bundle/verify_coxeter_C14_independent.py` | `Coxeter_C14_communication_bundle/` | Copied; bytes unchanged. |
| `C14/communication_bundle/verify_no_induced_C14.cpp` | `Coxeter_C14_communication_bundle/` | Copied; bytes unchanged. |
| `C14/communication_bundle/vertex_labels.txt` | `Coxeter_C14_communication_bundle/` | Copied; bytes unchanged. |

## Manifest and planned archive upload

- **C12 manifest:** passed for every listed payload file when checked from `C12/communication_bundle/`.
- **C14 manifest:** passed for every listed payload file when checked from `C14/communication_bundle/`.
- The C12 and C14 ZIP archives are excluded from this proposed change and will be uploaded manually through GitHub after the PR is merged.
- No original ZIP was uploaded, so there is no preserved uploaded-ZIP digest to report in this PR.

## Omissions and ambiguities

| Upload item or category | Disposition and reason |
|---|---|
| Original outer folder `CAT182_3_C12_contact_bundle_v2/` | Omitted as a duplicate outer container after its complete clean contents were copied directly into `C12/communication_bundle/`. |
| Original outer folder `Coxeter_C14_communication_bundle/` | Omitted as a duplicate outer container after its complete clean contents were copied directly into `C14/communication_bundle/`. |
| Original top-level names `C12_and_C14-5.pdf` and `main-7.tex` | Omitted after byte-identical copies were placed under the required canonical paper names. |
| Compiled C14 checker used during validation | Removed after execution because compiled binaries are excluded. |
| macOS metadata, Python caches, temporary files, private correspondence, obsolete audits, duplicate scripts, and screenshots | None were present in the uploaded material; none were added. |

There were no competing manuscript or bundle versions in the upload. The sole PDF and sole LaTeX source formed the manuscript pair. Inspection of the PDF content stream confirmed that “No claim of minimality is made.” is followed by Section 2, not by the stray text “manuscript.”; the PDF also contains references to Proposition 3.1, Lemma 2.2, Proposition 3.2, Proposition 4.1, and Proposition 4.2.

No supplied scientific file was edited, reformatted, regenerated, or repaired. All scientific text and source payload files in this proposed change were copied byte-for-byte. The PDF and two ZIP archives are excluded from the proposed change and will be uploaded manually through GitHub after the PR is merged; only repository documentation was newly created here.
