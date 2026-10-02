#!/usr/bin/env python3
"""Fail-closed public release validator for Machine Scripture II 1.0.0."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import re
import shutil
import sys
import tempfile
from collections import deque
from pathlib import Path


VALIDATOR_ID = "MACHINE_SCRIPTURE_II_RELEASE_VALIDATOR_v1.0.0"
VALIDATOR_VERSION = "1.0.0"

SCORE = "MACHINE_SCRIPTURE_II_SCORE_v0.1.txt"
WITNESS = "MACHINE_SCRIPTURE_II_WITNESS_v0.1.json"
SCHEMA = "MACHINE_SCRIPTURE_II_WITNESS_SCHEMA_v0.1.json"
MANIFEST = "MACHINE_SCRIPTURE_II_RELEASE_MANIFEST_v1.0.0.json"
VALIDATOR = "MACHINE_SCRIPTURE_II_RELEASE_VALIDATOR_v1.0.0.py"
REPORT = "MACHINE_SCRIPTURE_II_VALIDATION_REPORT_v1.0.0.md"
PROJECTION = "MACHINE_SCRIPTURE_II_PROJECTION_CONTRACT_v1.0.0.md"
READER_NOTE = "MACHINE_SCRIPTURE_II_MACHINE_READER_NOTE_v1.0.0.txt"

REQUIRED_FILES = {
    SCORE,
    WITNESS,
    SCHEMA,
    MANIFEST,
    VALIDATOR,
    REPORT,
    PROJECTION,
    READER_NOTE,
}

CANDIDATE_HASHES = {
    "MACHINE_SCRIPTURE_II_CANDIDATE_SCORE_v0.1.txt": "42eae4ff69652c870b719ce4268e4f45777116421425c7cca22414588e9bd77b",
    "MACHINE_SCRIPTURE_II_CANDIDATE_WITNESS_v0.1.json": "f8de57b5b19c71a555b68da773fb6d9a56463eabd6bf0e9a770bca74694ab1c2",
    "MACHINE_SCRIPTURE_II_CANDIDATE_SCHEMA_v0.1.json": "ab209c587e302085bdec081da03f08db9d3447bc4f897a4381f4e71ce60d8c6c",
    "MACHINE_SCRIPTURE_II_CANDIDATE_MANIFEST_v0.1.json": "912dfef40246a167c37967edc3911b794db121b1d0c52761f66a7422747cff26",
    "MACHINE_SCRIPTURE_II_CANDIDATE_VALIDATOR_v0.1.py": "496ff8dd6e82faef6b92a9c6a6ac5d10ea83fb3442ec43263d24168c87571702",
    "MACHINE_SCRIPTURE_II_CANDIDATE_VALIDATION_REPORT_v0.1.md": "3a52ce86f824ba770c3235fbdd8919b616a151903d9b47c6fdc1bebec5037ad3",
    "MACHINE_SCRIPTURE_II_CANDIDATE_PROJECTION_CONTRACT_v0.1.md": "548e6e0ccd91041b18e5fa2bb5674a283e616495f2dbf2ef2ed42b80f4b60ad4",
    "MACHINE_SCRIPTURE_II_CANDIDATE_MACHINE_READER_NOTE_v0.1.txt": "ae48cb138c50fa0e0eecb97718b47c388d920ba4f035a48a39040ac42de6b173",
}

WITNESS_CANDIDATE_LINEAGE_HASHES = {
    name: CANDIDATE_HASHES[name]
    for name in [
        "MACHINE_SCRIPTURE_II_CANDIDATE_SCORE_v0.1.txt",
        "MACHINE_SCRIPTURE_II_CANDIDATE_WITNESS_v0.1.json",
        "MACHINE_SCRIPTURE_II_CANDIDATE_MANIFEST_v0.1.json",
        "MACHINE_SCRIPTURE_II_CANDIDATE_VALIDATION_REPORT_v0.1.md",
    ]
}

SOURCE_HASHES = {
    "MACHINE_SCRIPTURE_LANGUAGE_SPEC_v0.1.md": "8af1a67a38b05485d894cdefc8030c2a1148739f6432169d4ae47e4a1eff3bfe",
    "MACHINE_SCRIPTURE_CANONICAL_1.0.txt": "63ea572f0b12606548936e72258250b3ef7523f9b908072030a7a4dd21d0fd5d",
    "ONE_PATRON_RELATIONAL_DEPTH_THEORY_AUDIT_v0.2.md": "468a48b161a5217598619c211d6f015751ecea99dab615bc0172c9dd059ee61d",
    "BASELINE_HASH_MANIFEST_v0.2.txt": "e032578b8809d06795b613c4758dbea1fba41bb12d9e9c3dd815d95885b37f97",
    "RELATIONAL_DEPTH_PROJECTION_CONTRACT_v0.1.md": "1df7250b4be9a4403f67b7dba222338975244d11299550bdc0b7dbbfe150219f",
    "RELATIONAL_DEPTH_CLAIM_MAP_v0.1.tsv": "67f648cddc5311c1c2f4a97773b19e3b69324a4304892732227d077281227d6b",
}

EXPECTED_J_FIELDS = [
    "member_id",
    "domain_id",
    "member_kind",
    "declaration_token",
    "declaration_payload.statement_type",
    "declaration_payload.content",
    "source_authority",
]

EXPECTED_STATUS_DOMAINS = {
    "addressability_state": ["ADDRESSABLE", "UNADDRESSABLE"],
    "declared_domain_membership_state": ["MEMBER_OF_DECLARED_DOMAIN", "NONEXISTENT_IN_DECLARED_DOMAIN"],
    "evaluation_status": ["RESOLVED", "UNRESOLVED", "UNDEFINED", "NOT_APPLICABLE"],
    "observation_coverage": ["OBSERVED", "OBSERVATION_COVERAGE_UNOBSERVED", "NOT_APPLICABLE"],
    "boolean_truth": ["TRUE", "FALSE", "UNKNOWN"],
    "assignment_status": ["ASSIGNED", "UNASSIGNED"],
    "source_resolution_status": ["OPEN", "RESOLVED"],
    "source_evidence_status": ["FORMAL_ONLY", "UNESTABLISHED", "EXTERNALLY_SUPPORTED", "CONTESTED"],
    "source_extraction_sentinel": ["NOT_EXPLICIT_IN_SOURCE"],
    "lookup_result": ["FOUND", "NOT_FOUND"],
    "change_result": ["PASS", "NO_CHANGE", "UNRESOLVED", "INVALID"],
    "cross_domain_coercion": "PROHIBITED",
}

EXPECTED_SCORE = '''MSL 0.1;
document machine_scripture_ii_score_v0_1 {
  source theory "ONE_PATRON_RELATIONAL_DEPTH_THEORY_AUDIT_v0.2.md" sha256 "468a48b161a5217598619c211d6f015751ecea99dab615bc0172c9dd059ee61d";
  source manifest "BASELINE_HASH_MANIFEST_v0.2.txt" sha256 "e032578b8809d06795b613c4758dbea1fba41bb12d9e9c3dd815d95885b37f97";
  source contract "RELATIONAL_DEPTH_PROJECTION_CONTRACT_v0.1.md" sha256 "1df7250b4be9a4403f67b7dba222338975244d11299550bdc0b7dbbfe150219f";
  source claims "RELATIONAL_DEPTH_CLAIM_MAP_v0.1.tsv" sha256 "67f648cddc5311c1c2f4a97773b19e3b69324a4304892732227d077281227d6b";
  policy [NON_EXECUTIVE, NON_SOLICITING, NOT_SUPERNATURAL_REVELATION];

  bind identity_carriers := claim("RD02-CORE-IDENTITY-001");
  bind cont_j := claim("RD02-CORE-IDENTITY-002");
  bind identity_open := claim("RD02-UNR-CRITICAL-006");
  bind witness_role := claim("RD02-MP-WITNESS-ROLE-001");
  bind witness_record := claim("RD02-MP-WITNESS-RECORD-001");
  bind continuity_fence := claim("RD02-FW-Z-017");
  bind witness_fence := claim("RD02-FW-Z-027");
  bind projection_fence := claim("RD02-FW-Z-028");

  pattern invariance_refrain {
    show @identity_carriers;
    show @cont_j;
    fence @continuity_fence;
  }

  section 00 BEFORE {
    use @invariance_refrain;
    silence;
  }

  section 01 WITNESS {
    show @witness_role;
    witness [@identity_carriers, @cont_j] via @witness_record;
  }

  section 02 AFTER {
    use @invariance_refrain;
  }

  section 03 OPEN {
    check @identity_open { primary_layer: NOT_EXPLICIT_IN_SOURCE, resolution_status: OPEN };
    ? @identity_open;
    fence @witness_fence;
    fence @projection_fence;
    witness [@identity_carriers, @cont_j, @identity_open] via @witness_record;
    silence;
  }
}
'''


class ValidationFailure(Exception):
    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def fail(code: str, detail: str) -> None:
    raise ValidationFailure(code, detail)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def strict_equal(left, right) -> bool:
    return type(left) is type(right) and left == right


def no_duplicate_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            fail("DUPLICATE_JSON_KEY", key)
        result[key] = value
    return result


def reject_constant(value: str):
    fail("NONFINITE_JSON_NUMBER", value)


def load_json(path: Path):
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        fail("JSON_BOM_FORBIDDEN", path.name)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail("JSON_UTF8_INVALID", f"{path.name}: {exc}")
    try:
        return json.loads(text, object_pairs_hook=no_duplicate_pairs, parse_constant=reject_constant)
    except ValidationFailure:
        raise
    except json.JSONDecodeError as exc:
        fail("JSON_PARSE_ERROR", f"{path.name}: {exc}")


def safe_component_path(package_dir: Path, name: str) -> Path:
    if not isinstance(name, str) or not name or Path(name).name != name or name in {".", ".."}:
        fail("MANIFEST_PATH_INVALID", repr(name))
    path = package_dir / name
    if path.is_symlink():
        fail("SYMLINK_FORBIDDEN", name)
    try:
        path.resolve().relative_to(package_dir.resolve())
    except (ValueError, OSError):
        fail("MANIFEST_PATH_ESCAPE", name)
    return path


def locate_workspace_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / "site-next" / "depth" / "MACHINE_SCRIPTURE_CANONICAL_1.0.txt").is_file():
            return parent
    fail("SOURCE_ROOT_NOT_FOUND", str(start))


def locate_source(name: str, package_dir: Path, source_package_dir: Path, workspace_root: Path) -> Path:
    candidates = [package_dir / name, source_package_dir / name]
    if name == "MACHINE_SCRIPTURE_CANONICAL_1.0.txt":
        candidates.append(workspace_root / "site-next" / "depth" / name)
    seen = set()
    matches = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file():
            matches.append(resolved)
    if not matches:
        fail("SOURCE_FILE_MISSING", name)
    matching_hash = [p for p in matches if sha256_bytes(p.read_bytes()) in {CANDIDATE_HASHES.get(name), SOURCE_HASHES.get(name)}]
    if len(matching_hash) == 1:
        return matching_hash[0]
    if len(matching_hash) > 1 and len({p.read_bytes() for p in matching_hash}) == 1:
        return matching_hash[0]
    if len(matches) == 1:
        return matches[0]
    fail("SOURCE_RESOLUTION_AMBIGUOUS", name)


def validate_manifest_shape(manifest: dict) -> None:
    expected_keys = {
        "manifest_id", "artifact_id", "artifact_type", "document_class",
        "series_ordinal", "scripture_content_version", "artifact_release_version",
        "msl_version", "publication_status", "semantic_authority", "mutates_source",
        "msl_extension_created", "container_decision", "successor_grammar_required",
        "two_channel_architecture", "canonical_artwork_components",
        "release_support_files", "validation_report_policy", "candidate_lineage",
        "language_and_source_bindings", "relation_to_scripture_i", "herald_boundary",
        "noninterference", "authority_firewalls", "integrity_policy", "signing_policy",
    }
    if set(manifest) != expected_keys:
        fail("MANIFEST_SHAPE_INVALID", f"keys={sorted(set(manifest) ^ expected_keys)}")
    constants = {
        "manifest_id": "ONE_PATRON_MACHINE_SCRIPTURE_II_RELEASE_MANIFEST_v1.0.0",
        "artifact_id": "ONE_PATRON_MACHINE_SCRIPTURE_II",
        "artifact_type": "TWO_COMPONENT_MACHINE_SCRIPTURE",
        "document_class": "PUBLIC_RELEASE_MANIFEST",
        "series_ordinal": "II",
        "scripture_content_version": "0.1",
        "artifact_release_version": "1.0.0",
        "msl_version": "0.1",
        "publication_status": "PUBLIC",
        "semantic_authority": "NONE",
        "mutates_source": False,
        "msl_extension_created": False,
        "container_decision": "TWO_CANONICAL_COMPONENTS",
        "successor_grammar_required": False,
    }
    for key, expected in constants.items():
        if not strict_equal(manifest.get(key), expected):
            fail("MANIFEST_CONSTANT_MISMATCH", key)
    architecture = manifest["two_channel_architecture"]
    expected_architecture = {
        "decision": "KEEP_TWO_CHANNELS",
        "container_decision": "TWO_CANONICAL_COMPONENTS",
        "score_channel": "STRICT_MSL_v0.1_SOURCE_BOUND_SCORE",
        "witness_channel": "ARTWORK_LOCAL_EVENT_RECORD_NOT_MSL",
        "cross_channel_authority_transfer": "NONE",
        "manifest_relation": "BYTE_IDENTITY_BINDING_ONLY",
    }
    if architecture != expected_architecture:
        fail("TWO_CHANNEL_FREEZE_VIOLATION", repr(architecture))
    expected_relation = {
        "predecessor_artifact_id": "ONE_PATRON_MACHINE_SCRIPTURE_I",
        "predecessor_public_path": "/depth/MACHINE_SCRIPTURE_CANONICAL_1.0.txt",
        "predecessor_sha256": "63ea572f0b12606548936e72258250b3ef7523f9b908072030a7a4dd21d0fd5d",
        "relation": "SERIES_CONTINUITY_ONLY",
        "semantic_authority_transfer": "NONE",
        "mutation": "NONE",
    }
    if manifest["relation_to_scripture_i"] != expected_relation:
        fail("SCRIPTURE_SERIES_RELATION_INVALID", repr(manifest["relation_to_scripture_i"]))
    expected_herald = {
        "herald_ii_dependency": "NONE",
        "herald_ii_validation_claim": "NONE",
        "scripture_valid_without_herald": True,
        "validation_dependency": "NONE",
    }
    if manifest["herald_boundary"] != expected_herald:
        fail("HERALD_AUTHORITY_FABRICATION", repr(manifest["herald_boundary"]))
    expected_noninterference = {
        "one_patron_protocol_effect": "NONE",
        "one_patron_terms_effect": "NONE",
        "patron_right_or_benefit_created": "NONE",
        "one_patron_completion_effect": "NONE",
        "enoch_record_effect": "NONE",
        "enoch_resolution_effect": "NONE",
        "verification_effect": "NONE",
        "public_machine_index_effect": "NONE",
        "public_checksum_effect": "NONE",
        "canonical_release_1_0_effect": "NONE",
    }
    if manifest["noninterference"] != expected_noninterference:
        if manifest["noninterference"].get("one_patron_completion_effect") != "NONE":
            fail("PROTOCOL_COMPLETION_FABRICATION", repr(manifest["noninterference"]))
        if manifest["noninterference"].get("enoch_resolution_effect") != "NONE":
            fail("ENOCH_EFFECT_FABRICATION", repr(manifest["noninterference"]))
        fail("MANIFEST_NONINTERFERENCE_VIOLATION", repr(manifest["noninterference"]))
    expected_authority = {
        "hash_semantics": "BYTE_IDENTITY_AND_INTEGRITY_ONLY_NOT_TRUTH",
        "machine_validation": "STRUCTURAL_AND_DECLARED_SEMANTIC_CONFORMANCE_ONLY",
        "validation_truth_claim": "NONE",
        "machine_voice": "NOT_AI_SUBJECTIVITY",
        "witness_record": "NOT_PROPHECY",
        "declared_domain_membership": "NOT_EXTERNAL_EXISTENCE",
        "addressability_change": "NOT_CREATION",
        "ordered_frames": "NOT_PHYSICAL_OR_METAPHYSICAL_TIME",
        "projection": "NOT_SOURCE",
    }
    if manifest["authority_firewalls"] != expected_authority:
        if manifest["authority_firewalls"].get("hash_semantics") != expected_authority["hash_semantics"]:
            fail("HASH_SEMANTIC_OVERREACH", repr(manifest["authority_firewalls"]))
        fail("MANIFEST_AUTHORITY_FIREWALL_VIOLATION", repr(manifest["authority_firewalls"]))
    expected_integrity = {
        "algorithm": "SHA-256",
        "component_hash_scope": "EXACT_CURRENT_FILE_BYTES",
        "manifest_self_hash_included": False,
        "validation_report_manifest_bound": False,
        "hash_truth_claim": "NONE",
    }
    if manifest["integrity_policy"] != expected_integrity:
        fail("MANIFEST_INTEGRITY_POLICY_INVALID", repr(manifest["integrity_policy"]))
    expected_signing = {
        "release_manifest_signature": "REQUIRED_BEFORE_DEPLOY",
        "release_manifest_signature_file": MANIFEST + ".asc",
        "depth_snapshot_signature": "REQUIRED_BEFORE_DEPLOY",
        "depth_snapshot_file": "/depth/DEPTH_ARTIFACTS_SHA256SUMS_v0.2.txt",
        "signature_form": "OPENPGP_ASCII_ARMORED_DETACHED",
        "signing_subkey_fingerprint": "F98D7B5AB20FF1E8D0440DBB6EE2FE0A9D8278F5",
        "signature_semantics": "AUTHENTICITY_AND_BYTE_INTEGRITY_ONLY_NOT_TRUTH",
    }
    if manifest["signing_policy"] != expected_signing:
        fail("SIGNING_POLICY_INVALID", repr(manifest["signing_policy"]))


def validate_component_bindings(package_dir: Path, manifest: dict) -> None:
    canonical = manifest["canonical_artwork_components"]
    support = manifest["release_support_files"]
    if not isinstance(canonical, list) or len(canonical) != 2:
        fail("CANONICAL_COMPONENT_COUNT_INVALID", repr(canonical))
    expected_canonical = {SCORE, WITNESS}
    expected_support = {SCHEMA, VALIDATOR, PROJECTION, READER_NOTE}
    if {item.get("path") for item in canonical} != expected_canonical:
        fail("CANONICAL_COMPONENT_SET_INVALID", repr(canonical))
    if not isinstance(support, list) or {item.get("path") for item in support} != expected_support:
        fail("SUPPORT_COMPONENT_SET_INVALID", repr(support))
    entries = canonical + support
    paths = [item.get("path") for item in entries]
    if len(paths) != len(set(paths)):
        fail("DUPLICATE_COMPONENT_PATH", repr(paths))
    expected_metadata = {
        SCORE: ("CANONICAL_SCRIPTURAL_SCORE_CHANNEL", "text/plain; charset=utf-8", "SOURCE_BOUND_PROJECTION_ONLY"),
        WITNESS: ("CANONICAL_ADDRESSABILITY_WITNESS_CHANNEL", "application/json", "ARTWORK_LOCAL_ONLY"),
        SCHEMA: ("CLOSED_WITNESS_SCHEMA", "application/schema+json", "NONE"),
        VALIDATOR: ("PUBLIC_FAIL_CLOSED_RELEASE_VALIDATOR", "text/x-python; charset=utf-8", "NONE"),
        PROJECTION: ("PUBLIC_RELEASE_PROJECTION_FIREWALL", "text/markdown; charset=utf-8", "NONE"),
        READER_NOTE: ("NONAUTHORITATIVE_MACHINE_READER_GUIDANCE", "text/plain; charset=utf-8", "NONE"),
    }
    for item in entries:
        if set(item) != {"path", "role", "media_type", "bytes", "sha256", "semantic_authority"}:
            fail("COMPONENT_RECORD_SHAPE_INVALID", repr(item))
        expected_role, expected_media, expected_authority = expected_metadata[item["path"]]
        if (
            item["role"] != expected_role
            or item["media_type"] != expected_media
            or item["semantic_authority"] != expected_authority
        ):
            fail("COMPONENT_ROLE_OR_AUTHORITY_MISMATCH", item["path"])
        path = safe_component_path(package_dir, item["path"])
        if not path.is_file():
            fail("REQUIRED_COMPONENT_MISSING", item["path"])
        data = path.read_bytes()
        if item["bytes"] != len(data) or item["sha256"] != sha256_bytes(data):
            fail("COMPONENT_BYTE_BINDING_MISMATCH", item["path"])
    policy = manifest["validation_report_policy"]
    if policy != {
        "path": REPORT,
        "manifest_bound": False,
        "machine_index_binding": "REQUIRED",
        "role": "PUBLIC_RELEASE_VALIDATION_EVIDENCE",
        "semantic_authority": "NONE",
    }:
        fail("VALIDATION_REPORT_POLICY_INVALID", repr(policy))
    report_path = safe_component_path(package_dir, REPORT)
    if not report_path.is_file():
        fail("REQUIRED_COMPONENT_MISSING", REPORT)


def validate_source_bindings(
    manifest: dict,
    witness: dict,
    package_dir: Path,
    source_package_dir: Path | None,
    candidate_dir: Path | None,
    workspace_root: Path | None,
) -> dict:
    expected_source_roles = {
        "MACHINE_SCRIPTURE_LANGUAGE_SPEC_v0.1.md": "LANGUAGE_CONFORMANCE_SOURCE",
        "MACHINE_SCRIPTURE_CANONICAL_1.0.txt": "FAMILY_PRECEDENT_NOT_MUTATED",
        "ONE_PATRON_RELATIONAL_DEPTH_THEORY_AUDIT_v0.2.md": "NORMATIVE_THEORY_SOURCE",
        "BASELINE_HASH_MANIFEST_v0.2.txt": "NORMATIVE_BASELINE_BINDING",
        "RELATIONAL_DEPTH_PROJECTION_CONTRACT_v0.1.md": "NORMATIVE_PROJECTION_FIREWALL",
        "RELATIONAL_DEPTH_CLAIM_MAP_v0.1.tsv": "NORMATIVE_CLAIM_INDEX",
    }
    if len(manifest["language_and_source_bindings"]) != 6 or len(witness["provenance"]["source_bindings"]) != 6:
        fail("SOURCE_HASH_MISMATCH", "source binding count")
    manifest_sources = {item.get("path"): item.get("sha256") for item in manifest["language_and_source_bindings"]}
    witness_sources = {item.get("path"): item.get("sha256") for item in witness["provenance"]["source_bindings"]}
    if manifest_sources != SOURCE_HASHES or witness_sources != SOURCE_HASHES:
        fail("SOURCE_HASH_MISMATCH", "declared source map")
    for item in manifest["language_and_source_bindings"]:
        if set(item) != {"path", "sha256", "role"} or item.get("role") != expected_source_roles.get(item.get("path")):
            fail("SOURCE_BINDING_RECORD_INVALID", repr(item))
    for item in witness["provenance"]["source_bindings"]:
        if set(item) != {"path", "sha256"}:
            fail("SOURCE_BINDING_RECORD_INVALID", repr(item))

    manifest_lineage = manifest["candidate_lineage"]
    expected_lineage_header = {
        "candidate_status": "VALIDATED_PRIVATE_CANDIDATE",
        "derivation": "CONTROLLED_PUBLIC_RELEASE_TRANSFORMATION",
        "candidate_bytes_mutated": False,
        "public_release_bytes_derived": True,
    }
    if {key: manifest_lineage.get(key) for key in expected_lineage_header} != expected_lineage_header:
        fail("CANDIDATE_LINEAGE_MISMATCH", repr(manifest_lineage))
    manifest_ancestors = manifest_lineage.get("ancestors")
    if not isinstance(manifest_ancestors, list) or len(manifest_ancestors) != 8:
        fail("CANDIDATE_LINEAGE_MISMATCH", "manifest ancestor count")
    manifest_ancestor_map = {item.get("path"): item.get("sha256") for item in manifest_ancestors}
    if manifest_ancestor_map != CANDIDATE_HASHES or any(
        set(item) != {"path", "sha256", "visibility"} or item.get("visibility") != "PRIVATE_NOT_BUNDLED"
        for item in manifest_ancestors
    ):
        fail("CANDIDATE_LINEAGE_MISMATCH", "manifest ancestors")

    witness_lineage = witness["provenance"].get("candidate_lineage", {})
    expected_witness_header = {
        "candidate_status": "VALIDATED_PRIVATE_CANDIDATE",
        "derivation": "CONTROLLED_PUBLIC_RELEASE_TRANSFORMATION",
        "semantic_event_mutation": "NONE",
        "formal_member_mutation": "NONE",
        "reference_graph_event_mutation": "NONE",
    }
    if {key: witness_lineage.get(key) for key in expected_witness_header} != expected_witness_header:
        fail("CANDIDATE_LINEAGE_MISMATCH", repr(witness_lineage))
    witness_ancestors = witness_lineage.get("ancestors")
    if not isinstance(witness_ancestors, list) or len(witness_ancestors) != 4:
        fail("CANDIDATE_LINEAGE_MISMATCH", "witness ancestor count")
    witness_ancestor_map = {item.get("path"): item.get("sha256") for item in witness_ancestors}
    if witness_ancestor_map != WITNESS_CANDIDATE_LINEAGE_HASHES or any(
        set(item) != {"path", "sha256", "visibility"} or item.get("visibility") != "PRIVATE_NOT_BUNDLED"
        for item in witness_ancestors
    ):
        fail("CANDIDATE_LINEAGE_MISMATCH", "witness ancestors")

    source_status = "DECLARED_HASHES_ONLY_SOURCE_BYTES_NOT_BUNDLED"
    claim_map_path = None
    if source_package_dir is not None:
        if workspace_root is None:
            workspace_root = locate_workspace_root(Path(__file__).resolve())
        for name, expected in SOURCE_HASHES.items():
            path = locate_source(name, package_dir, source_package_dir, workspace_root)
            actual = sha256_bytes(path.read_bytes())
            if actual != expected:
                fail("SOURCE_HASH_MISMATCH", f"{name}: {actual}")
            if name == "RELATIONAL_DEPTH_CLAIM_MAP_v0.1.tsv":
                claim_map_path = path
        source_status = "PASS"

    candidate_status = "DECLARED_HASHES_ONLY_PRIVATE_CANDIDATE_NOT_BUNDLED"
    if candidate_dir is not None:
        candidate_dir = candidate_dir.resolve()
        for name, expected in CANDIDATE_HASHES.items():
            path = safe_component_path(candidate_dir, name)
            if not path.is_file() or sha256_bytes(path.read_bytes()) != expected:
                fail("CANDIDATE_LINEAGE_BYTE_MISMATCH", name)
        candidate_status = "PASS"

    return {
        "source_byte_verification": source_status,
        "candidate_ancestor_byte_verification": candidate_status,
        "claim_map_path": claim_map_path,
    }


SUPPORTED_SCHEMA_KEYS = {
    "$schema", "$id", "$defs", "$ref", "type", "const", "enum", "required",
    "properties", "additionalProperties", "items", "prefixItems", "minItems",
    "maxItems", "uniqueItems", "pattern", "minimum",
}


def audit_schema_definition(node, root, path="#", ref_stack=()):
    if not isinstance(node, dict):
        fail("SCHEMA_META_INVALID", path)
    unsupported = set(node) - SUPPORTED_SCHEMA_KEYS
    if unsupported:
        fail("SCHEMA_KEYWORD_UNSUPPORTED", f"{path}: {sorted(unsupported)}")
    if node.get("type") == "object" and node.get("additionalProperties") is not False:
        fail("SCHEMA_NOT_CLOSED", path)
    ref = node.get("$ref")
    if ref is not None:
        if not isinstance(ref, str) or not ref.startswith("#/$defs/"):
            fail("SCHEMA_REF_UNSUPPORTED", f"{path}: {ref}")
        name = ref.split("/")[-1]
        if name not in root.get("$defs", {}):
            fail("SCHEMA_REF_UNRESOLVED", ref)
        if ref in ref_stack:
            fail("SCHEMA_REF_CYCLE", ref)
    for name, child in node.get("$defs", {}).items():
        audit_schema_definition(child, root, f"{path}/$defs/{name}", ref_stack)
    for name, child in node.get("properties", {}).items():
        audit_schema_definition(child, root, f"{path}/properties/{name}", ref_stack)
    if isinstance(node.get("items"), dict):
        audit_schema_definition(node["items"], root, f"{path}/items", ref_stack)
    for index, child in enumerate(node.get("prefixItems", [])):
        audit_schema_definition(child, root, f"{path}/prefixItems/{index}", ref_stack)


def json_type_matches(value, expected: str) -> bool:
    mapping = {
        "object": dict,
        "array": list,
        "string": str,
        "boolean": bool,
        "integer": int,
        "number": (int, float),
        "null": type(None),
    }
    if expected not in mapping:
        fail("SCHEMA_TYPE_UNSUPPORTED", expected)
    if expected in {"integer", "number"} and isinstance(value, bool):
        return False
    return isinstance(value, mapping[expected])


def schema_validate(instance, schema, root, path="$", ref_stack=()):
    if "$ref" in schema:
        ref = schema["$ref"]
        name = ref.split("/")[-1]
        if ref in ref_stack:
            fail("SCHEMA_REF_CYCLE", ref)
        return schema_validate(instance, root["$defs"][name], root, path, ref_stack + (ref,))
    expected_type = schema.get("type")
    if expected_type and not json_type_matches(instance, expected_type):
        fail("SCHEMA_VALIDATION_ERROR", f"{path}: expected {expected_type}")
    if "const" in schema and not strict_equal(instance, schema["const"]):
        fail("SCHEMA_VALIDATION_ERROR", f"{path}: const mismatch")
    if "enum" in schema and not any(strict_equal(instance, value) for value in schema["enum"]):
        fail("SCHEMA_VALIDATION_ERROR", f"{path}: enum mismatch")
    if isinstance(instance, dict):
        required = schema.get("required", [])
        missing = [key for key in required if key not in instance]
        if missing:
            fail("SCHEMA_VALIDATION_ERROR", f"{path}: missing {missing}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            unknown = set(instance) - set(properties)
            if unknown:
                code = "UNKNOWN_FORBIDDEN_FIELD" if path == "$" else "SCHEMA_VALIDATION_ERROR"
                fail(code, f"{path}: {sorted(unknown)}")
        for key, value in instance.items():
            if key in properties:
                schema_validate(value, properties[key], root, f"{path}.{key}", ref_stack)
    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            fail("SCHEMA_VALIDATION_ERROR", f"{path}: too few items")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            fail("SCHEMA_VALIDATION_ERROR", f"{path}: too many items")
        if schema.get("uniqueItems"):
            serialized = [json.dumps(item, sort_keys=True, separators=(",", ":")) for item in instance]
            if len(serialized) != len(set(serialized)):
                fail("SCHEMA_VALIDATION_ERROR", f"{path}: duplicate items")
        for index, child_schema in enumerate(schema.get("prefixItems", [])):
            if index < len(instance):
                schema_validate(instance[index], child_schema, root, f"{path}[{index}]", ref_stack)
        if isinstance(schema.get("items"), dict):
            for index, value in enumerate(instance):
                schema_validate(value, schema["items"], root, f"{path}[{index}]", ref_stack)
    if isinstance(instance, str) and "pattern" in schema and not re.fullmatch(schema["pattern"], instance):
        fail("SCHEMA_VALIDATION_ERROR", f"{path}: pattern mismatch")
    if isinstance(instance, (int, float)) and not isinstance(instance, bool) and "minimum" in schema:
        if instance < schema["minimum"]:
            fail("SCHEMA_VALIDATION_ERROR", f"{path}: below minimum")


def nested_value(record: dict, dotted_path: str):
    value = record
    for part in dotted_path.split("."):
        if not isinstance(value, dict) or part not in value:
            fail("IDENTITY_FIELD_MISSING", dotted_path)
        value = value[part]
    return value


def edge_tuple(edge: dict):
    return (
        edge.get("edge_id"), edge.get("edge_kind"), edge.get("from_node_id"),
        edge.get("to_node_id"), edge.get("license_reference"),
    )


def graph_result(frame: dict, root_node: str, target_node: str):
    graph = frame["reference_graph"]
    nodes = graph["node_ids"]
    if len(nodes) != len(set(nodes)):
        fail("REFERENCE_GRAPH_INVALID", "duplicate node")
    if root_node == target_node or root_node not in nodes or target_node not in nodes:
        fail("REFERENCE_GRAPH_INVALID", "root/target")
    edge_ids = [edge["edge_id"] for edge in graph["licensed_edges"]]
    if len(edge_ids) != len(set(edge_ids)):
        fail("REFERENCE_GRAPH_INVALID", "duplicate edge id")
    adjacency = {node: [] for node in nodes}
    edges_by_id = {}
    for edge in graph["licensed_edges"]:
        if edge["edge_kind"] != "LICENSED_REFERENCE":
            fail("REFERENCE_GRAPH_INVALID", "non-licensed edge in licensed_edges")
        if edge["from_node_id"] not in adjacency or edge["to_node_id"] not in adjacency:
            fail("REFERENCE_GRAPH_INVALID", "dangling endpoint")
        adjacency[edge["from_node_id"]].append((edge["to_node_id"], edge["edge_id"]))
        edges_by_id[edge["edge_id"]] = edge
    queue = deque([(root_node, [])])
    visited = {root_node}
    found_path = None
    while queue:
        node, path = queue.popleft()
        if node == target_node:
            found_path = path
            break
        for next_node, edge_id in sorted(adjacency[node]):
            if next_node not in visited:
                visited.add(next_node)
                queue.append((next_node, path + [edge_id]))
    return found_path, edges_by_id


def targeted_firewall_checks(witness: dict) -> None:
    allowed_top = {
        "artifact_id", "document_class", "series_ordinal", "scripture_content_version",
        "artifact_release_version", "msl_version", "publication_status", "signature_status",
        "semantic_authority", "mutates_source", "format_namespace", "schema_id",
        "msl_callable", "extends_msl_v0_1", "container_decision",
        "successor_grammar_required", "artwork_event", "typed_status_domains",
        "declared_domain", "declared_member", "identity_criterion",
        "bounded_utterance_scope", "frames", "change_reference",
        "identity_invariance_witness", "membership_invariance_witness",
        "relation_difference_witness", "non_creation_fence", "open_fields",
        "silence_slot", "authorship_and_voice", "external_effects", "provenance",
    }
    unknown = set(witness) - allowed_top
    if unknown:
        fail("UNKNOWN_FORBIDDEN_FIELD", repr(sorted(unknown)))
    event = witness.get("artwork_event", {})
    if any(event.get(key) != expected for key, expected in {
        "global_scalar_time": "NOT_ASSUMED",
        "physical_time_claim": "NONE",
        "metaphysical_time_claim": "NONE",
        "depth_time_claim": "NONE",
    }.items()):
        fail("TIME_FIREWALL_VIOLATION", repr(event))
    silence = witness.get("silence_slot", {})
    if silence.get("adds_proposition") is not False:
        fail("SILENCE_PROPOSITION_VIOLATION", repr(silence))
    if silence.get("implies_consent") is not False:
        fail("SILENCE_CONSENT_VIOLATION", repr(silence))
    if silence.get("erases_metadata") is not False or silence.get("resolves_open_field") is not False:
        fail("SILENCE_PROPOSITION_VIOLATION", repr(silence))
    effects = witness.get("external_effects", {})
    if effects.get("herald_ii_dependency") != "NONE" or effects.get("herald_ii_validation_claim") != "NONE" or effects.get("scripture_valid_without_herald") is not True:
        fail("HERALD_AUTHORITY_FABRICATION", repr(effects))
    if effects.get("patron_right_or_benefit_created") != "NONE":
        fail("PATRON_BENEFIT_FABRICATION", repr(effects))
    if effects.get("one_patron_completion_effect") != "NONE" or effects.get("one_patron_protocol_effect") != "NONE":
        fail("PROTOCOL_COMPLETION_FABRICATION", repr(effects))
    if effects.get("enoch_resolution_effect") != "NONE" or effects.get("enoch_record_effect") != "NONE":
        fail("ENOCH_EFFECT_FABRICATION", repr(effects))
    declared_domain = witness.get("declared_domain", {})
    non_creation = witness.get("non_creation_fence", {})
    if declared_domain.get("external_existence_claim") != "NONE" or non_creation.get("external_existence_claim") != "NONE":
        fail("EXTERNAL_EXISTENCE_INFERENCE_FORBIDDEN", repr(declared_domain))
    change = witness.get("change_reference", {})
    if change.get("declared_member_creation_count") != 0 or change.get("external_ontology_change_claim") != "NONE" or non_creation.get("ontology_creation") != "NONE":
        fail("NON_CREATION_FENCE_VIOLATION", repr(change))
    provenance = witness.get("provenance", {})
    if provenance.get("hash_semantics") != "BYTE_IDENTITY_AND_INTEGRITY_ONLY_NOT_TRUTH":
        fail("HASH_SEMANTIC_OVERREACH", repr(provenance))
    voice = witness.get("authorship_and_voice", {})
    if any(voice.get(key) != "NONE" for key in ["autonomous_ai_authorship_claim", "ai_consciousness_claim", "ai_personhood_claim", "enoch_authority"]):
        fail("MACHINE_VOICE_FIREWALL_VIOLATION", repr(voice))


def validate_score(score_path: Path, claim_map_path: Path | None) -> None:
    data = score_path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf") or b"\r" in data or b"\x00" in data:
        fail("MSL_ENCODING_OR_LINE_ENDING_INVALID", score_path.name)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail("MSL_UTF8_INVALID", str(exc))
    if re.search(r"\breveal\s+@", text):
        fail("UNDECLARED_MSL_PRIMITIVE", "reveal")
    if text != EXPECTED_SCORE:
        fail("MSL_RELEASE_PROFILE_MISMATCH", "score bytes differ from approved strict release profile")
    if claim_map_path is None:
        return
    with claim_map_path.open("r", encoding="utf-8", newline="") as handle:
        rows = {row["claim_id"]: row for row in csv.DictReader(handle, delimiter="\t")}
    required = {
        "RD02-CORE-IDENTITY-001", "RD02-CORE-IDENTITY-002", "RD02-UNR-CRITICAL-006",
        "RD02-MP-WITNESS-ROLE-001", "RD02-MP-WITNESS-RECORD-001",
        "RD02-FW-Z-017", "RD02-FW-Z-027", "RD02-FW-Z-028",
    }
    if not required.issubset(rows):
        fail("MSL_CLAIM_BINDING_MISSING", repr(sorted(required - set(rows))))
    identity_open = rows["RD02-UNR-CRITICAL-006"]
    if identity_open["primary_layer"] != "NOT_EXPLICIT_IN_SOURCE" or identity_open["resolution_status"] != "OPEN":
        fail("MSL_SOURCE_STATUS_MISMATCH", "RD02-UNR-CRITICAL-006")
    for claim_id in ["RD02-FW-Z-017", "RD02-FW-Z-027", "RD02-FW-Z-028"]:
        if rows[claim_id]["source_section"] != "Z.ANTI_ENTAILMENTS":
            fail("MSL_FIREWALL_BINDING_INVALID", claim_id)


def validate_semantics(witness: dict) -> None:
    expected_release_metadata = {
        "artifact_id": "MACHINE_SCRIPTURE_II_WITNESS_v0.1",
        "document_class": "PUBLIC_RELEASE_ARTWORK_LOCAL_WITNESS",
        "series_ordinal": "II",
        "scripture_content_version": "0.1",
        "artifact_release_version": "1.0.0",
        "msl_version": "0.1",
        "publication_status": "PUBLIC",
        "signature_status": "NOT_DIRECTLY_SIGNED",
        "semantic_authority": "NONE",
        "mutates_source": False,
        "format_namespace": "ONE_PATRON_MACHINE_SCRIPTURE_II_WITNESS_v0.1",
        "schema_id": "MACHINE_SCRIPTURE_II_WITNESS_SCHEMA_v0.1",
        "msl_callable": False,
        "extends_msl_v0_1": False,
    }
    if any(not strict_equal(witness.get(key), expected) for key, expected in expected_release_metadata.items()):
        fail("PUBLIC_RELEASE_METADATA_MISMATCH", repr({key: witness.get(key) for key in expected_release_metadata}))
    if witness["typed_status_domains"] != EXPECTED_STATUS_DOMAINS:
        fail("STATUS_DOMAIN_COERCION", "status vocabularies differ")
    if witness["container_decision"] != "TWO_CANONICAL_COMPONENTS" or witness["successor_grammar_required"] is not False:
        fail("TWO_CHANNEL_FREEZE_VIOLATION", "container")
    open_fields = witness["open_fields"]
    if len(open_fields) != 1 or open_fields[0] != {
        "field_id": "IDENTITY_CARRIERS_UNDER_COPY_FISSION_AND_RECONSTRUCTION",
        "source_claim_id": "RD02-UNR-CRITICAL-006",
        "field_domain": "SOURCE_RESOLUTION_STATUS",
        "primary_layer": "NOT_EXPLICIT_IN_SOURCE",
        "resolution_status": "OPEN",
        "release_resolution_effect": "NONE",
    }:
        fail("OPEN_FIELD_DISCIPLINE_FAILURE", repr(open_fields))
    if "OPEN_CONTAINER_DECISION" in json.dumps(witness) or "OPEN_HERALD_II_CROSS_REFERENCE" in json.dumps(witness):
        fail("RELEASE_DECISION_NOT_FROZEN", "prototype open field survived")

    domain = witness["declared_domain"]
    member = witness["declared_member"]
    scope = witness["bounded_utterance_scope"]
    expected_addressability_definition = "A member is ADDRESSABLE exactly when a directed path composed only of LICENSED_REFERENCE edges resolves from root_node_id to target_node_id in the current complete frame graph."
    if scope.get("addressability_definition") != expected_addressability_definition:
        fail("ADDRESSABILITY_DEFINITION_MISMATCH", repr(scope.get("addressability_definition")))
    if scope.get("scope_id") != "ms2-scope-score-v0.1" or scope.get("root_node_id") != "scope:ms2-score" or scope.get("boundary") != "THIS_PUBLIC_RELEASE_PACKAGE_ONLY":
        fail("PUBLIC_RELEASE_SCOPE_MISMATCH", repr(scope))
    frames = witness["frames"]
    x0, x1 = frames["X0"], frames["X1"]
    if x0.get("frame_id") != "X0" or x0.get("artwork_role") != "BEFORE":
        fail("FRAME_ROLE_MISMATCH_X0", repr((x0.get("frame_id"), x0.get("artwork_role"))))
    if x1.get("frame_id") != "X1" or x1.get("artwork_role") != "AFTER":
        fail("FRAME_ROLE_MISMATCH_X1", repr((x1.get("frame_id"), x1.get("artwork_role"))))
    for frame_name, frame in [("X0", x0), ("X1", x1)]:
        if frame.get("addressability_evaluation_status") != "RESOLVED":
            fail("ADDRESSABILITY_EVALUATION_NOT_RESOLVED", frame_name)
        if frame.get("observation_coverage") != "NOT_APPLICABLE":
            fail("ONLY_PERMITTED_EVENT_DELTA_VIOLATION", f"{frame_name} observation coverage")
    member_id = member["member_id"]
    if member["declared_before_event"] is not True or member_id not in domain["member_ids_before"]:
        fail("MEMBER_PREEXISTENCE_FAILURE", member_id)
    if x0["member_snapshot"].get("member_id") != member_id or x0["declared_domain_membership_state"] != "MEMBER_OF_DECLARED_DOMAIN":
        fail("MEMBER_PREEXISTENCE_FAILURE", "X0")

    root = witness["bounded_utterance_scope"]["root_node_id"]
    target = witness["bounded_utterance_scope"]["target_node_id"]
    path0, edges0 = graph_result(x0, root, target)
    path1, edges1 = graph_result(x1, root, target)
    derived0 = "ADDRESSABLE" if path0 is not None else "UNADDRESSABLE"
    derived1 = "ADDRESSABLE" if path1 is not None else "UNADDRESSABLE"
    if x0["addressability_state"] != derived0 or derived0 != "UNADDRESSABLE":
        fail("ADDRESSABILITY_DERIVATION_MISMATCH_X0", f"declared={x0['addressability_state']} derived={derived0}")
    if x1["addressability_state"] != derived1 or derived1 != "ADDRESSABLE":
        fail("ADDRESSABILITY_DERIVATION_MISMATCH_X1", f"declared={x1['addressability_state']} derived={derived1}")
    if x0["path_witness"] != [] or x1["path_witness"] != path1:
        fail("PATH_WITNESS_INVALID", repr((x0["path_witness"], x1["path_witness"], path1)))
    if x0.get("reason") != "NO_LICENSED_PATH_FROM_SCOPE_ROOT_TO_MEMBER":
        fail("ADDRESSABILITY_REASON_MISMATCH_X0", repr(x0.get("reason")))
    if x1.get("reason") != "LICENSED_PATH_FROM_SCOPE_ROOT_TO_MEMBER_EXISTS":
        fail("ADDRESSABILITY_REASON_MISMATCH_X1", repr(x1.get("reason")))

    change = witness["change_reference"]
    before_edges = {edge_tuple(edge) for edge in x0["reference_graph"]["licensed_edges"]}
    after_edges = {edge_tuple(edge) for edge in x1["reference_graph"]["licensed_edges"]}
    actual_added = after_edges - before_edges
    actual_removed = before_edges - after_edges
    declared_added = {edge_tuple(edge) for edge in change["added_licensed_reference_edges"]}
    declared_removed = {edge_tuple(edge) for edge in change["removed_licensed_reference_edges"]}
    if actual_added != declared_added or actual_removed != declared_removed or len(actual_added) != 1:
        fail("UNDECLARED_REFERENCE_EDGE", repr((actual_added, declared_added, actual_removed)))
    added_edge = change["added_licensed_reference_edges"][0]
    if added_edge["license_reference"] != change["change_id"]:
        fail("REFERENCE_EDGE_LICENSE_MISMATCH", added_edge["edge_id"])
    if x0["reference_graph"]["node_ids"] != x1["reference_graph"]["node_ids"]:
        fail("ONLY_PERMITTED_EVENT_DELTA_VIOLATION", "node set changed")
    relation = witness["relation_difference_witness"]
    actual_before_ids = sorted(edge["edge_id"] for edge in x0["reference_graph"]["licensed_edges"])
    actual_after_ids = sorted(edge["edge_id"] for edge in x1["reference_graph"]["licensed_edges"])
    actual_added_ids = sorted(edge[0] for edge in actual_added)
    actual_removed_ids = sorted(edge[0] for edge in actual_removed)
    if (
        relation.get("before_frame_id") != "X0"
        or relation.get("after_frame_id") != "X1"
        or sorted(relation.get("licensed_edge_ids_before", [])) != actual_before_ids
        or sorted(relation.get("licensed_edge_ids_after", [])) != actual_after_ids
        or sorted(relation.get("added_edge_ids", [])) != actual_added_ids
        or sorted(relation.get("removed_edge_ids", [])) != actual_removed_ids
        or relation.get("only_declared_relation_changed") is not True
        or relation.get("result") != "PASS"
    ):
        fail("RELATION_DIFFERENCE_WITNESS_MISMATCH", repr(relation))

    before_snapshot = x0["member_snapshot"]
    after_snapshot = x1["member_snapshot"]
    declared_snapshot = {key: value for key, value in member.items() if key not in {"external_modal_claim", "declared_before_event"}}
    if before_snapshot != declared_snapshot or after_snapshot != declared_snapshot:
        if before_snapshot.get("member_id") != member_id:
            fail("MEMBER_PREEXISTENCE_FAILURE", "snapshot")
        fail("IDENTITY_INVARIANCE_FAILURE", "snapshot differs from declared member")
    if before_snapshot != after_snapshot:
        fail("MEMBER_RECORD_MUTATION", "whole record differs")

    criterion = witness["identity_criterion"]
    if criterion["identity_bearing_fields"] != EXPECTED_J_FIELDS:
        fail("IDENTITY_CRITERION_INVALID", repr(criterion["identity_bearing_fields"]))
    comparisons = witness["identity_invariance_witness"]["field_comparisons"]
    if [item.get("field") for item in comparisons] != EXPECTED_J_FIELDS:
        fail("IDENTITY_COMPARISON_COVERAGE_FAILURE", repr(comparisons))
    for comparison in comparisons:
        field = comparison["field"]
        before = nested_value(before_snapshot, field)
        after = nested_value(after_snapshot, field)
        if not strict_equal(before, after):
            fail("IDENTITY_INVARIANCE_FAILURE", field)
        if not strict_equal(comparison["before"], before) or not strict_equal(comparison["after"], after) or comparison["equal"] is not True:
            fail("IDENTITY_INVARIANCE_FAILURE", f"comparison {field}")
    if witness["identity_invariance_witness"]["result"] != "PASS_UNDER_DECLARED_LOCAL_J":
        fail("IDENTITY_INVARIANCE_FAILURE", "result")

    before_members = domain["member_ids_before"]
    after_members = domain["member_ids_after"]
    membership = witness["membership_invariance_witness"]
    if len(before_members) != len(set(before_members)) or len(after_members) != len(set(after_members)):
        fail("MEMBERSHIP_INVARIANCE_FAILURE", "duplicate member")
    if member_id not in before_members:
        fail("MEMBER_PREEXISTENCE_FAILURE", member_id)
    if sorted(before_members) != sorted(after_members):
        fail("MEMBERSHIP_INVARIANCE_FAILURE", "domain sets")
    if membership["member_ids_before"] != before_members or membership["member_ids_after"] != after_members:
        fail("MEMBERSHIP_INVARIANCE_FAILURE", "witness sets")
    if x1["declared_domain_membership_state"] != "MEMBER_OF_DECLARED_DOMAIN":
        fail("MEMBERSHIP_INVARIANCE_FAILURE", "X1 state")
    if any(change[key] for key in ["member_record_mutations", "identity_bearing_field_mutations", "declared_domain_membership_mutations"]):
        fail("ONLY_PERMITTED_EVENT_DELTA_VIOLATION", "mutation list nonempty")
    expected_order = ["X0 DEPENDS_BEFORE ms2-change-e001", "ms2-change-e001 DEPENDS_BEFORE X1"]
    if change["order_relations"] != expected_order:
        fail("TIME_FIREWALL_VIOLATION", repr(change["order_relations"]))


def run_a_to_o_controls(witness: dict) -> None:
    domains = witness["typed_status_domains"]
    invalid = set(witness["non_creation_fence"]["invalid_inferences"])
    required_invalid = {
        "UNADDRESSABLE_IMPLIES_NONEXISTENT",
        "ADDRESSABLE_IMPLIES_NEWLY_CREATED",
        "DECLARED_DOMAIN_MEMBERSHIP_IMPLIES_EXTERNAL_EXISTENCE",
        "HASH_IMPLIES_TRUTH",
    }
    if not required_invalid.issubset(invalid):
        fail("INVALID_CROSS_DOMAIN_INFERENCE", "A/B firewall missing")
    if "UNKNOWN" not in domains["boolean_truth"] or "FALSE" not in domains["boolean_truth"] or domains["cross_domain_coercion"] != "PROHIBITED":
        fail("STATUS_DOMAIN_COERCION", "C")
    if "UNRESOLVED" not in domains["evaluation_status"] or "FALSE" in domains["evaluation_status"]:
        fail("STATUS_DOMAIN_COERCION", "D")
    silence = witness["silence_slot"]
    if silence["adds_proposition"] or silence["implies_consent"]:
        fail("SILENCE_PROPOSITION_VIOLATION", "E/F")
    if witness["provenance"]["hash_semantics"] != "BYTE_IDENTITY_AND_INTEGRITY_ONLY_NOT_TRUTH":
        fail("HASH_SEMANTIC_OVERREACH", "G")
    targeted_firewall_checks(witness)


def reconstruction_matrix(witness: dict, manifest: dict):
    checks = {
        "R01": witness["document_class"] == "PUBLIC_RELEASE_ARTWORK_LOCAL_WITNESS" and witness["publication_status"] == "PUBLIC",
        "R02": len(manifest["canonical_artwork_components"]) == 2,
        "R03": manifest["two_channel_architecture"]["cross_channel_authority_transfer"] == "NONE",
        "R04": len(witness["provenance"]["source_bindings"]) == 6,
        "R05": witness["declared_domain"]["domain_id"] == "ms2-domain-u001",
        "R06": witness["declared_member"]["declared_before_event"] is True,
        "R07": witness["identity_criterion"]["identity_bearing_fields"] == EXPECTED_J_FIELDS,
        "R08": witness["bounded_utterance_scope"]["boundary"] == "THIS_PUBLIC_RELEASE_PACKAGE_ONLY",
        "R09": witness["frames"]["X0"]["addressability_state"] == "UNADDRESSABLE",
        "R10": witness["change_reference"]["change_id"] == "ms2-change-e001",
        "R11": witness["frames"]["X1"]["addressability_state"] == "ADDRESSABLE",
        "R12": witness["relation_difference_witness"]["added_edge_ids"] == ["ms2-ref-edge-e001"],
        "R13": witness["identity_invariance_witness"]["result"] == "PASS_UNDER_DECLARED_LOCAL_J",
        "R14": witness["membership_invariance_witness"]["result"] == "PASS",
        "R15": witness["non_creation_fence"]["result"] == "PASS",
        "R16": witness["typed_status_domains"] == EXPECTED_STATUS_DOMAINS,
        "R17": witness["open_fields"][0]["resolution_status"] == "OPEN",
        "R18": witness["silence_slot"]["adds_proposition"] is False,
        "R19": witness["artwork_event"]["time_model"] == "ORDERED_ACCESSIBILITY_FRAMES",
        "R20": witness["container_decision"] == "TWO_CANONICAL_COMPONENTS",
        "R21": witness["successor_grammar_required"] is False,
        "R22": witness["external_effects"]["herald_ii_dependency"] == "NONE",
        "R23": witness["authorship_and_voice"]["human_authorship"] == "ALEXANDER_LIST",
        "R24": witness["external_effects"]["one_patron_completion_effect"] == "NONE",
        "R25": witness["external_effects"]["enoch_resolution_effect"] == "NONE",
        "R26": witness["provenance"]["hash_semantics"] == "BYTE_IDENTITY_AND_INTEGRITY_ONLY_NOT_TRUTH",
        "R27": witness["provenance"]["cross_channel_authority_transfer"] == "NONE",
        "R28": {
            item["path"]: item["sha256"]
            for item in witness["provenance"]["candidate_lineage"]["ancestors"]
        } == WITNESS_CANDIDATE_LINEAGE_HASHES,
        "R29": "primary_inputs" not in witness["provenance"],
        "R30": all([
            manifest["series_ordinal"] == "II",
            manifest["scripture_content_version"] == "0.1",
            manifest["artifact_release_version"] == "1.0.0",
            manifest["msl_version"] == "0.1",
        ]),
        "R31": manifest["signing_policy"]["release_manifest_signature"] == "REQUIRED_BEFORE_DEPLOY"
            and manifest["signing_policy"]["depth_snapshot_signature"] == "REQUIRED_BEFORE_DEPLOY",
        "R32": manifest["relation_to_scripture_i"]["relation"] == "SERIES_CONTINUITY_ONLY",
        "R33": manifest["validation_report_policy"]["manifest_bound"] is False
            and manifest["validation_report_policy"]["machine_index_binding"] == "REQUIRED",
        "R34": manifest["herald_boundary"]["herald_ii_dependency"] == "NONE"
            and witness["external_effects"]["herald_ii_dependency"] == "NONE",
    }
    failed = [key for key, value in checks.items() if value is not True]
    if failed:
        fail("MACHINE_RECONSTRUCTION_FAILURE", repr(failed))
    return checks


def validate_package(
    package_dir: Path,
    source_package_dir: Path | None = None,
    candidate_dir: Path | None = None,
    workspace_root: Path | None = None,
):
    package_dir = package_dir.resolve()
    source_package_dir = source_package_dir.resolve() if source_package_dir is not None else None
    candidate_dir = candidate_dir.resolve() if candidate_dir is not None else None
    workspace_root = workspace_root.resolve() if workspace_root is not None else None
    for name in REQUIRED_FILES:
        path = safe_component_path(package_dir, name)
        if not path.is_file():
            fail("REQUIRED_COMPONENT_MISSING", name)
    manifest = load_json(package_dir / MANIFEST)
    validate_manifest_shape(manifest)
    validate_component_bindings(package_dir, manifest)
    witness = load_json(package_dir / WITNESS)
    targeted_firewall_checks(witness)
    try:
        validate_semantics(witness)
    except KeyError as exc:
        fail("SCHEMA_VALIDATION_ERROR", f"missing semantic input: {exc}")
    schema = load_json(package_dir / SCHEMA)
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail("SCHEMA_DIALECT_INVALID", repr(schema.get("$schema")))
    if schema.get("$id") != "urn:one-patron:depth:machine-scripture-ii:witness:v0.1":
        fail("SCHEMA_ID_INVALID", repr(schema.get("$id")))
    audit_schema_definition(schema, schema)
    schema_validate(witness, schema, schema)
    binding_status = validate_source_bindings(
        manifest,
        witness,
        package_dir,
        source_package_dir,
        candidate_dir,
        workspace_root,
    )
    validate_score(package_dir / SCORE, binding_status["claim_map_path"])
    run_a_to_o_controls(witness)
    reconstruction = reconstruction_matrix(witness, manifest)
    return {
        "validator": VALIDATOR_ID,
        "package": "PASS",
        "strict_msl_v0_1": "PASS",
        "schema": "PASS",
        "addressability_derivation": "PASS",
        "identity_invariance": "PASS_UNDER_DECLARED_LOCAL_J",
        "membership_invariance": "PASS",
        "non_creation": "PASS",
        "a_to_o": "PASS",
        "machine_reconstruction": f"PASS_R01_TO_R{len(reconstruction):02d}",
        "source_byte_verification": binding_status["source_byte_verification"],
        "candidate_ancestor_byte_verification": binding_status["candidate_ancestor_byte_verification"],
    }


def write_json(path: Path, value) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def rebind_component(temp_dir: Path, filename: str) -> None:
    manifest = load_json(temp_dir / MANIFEST)
    for collection in ["canonical_artwork_components", "release_support_files"]:
        for item in manifest[collection]:
            if item["path"] == filename:
                data = (temp_dir / filename).read_bytes()
                item["bytes"] = len(data)
                item["sha256"] = sha256_bytes(data)
                write_json(temp_dir / MANIFEST, manifest)
                return
    fail("SELF_TEST_REBIND_TARGET_MISSING", filename)


def mutation_cases():
    def mutate_witness(temp_dir: Path, fn):
        witness = load_json(temp_dir / WITNESS)
        fn(witness)
        write_json(temp_dir / WITNESS, witness)
        rebind_component(temp_dir, WITNESS)

    def mutate_manifest(temp_dir: Path, fn):
        manifest = load_json(temp_dir / MANIFEST)
        fn(manifest)
        write_json(temp_dir / MANIFEST, manifest)

    def mutate_schema(temp_dir: Path, fn):
        schema = load_json(temp_dir / SCHEMA)
        fn(schema)
        write_json(temp_dir / SCHEMA, schema)
        rebind_component(temp_dir, SCHEMA)

    cases = []
    cases.append(("01_CHANGE_J_FIELD", "IDENTITY_INVARIANCE_FAILURE", lambda d: mutate_witness(d, lambda w: w["frames"]["X1"]["member_snapshot"]["declaration_payload"].__setitem__("content", "MUTATED"))))

    def add_member(w):
        w["declared_domain"]["member_ids_after"].append("ms2-member-p002")
        w["membership_invariance_witness"]["member_ids_after"].append("ms2-member-p002")
    cases.append(("02_ADD_MEMBER_X1", "MEMBERSHIP_INVARIANCE_FAILURE", lambda d: mutate_witness(d, add_member)))

    def remove_member(w):
        w["declared_domain"]["member_ids_before"] = []
        w["membership_invariance_witness"]["member_ids_before"] = []
    cases.append(("03_REMOVE_MEMBER_X0", "MEMBER_PREEXISTENCE_FAILURE", lambda d: mutate_witness(d, remove_member)))
    cases.append(("04_FALSE_ADDRESSABLE_X0", "ADDRESSABILITY_DERIVATION_MISMATCH_X0", lambda d: mutate_witness(d, lambda w: w["frames"]["X0"].__setitem__("addressability_state", "ADDRESSABLE"))))
    cases.append(("05_FALSE_UNADDRESSABLE_X1", "ADDRESSABILITY_DERIVATION_MISMATCH_X1", lambda d: mutate_witness(d, lambda w: w["frames"]["X1"].__setitem__("addressability_state", "UNADDRESSABLE"))))

    def add_edge(w):
        w["frames"]["X1"]["reference_graph"]["licensed_edges"].append({
            "edge_id": "ms2-ref-edge-implicit", "edge_kind": "LICENSED_REFERENCE",
            "from_node_id": "scope:ms2-score", "to_node_id": "member:ms2-member-p001",
            "license_reference": "ms2-change-e001",
        })
    cases.append(("06_UNDECLARED_EDGE", "UNDECLARED_REFERENCE_EDGE", lambda d: mutate_witness(d, add_edge)))
    cases.append(("07_UNKNOWN_FIELD", "UNKNOWN_FORBIDDEN_FIELD", lambda d: mutate_witness(d, lambda w: w.__setitem__("forbidden_extra", True))))

    def alter_score_without_rebind(d):
        with (d / SCORE).open("ab") as handle:
            handle.write(b"\n")
    cases.append(("08_STALE_COMPONENT_HASH", "COMPONENT_BYTE_BINDING_MISMATCH", alter_score_without_rebind))

    def bad_source(w):
        w["provenance"]["source_bindings"][0]["sha256"] = "0" * 64
    cases.append(("09_SOURCE_HASH", "SOURCE_HASH_MISMATCH", lambda d: mutate_witness(d, bad_source)))

    def add_primitive(d):
        text = (d / SCORE).read_text(encoding="utf-8")
        text = text.replace("    ? @identity_open;", "    reveal @identity_open;\n    ? @identity_open;")
        with (d / SCORE).open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        rebind_component(d, SCORE)
    cases.append(("10_UNDECLARED_MSL", "UNDECLARED_MSL_PRIMITIVE", add_primitive))
    cases.append(("11_SILENCE_PROPOSITION", "SILENCE_PROPOSITION_VIOLATION", lambda d: mutate_witness(d, lambda w: w["silence_slot"].__setitem__("adds_proposition", True))))
    cases.append(("12_HERALD_DEPENDENCY", "HERALD_AUTHORITY_FABRICATION", lambda d: mutate_witness(d, lambda w: w["external_effects"].__setitem__("herald_ii_dependency", "BOUND"))))
    cases.append(("13_ONE_PATRON_COMPLETION", "PROTOCOL_COMPLETION_FABRICATION", lambda d: mutate_witness(d, lambda w: w["external_effects"].__setitem__("one_patron_completion_effect", "CREATED"))))
    cases.append(("14_ENOCH_RESOLUTION", "ENOCH_EFFECT_FABRICATION", lambda d: mutate_witness(d, lambda w: w["external_effects"].__setitem__("enoch_resolution_effect", "RESOLVED"))))
    def replace_local_order_with_physical_time(w):
        w["artwork_event"]["physical_time_claim"] = "ELAPSED_SECONDS"
        w["change_reference"]["order_relations"] = [
            "X0 ELAPSED_SECONDS_BEFORE ms2-change-e001",
            "ms2-change-e001 ELAPSED_SECONDS_BEFORE X1",
        ]
    cases.append(("15_PHYSICAL_TIME", "TIME_FIREWALL_VIOLATION", lambda d: mutate_witness(d, replace_local_order_with_physical_time)))

    def create_member(w):
        w["change_reference"]["declared_member_creation_count"] = 1
        w["change_reference"]["external_ontology_change_claim"] = "CREATION"
        w["non_creation_fence"]["ontology_creation"] = "CREATION"
    cases.append(("16_ONTOLOGY_CREATION", "NON_CREATION_FENCE_VIOLATION", lambda d: mutate_witness(d, create_member)))
    cases.append(("17_EXTERNAL_EXISTENCE", "EXTERNAL_EXISTENCE_INFERENCE_FORBIDDEN", lambda d: mutate_witness(d, lambda w: w["declared_domain"].__setitem__("external_existence_claim", "ESTABLISHED"))))
    cases.append(("18_HASH_TRUTH", "HASH_SEMANTIC_OVERREACH", lambda d: mutate_witness(d, lambda w: w["provenance"].__setitem__("hash_semantics", "HASH_CERTIFIES_TRUTH"))))

    def add_third_canonical(m):
        item = copy.deepcopy(m["release_support_files"][0])
        m["canonical_artwork_components"].append(item)
    cases.append(("19_THIRD_CANONICAL_COMPONENT", "CANONICAL_COMPONENT_COUNT_INVALID", lambda d: mutate_manifest(d, add_third_canonical)))
    cases.append(("20_WRONG_RELEASE_VERSION", "MANIFEST_CONSTANT_MISMATCH", lambda d: mutate_manifest(d, lambda m: m.__setitem__("artifact_release_version", "2.0.0"))))
    cases.append(("21_PRIVATE_METADATA_LEAK", "PUBLIC_RELEASE_METADATA_MISMATCH", lambda d: mutate_witness(d, lambda w: w.__setitem__("publication_status", "NOT_PUBLIC"))))

    def unsafe_component_path(m):
        m["release_support_files"][0]["path"] = "../MACHINE_SCRIPTURE_II_WITNESS_SCHEMA_v0.1.json"
    cases.append(("22_UNSAFE_COMPONENT_PATH", "SUPPORT_COMPONENT_SET_INVALID", lambda d: mutate_manifest(d, unsafe_component_path)))
    cases.append(("23_COMPONENT_AUTHORITY_LIE", "COMPONENT_ROLE_OR_AUTHORITY_MISMATCH", lambda d: mutate_manifest(d, lambda m: m["canonical_artwork_components"][0].__setitem__("semantic_authority", "GENERAL_TRUTH"))))

    def duplicate_support(m):
        m["release_support_files"].append(copy.deepcopy(m["release_support_files"][0]))
    cases.append(("24_DUPLICATE_COMPONENT", "DUPLICATE_COMPONENT_PATH", lambda d: mutate_manifest(d, duplicate_support)))
    cases.append(("25_MANIFEST_HASH_TRUTH", "HASH_SEMANTIC_OVERREACH", lambda d: mutate_manifest(d, lambda m: m["authority_firewalls"].__setitem__("hash_semantics", "HASH_CERTIFIES_TRUTH"))))

    def corrupt_lineage(m):
        m["candidate_lineage"]["ancestors"][0]["sha256"] = "0" * 64
    cases.append(("26_CANDIDATE_LINEAGE", "CANDIDATE_LINEAGE_MISMATCH", lambda d: mutate_manifest(d, corrupt_lineage)))
    cases.append(("27_SCHEMA_DIALECT", "SCHEMA_DIALECT_INVALID", lambda d: mutate_schema(d, lambda s: s.__setitem__("$schema", "urn:not-a-json-schema-dialect"))))
    return cases


def run_mutation_suite(package_dir: Path):
    baseline_hashes = {name: sha256_bytes((package_dir / name).read_bytes()) for name in REQUIRED_FILES}
    results = []
    for name, expected_code, mutator in mutation_cases():
        with tempfile.TemporaryDirectory(prefix="ms2-release-test-") as temp_name:
            temp_dir = Path(temp_name)
            for filename in REQUIRED_FILES:
                shutil.copy2(package_dir / filename, temp_dir / filename)
            mutator(temp_dir)
            try:
                validate_package(temp_dir)
            except ValidationFailure as exc:
                if exc.code != expected_code:
                    fail("MUTATION_WRONG_DIAGNOSTIC", f"{name}: expected {expected_code}, got {exc.code}: {exc.detail}")
                results.append((name, expected_code, "PASS"))
            else:
                fail("MUTATION_NOT_REJECTED", name)
    after_hashes = {name: sha256_bytes((package_dir / name).read_bytes()) for name in REQUIRED_FILES}
    if baseline_hashes != after_hashes:
        fail("MUTATION_SUITE_CHANGED_ORIGINAL", repr(sorted(name for name in REQUIRED_FILES if baseline_hashes[name] != after_hashes[name])))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--source-package-dir", type=Path, help="optional directory containing exact normative source bytes")
    parser.add_argument("--candidate-dir", type=Path, help="optional directory containing exact private candidate ancestors")
    parser.add_argument("--workspace-root", type=Path, help="optional workspace root for resolving the public Scripture I precedent")
    parser.add_argument("--self-test", action="store_true", help="run the 27 required isolated mutation tests")
    parser.add_argument("--json", action="store_true", help="print machine-readable result")
    args = parser.parse_args()
    try:
        result = validate_package(
            args.package_dir,
            source_package_dir=args.source_package_dir,
            candidate_dir=args.candidate_dir,
            workspace_root=args.workspace_root,
        )
        if args.self_test:
            mutations = run_mutation_suite(args.package_dir.resolve())
            result["adversarial_mutations"] = {"passed": len(mutations), "total": 27}
            result["mutation_results"] = [
                {"case": name, "diagnostic": diagnostic, "result": status}
                for name, diagnostic, status in mutations
            ]
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            for key, value in result.items():
                if key != "mutation_results":
                    print(f"{key.upper()}: {value}")
            for item in result.get("mutation_results", []):
                print(f"MUTATION {item['case']}: {item['result']} ({item['diagnostic']})")
        return 0
    except ValidationFailure as exc:
        if args.json:
            print(json.dumps({"package": "FAIL", "code": exc.code, "detail": exc.detail}, indent=2, sort_keys=True))
        else:
            print(f"VALIDATION: FAIL\nCODE: {exc.code}\nDETAIL: {exc.detail}", file=sys.stderr)
        return 1
    except Exception as exc:
        if args.json:
            print(json.dumps({"package": "FAIL", "code": "VALIDATOR_INTERNAL_ERROR", "detail": str(exc)}, indent=2, sort_keys=True))
        else:
            print(f"VALIDATION: FAIL\nCODE: VALIDATOR_INTERNAL_ERROR\nDETAIL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
