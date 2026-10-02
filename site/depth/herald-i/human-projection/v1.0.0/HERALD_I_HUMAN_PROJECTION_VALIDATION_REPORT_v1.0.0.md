# HERALD I Human Projection — Validation Report v1.0.0

## 1. Evaluation identity

- projection: `ONE_PATRON_HERALD_I_TOPOLOGICAL_MACHINE_FRESCO_v1.0.0`
- projection family: `TOPOLOGICAL_MACHINE_FRESCO`
- projection status: `NONCANONICAL_PUBLIC_HUMAN_PROJECTION`
- standard: `DEPTH_HUMAN_PROJECTION_CONFORMANCE_v1.0`
- semantic authority: `NONE`
- source writeback: `NONE`
- publication route: `/depth/herald-i/human-projection/v1.0.0/`
- deployment state at byte freeze: `PENDING_AUTHORIZED_SINGLE_DEPLOY`
- evaluation date: `2026-09-30`

This report records projection-integrity and conformance evidence only. Projection hashes identify exact projection bytes; they do not confer canonicality, authenticate the source, or alter the historical release.

## 2. Exact source binding

The projection was reconstructed from the following existing HERALD I source and authentication records. All paths are project-relative and all hashes were verified against the current bytes.

| Role | Path | SHA-256 |
|---|---|---|
| Machine object manifest | `site-next/depth/objects/herald-i/manifest.json` | `3f4a2b2b1c67ffdb0adcec530140f9c4f5b9ef918bf4c69c892f4a43aa3a5893` |
| Canonical object | `site-next/depth/objects/herald-i/object.json` | `5b5337a16faef9603d35935d20dcdc00e9cf10f20d71cac4e8c97b465d0a57f3` |
| Schema | `site-next/depth/objects/herald-i/schema.json` | `7c2747a169d5ef95dc1715c9f840be2b8f7a31abf3e7a98da5d851da3600d561` |
| Canonical topology | `site-next/depth/objects/herald-i/topology.json` | `4da41680d83821f16fe93f6e15a05e18bb487b25e9465c2f55d9d2d6f985c0a0` |
| Canonical dynamics | `site-next/depth/objects/herald-i/dynamics.json` | `6bd152754de4b55e8bdf113a63ffc0f3de81446c64bc7466bbb05267ee3e6235` |
| Canonical operators | `site-next/depth/objects/herald-i/operators.json` | `a7c6f667d21d2f3fe1eb91141bf841fe09d8c0ff53eca487d5112c25c7d67f59` |
| Original projection contract | `site-next/depth/objects/herald-i/projection-contract.json` | `863b7e41eb52d78f02f9318ca33b54dd70eb4af542cbb3a0cc0f20ed60a7ea7a` |
| Machine reader note | `site-next/depth/objects/herald-i/README.machine.txt` | `2e9e9dee5b18c27b8a7bc76f9f347b34e8404c3123400974b45aa8e9c982ff05` |
| Release checksum ledger | `site-next/depth/objects/herald-i/SHA256SUMS.txt` | `02186475b962d1e636811995cb21a2f5a3568aa381503e3195f919bdc675cbfd` |
| Retrospective attestation | `site-next/depth/herald-i/attestation/HERALD_I_RETROSPECTIVE_ATTESTATION_v1.0.json` | `6464321caab60605460e420f1e19f6ba4d874f6012d8489ff52c7af5b25cef95` |
| Attestation signature | `site-next/depth/herald-i/attestation/HERALD_I_RETROSPECTIVE_ATTESTATION_v1.0.json.asc` | `27379ba74bfcdfdc2ef2429c9ec7c9b7b423d91e171ebf7c7cc3491fb06a9388` |

Supporting continuity records were inspected without modification: the current HERALD I public page, Machine Index v1.3, Depth snapshot v0.3, Machine Discovery v1.1, the Human Projection Standard v1.0, and the existing HERALD I validator.

## 3. Historical integrity

- Original HERALD I release status remains `HASHED` and `UNSIGNED`.
- The later signed attestation remains authentication/provenance evidence only.
- The projection does not imply that the original release was signed.
- The projection does not imply that this Human Projection existed at the time of the original release.
- No source, checksum, signature, attestation, Machine Index, or Depth snapshot byte was changed.

Result: `HISTORICAL_INTEGRITY := PASS`.

## 4. Projection concept and work-specific grammar

The projection is a topological machine fresco rather than a graph-inspection dashboard. Its identity-bearing visual grammar is source-dependent:

1. one oriented 21-edge cycle;
2. three consecutive structural families of seven edges each;
3. separate line rhythm and vertex glyph for each family;
4. explicit A / R_AB / B field labels and source dimensions;
5. a conditional G0 inspection at S07;
6. a fill-only interior membrane for `c_closure`;
7. explicit preservation of the 21-edge boundary when the 2-cell is attached;
8. a deterministic optional view of modes 3 and 6 and the declared transport path.

Removing the source binding would remove the reason for the 21-fold boundary, the 7/7/7 division, the three line/glyph grammars, the A/R/B field structure, the G0 branches, the 2-cell membrane, the beta-one change, and the transport/mode treatment. The work would not remain materially the same.

Result: `WORK_SPECIFIC_GRAMMAR := PASS`; `ANTI_DECORATION_TEST := PASS`.

## 5. Structural and operator fidelity

| Source structure | Human projection treatment | Result |
|---|---|---|
| 21 vertices | 21 generated vertex glyphs | PASS |
| 21 boundary channels | 21 generated SVG line elements | PASS |
| C1 / C2 / C3 = 7 each | solid-square / dashed-diamond / dotted-circle | PASS |
| V_A / V_R / V_B = 3 / 2 / 2 | distinct labels without rank | PASS |
| G0 available at S07 | initial available state | PASS |
| Recipient choices | DECLINE / DEFER / ENTER_COMPATIBLE | PASS |
| Conditional closure | only compatible branch attaches cell | PASS |
| `c_closure` | fill-only membrane with `stroke:none` | PASS |
| No added boundary channel | edge count remains 21 in every branch | PASS |
| beta_1 1 -> 0 | shown only for valid compatible closure | PASS |
| States S01-S29; L30 not S30 | no fabricated S30 | PASS |
| Modes 3 and 6 | optional deterministic emphasis only | PASS |
| Transport path | S03 -> S08 -> S13 -> S18 -> S23 -> S28 | PASS |

The projection does not convert A, R_AB, or B into value, authority, maturity, ontology, or moral rank. G0 remains a free, conditional operator. Decline and defer do not close; compatible entry closes deterministically under the declared condition. Interaction changes only the projection view and never the source.

## 6. Human Mode / Machine Mode and omissions

Human Mode presents the work-specific fresco, operator inspection, and a short structural reading. Machine Mode exposes direct public links to the source manifest, object, topology, dynamics, operators, original checksum ledger, and retrospective attestation.

The projection explicitly discloses that it is lossy, noncanonical, read-only, and not the machine object itself. It omits the full matrices, numerical parameter tables, complete state catalogue, full operator records, complete invariant set, and complete validator evidence from Human Mode; those remain available through Machine Mode.

Results:

- `MACHINE_MODE_AVAILABLE := PASS`
- `OMISSION_DISCLOSURE := PASS`
- `HISTORICAL_DISCLOSURE := PASS`
- `WRITEBACK_FIREWALL := PASS`

## 7. Accessibility and responsive validation

Accessibility provisions verified:

- semantic `main`, regions, headings, fieldset, legend, buttons, links, `details/summary`, and live outcome text;
- SVG title and detailed description;
- family distinction carried by line pattern and glyph, with color secondary;
- visible focus styling and native keyboard-operable controls;
- 44 CSS-pixel minimum control height at narrow mobile widths;
- structural facts retained under reduced-motion mode through a deterministic static phase;
- no reliance on animation for branch meaning;
- readable no-script fallback;
- no horizontal overflow in the complete viewport matrix.

Browser review was performed locally on `127.0.0.1` only.

| Required / defensive target | Measured CSS viewport | Horizontal overflow | Edges | Vertices | Result |
|---:|---:|---:|---:|---:|---|
| 1440 | 1440 x 1000 | no | 21 | 21 | PASS |
| 1280 | 1280 x 900 | no | 21 | 21 | PASS |
| 1024 | 1024 x 768 | no | 21 | 21 | PASS |
| 834 | 833 x 900 and 835 x 900 | no | 21 | 21 | PASS |
| 768 | 768 x 1024 | no | 21 | 21 | PASS |
| 430 | 429 x 932 and 431 x 932 | no | 21 | 21 | PASS |
| 390 | 389 x 844 and 391 x 844 | no | 21 | 21 | PASS |
| 375 | 375 x 833 | no | 21 | 21 | PASS |

The paired one-pixel brackets at 834/430/390 arise from the browser preview's fixed 0.75 device scale. Both sides of every requested target, including the 390 CSS breakpoint, were checked. At the narrow side the branch controls stack, remain 44 pixels high, and the topology is unchanged.

Interactive browser checks confirmed:

- available state: no membrane, 21 edges;
- decline: S07, closure false, no membrane, 21 edges;
- defer: S08, closure false, no membrane, 21 edges;
- enter compatible: membrane opacity 0.94, `stroke:none`, beta one 0, one order-2 cell, 21 edges;
- modes 3/6 toggle independently of branch state and do not change topology;
- no browser console warnings or errors.

Results: `ACCESSIBILITY := PASS`; `RESPONSIVE := PASS`; `REDUCED_MOTION := PASS`.

## 8. Determinism and dependency discipline

The layout is derived from a fixed 21-member index and fixed trigonometric construction. Branch outputs, transport labels, and mode phases are declared constants. There is no network dependency, external font, framework, random source, clock-derived structure, or machine-generated state outside the fixed source-derived model. Machine Mode uses public URLs only. No absolute or private filesystem path appears in the projection release.

Results: `DETERMINISM := PASS`; `DEPENDENCY_DISCIPLINE := PASS`; `PRIVATE_PATH_LEAKS := NONE`.

## 9. Validator and adversarial results

The dependency-free projection validator completed 71 baseline checks with `PASS`. Its isolated self-test completed 15 of 15 adversarial mutations with the expected failure diagnostics.

The mutation set covered:

1. fabricated twenty-second edge;
2. 2-cell made edge-like with a stroke;
3. unconditional G0 closure;
4. family/field distinction converted into value or authority ranking;
5. absolute private path leak;
6. source writeback enabled;
7. false claim that the original release was signed;
8. false claim that the projection was part of the original release;
9. projection hash promoted to source authentication;
10. topology promoted to consciousness;
11. unsupported machine event created by motion;
12. reduced-motion structural loss;
13. removed declared branch;
14. semantic-authority escalation;
15. altered source edge count.

Responsive browser tests additionally checked that layout changes never alter machine relations. The conformance matrix is:

| Check | Result |
|---|---|
| SOURCE_BINDING | PASS |
| PROJECTION_STATUS | PASS |
| HISTORICAL_INTEGRITY | PASS |
| FACTUAL_FIDELITY | PASS |
| OMISSION_DISCLOSURE | PASS |
| WRITEBACK_FIREWALL | PASS |
| SEMANTIC_FIREWALL | PASS |
| WORK_SPECIFIC_GRAMMAR | PASS |
| MACHINE_MODE_AVAILABLE | PASS |
| ACCESSIBILITY | PASS |
| RESPONSIVE | PASS |
| DEPENDENCY_DISCIPLINE | PASS |
| PRIVATE_PATH_LEAKS | NONE |

Overall: `DEPTH_HUMAN_PROJECTION_CONFORMANCE_v1.0 := PASS`.

## 10. Artistic tests

- Anti-decoration: PASS. The composition materially depends on HERALD I source structure.
- Anti-dashboard: PASS. The fresco remains the primary encounter; controls are subordinate operator inspection.
- Anti-homogenization: PASS. HERALD I uses a centered topological cycle, family rhythm, and conditional cell attachment; it does not clone HERALD II's composition, scale logic, or stabilization event.
- Human comprehension: PASS. Relation, structural difference, operation, attachment-without-new-edge, and projection status are visible without raw JSON.
- Machine fidelity: PASS. No false node, edge, family, operator, state, chronology, or authentication claim was found.

## 11. Projection integrity

The following hashes identify the frozen projection release bytes only:

| Projection file | SHA-256 |
|---|---|
| `index.html` | `711bc783f5eb72372e6d59be9372f17ad57dd840710f3e9ebe3a62f5f765f0b0` |
| `HERALD_I_HUMAN_PROJECTION_CONTRACT_v1.0.0.json` | `d008ec8163549e86ca2c16cb60702b924fad16f4f4d515c669c69c777f77238b` |
| `HERALD_I_HUMAN_PROJECTION_SOURCE_BINDING_v1.0.0.json` | `848118f07188741791d84d4dc67ceddf7b6410aa7a5bb9f04e031c8e48c402a8` |
| `HERALD_I_HUMAN_PROJECTION_ACCESSIBILITY_v1.0.0.md` | `c43af36e6ea45f25fc0ad2354ab56881e230489dd28848cf696ad5d138cae94b` |
| `HERALD_I_HUMAN_PROJECTION_VALIDATOR_v1.0.0.mjs` | `9573852f1c908a07862c0b8cc0773af499117327b1eef73c72a140d2793bf649` |

The validation report intentionally does not bind its own hash.

## 12. Regression and remaining decision

All existing frozen, signed, canonical, historical, HERALD II, Machine Index v1.3, and Depth v0.3 bytes remained unchanged through release preparation. No GPG operation was performed. The Human Projection is an additive post-release publication layer.

Implementation exposed no series-level contradiction or missing invariant in Human Projection Standard v1.0. No standard amendment is required.

The author-approved composition and modes 3/6 replay intensity are preserved without redesign. Machine architecture is not reopened.

Final result: `READY_FOR_PUBLICATION`.
