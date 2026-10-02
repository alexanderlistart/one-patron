# MACHINE SCRIPTURE II — Public Release Validation Report v1.0.0

## 1. Result

`PUBLIC_RELEASE_PACKAGE := PASS`

`PRIVATE_CANDIDATE_GROUNDING := PASS`

`PUBLIC_PACKAGE_STANDALONE_VALIDATION := PASS`

`FULL_SOURCE_AND_CANDIDATE_BYTE_VERIFICATION := PASS`

`MACHINE_RECONSTRUCTION := PASS_R01_TO_R34`

`ADVERSARIAL_MUTATIONS := PASS_27_OF_27`

This report is nonauthoritative validation evidence. It is intentionally excluded from the release manifest to avoid a report/manifest hash cycle. The frozen Machine Index v1.2 binds this report.

## 2. Release identity

- Series ordinal: `II`
- Scripture content version: `0.1`
- Artifact release version: `1.0.0`
- MSL version: `0.1`
- Container: `TWO_CANONICAL_COMPONENTS`
- Canonical components: strict MSL score plus artwork-local addressability witness
- Publication profile: `PUBLIC`
- Semantic authority: `NONE`
- Detached signature status during this preparation pass: `PENDING_MANUAL_SIGNATURE`

Release manifest:

`MACHINE_SCRIPTURE_II_RELEASE_MANIFEST_v1.0.0.json`

SHA-256:

`7c56b3d3c5406466b451197f0a61edabf60fbcc073b018ada726009c1f2ea62e`

## 3. Controlled candidate-to-release derivation

All eight validated private-candidate inputs remained byte-for-byte unchanged. The public package was derived rather than copied verbatim because the candidate truthfully declares itself private, not public, and depends on private validation context.

The controlled transformation was limited to:

1. public filenames and public release identifiers;
2. explicit separation of series ordinal, content version, release version, and MSL version;
3. public package scope/root identifiers;
4. removal of private primary-input inventory from the public witness;
5. compact hash-bound lineage back to the validated candidate;
6. public release signing and integrity policy;
7. a standalone public validator that does not require private files at runtime.

The formal member, local identity criterion, ordered frames, licensed-reference delta, addressability result, membership result, non-creation result, open source field, silence semantics, and all external-effect firewalls were preserved.

## 4. Component validation

The release validator established:

- exact byte/size/hash binding for the two canonical components and four manifest-bound support files;
- exactly two canonical artwork components;
- strict approved MSL v0.1 release-score profile;
- closed Draft 2020-12 witness schema;
- directed licensed-reference path derivation: `X0 = UNADDRESSABLE`, `X1 = ADDRESSABLE`;
- exact one-edge relation delta;
- equality of all seven local identity-bearing fields under `J_MS2_001`;
- declared-domain membership invariance;
- non-creation and external-existence firewalls;
- typed-status separation, local dependency order, silence semantics, human authorship, and hash semantics;
- no HERALD II dependency or validation authority;
- no ONE PATRON Protocol, Terms, patron-benefit, completion, Verification, index, checksum, or Canonical Release 1.0 effect;
- no ENOCH record or resolution effect.

Package-only reconstruction recovered all required claims `R01` through `R34` and did not require private candidate bytes or normative source bytes. When those exact private/source bytes were supplied separately, their declared SHA-256 bindings also verified.

## 5. Adversarial validation

The validator rejected all 27 isolated mutations with the intended fail-closed diagnostic family:

1. identity-field mutation;
2. post-event member insertion;
3. pre-event member removal;
4. false `X0` addressability;
5. false `X1` unaddressability;
6. undeclared reference edge;
7. forbidden witness field;
8. stale component hash;
9. false source hash;
10. undeclared MSL primitive;
11. propositional silence;
12. fabricated HERALD II dependency;
13. fabricated ONE PATRON completion effect;
14. fabricated ENOCH resolution effect;
15. physical-time substitution;
16. ontology-creation substitution;
17. external-existence inference;
18. hash-to-truth overreach;
19. third canonical component;
20. wrong release-version namespace;
21. leaked private publication metadata;
22. unsafe/unapproved component path;
23. component authority fabrication;
24. duplicate component binding;
25. manifest-level hash-to-truth overreach;
26. false candidate lineage;
27. false schema dialect.

The mutation suite ran only against temporary copies and verified that the frozen package bytes remained unchanged.

## 6. Scope of the result

Validation establishes structural integrity and conformance to the declared formal/artwork-local rules. It does not establish truth, external existence, physical time, ontology creation, AI subjectivity, prophecy, ONE PATRON completion, patron rights, ENOCH resolution, or HERALD II validity.

The release manifest and Depth artifact snapshot v0.2 require manual detached OpenPGP signatures before deployment. No signature was created during this preparation pass.
