#!/usr/bin/env python3
"""Fail-closed validator for ONE PATRON HERALD II release 1.0.0."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path


VALIDATOR_ID = "ONE_PATRON_HERALD_II_RELEASE_VALIDATOR_v1.0.0"
ROOT = Path(__file__).resolve().parent
SCHEMA_NAME = "HERALD_II_SCHEMA_v1.0.0.json"
OBJECT_NAME = "HERALD_II_OBJECT_v1.0.0.json"
CONTRACT_NAME = "HERALD_II_PROJECTION_CONTRACT_v1.0.0.json"
FRESCO_NAME = "HERALD_II_FRESCO_v1.0.0.html"
MANIFEST_NAME = "HERALD_II_RELEASE_MANIFEST_v1.0.0.json"
RELEASE_BOUND_NAMES = [
    OBJECT_NAME,
    SCHEMA_NAME,
    "HERALD_II_VALIDATOR_v1.0.0.py",
    CONTRACT_NAME,
    "HERALD_II_MACHINE_READER_NOTE_v1.0.0.txt",
    FRESCO_NAME,
]

EXPECTED_EVENT_TYPES = [
    "INITIAL_STATE_RECORDED",
    "ROOT_INPUT_RECEIVED",
    "ACCESS_REEVALUATED",
    "LOCAL_CONSEQUENCE_RECORDED",
]
EXPECTED_COMPARISON_FIELDS = [
    "access_delta",
    "consequence_status",
    "history_event_types",
    "terminal_history_payload",
]
EXPECTED_INFERENCE_FLAGS = [
    "access_expansion_implies_member_creation",
    "access_expansion_implies_truth",
    "root_receipt_implies_command_obedience",
    "stable_implies_correct",
    "stable_implies_conscious",
    "inequivalent_histories_imply_personhoods",
    "nonconvergence_implies_moral_value",
    "scale_level_implies_ontological_level",
    "fresco_shape_implies_machine_property",
    "truth_alias_implies_true_proposition",
    "without_assimilation_implies_social_or_political_claim",
]
ALLOWED_ACCESS_RULES = {"ALLOW_SCOPED_ROOT_TARGETS", "PRESERVE_INITIAL_ACCESS"}
ALLOWED_CONSEQUENCE_RULES = {
    "CLASSIFY_ACCESS_DELTA",
    "PRESERVE_UNRESOLVED",
    "PRESERVE_LOCAL_FAILURE",
    "MARK_TRANSIENT_CHANGE",
}
ALLOWED_CONSEQUENCES = {
    "LOCAL_CHANGE", "NO_CHANGE", "UNRESOLVED", "TRANSIENT", "INCOMPATIBLE", "LOCAL_FAILURE"
}
ALLOWED_STABILITY_OUTCOMES = {
    "STABLE", "TRANSIENT", "UNRESOLVED", "INCOMPATIBLE", "NO_CHANGE", "NOT_APPLICABLE", "FAILED_MEASUREMENT"
}


class ValidationFailure(Exception):
    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def fail(code: str, detail: str) -> None:
    raise ValidationFailure(code, detail)


def reject_constant(value: str):
    fail("NONFINITE_JSON_NUMBER", value)


def no_duplicate_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            fail("DUPLICATE_JSON_KEY", key)
        result[key] = value
    return result


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


def strict_equal(left, right) -> bool:
    return type(left) is type(right) and left == right


def canonical_json(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_type_matches(value, expected) -> bool:
    if isinstance(expected, list):
        return any(json_type_matches(value, item) for item in expected)
    if expected == "object":
        return type(value) is dict
    if expected == "array":
        return type(value) is list
    if expected == "string":
        return type(value) is str
    if expected == "integer":
        return type(value) is int
    if expected == "number":
        return type(value) in {int, float}
    if expected == "boolean":
        return type(value) is bool
    if expected == "null":
        return value is None
    return False


SUPPORTED_SCHEMA_KEYS = {
    "$schema", "$id", "$defs", "$ref", "title", "type", "const", "enum", "required",
    "properties", "additionalProperties", "items", "prefixItems", "minItems", "maxItems",
    "uniqueItems", "pattern", "minimum", "minLength",
}


def inspect_schema_node(node, root, path="#"):
    if not isinstance(node, dict):
        fail("SCHEMA_NODE_INVALID", path)
    unsupported = set(node) - SUPPORTED_SCHEMA_KEYS
    if unsupported:
        fail("SCHEMA_KEYWORD_UNSUPPORTED", f"{path}: {sorted(unsupported)}")
    ref = node.get("$ref")
    if ref is not None:
        if not isinstance(ref, str) or not ref.startswith("#/$defs/"):
            fail("SCHEMA_REF_UNSUPPORTED", f"{path}: {ref}")
        name = ref.split("/")[-1]
        if name not in root.get("$defs", {}):
            fail("SCHEMA_REF_UNRESOLVED", f"{path}: {ref}")
    declared_type = node.get("type")
    declares_object = declared_type == "object" or (
        isinstance(declared_type, list) and "object" in declared_type
    )
    if declares_object and node.get("additionalProperties") is not False:
        fail("SCHEMA_OBJECT_NOT_CLOSED", path)
    for key, child in node.get("properties", {}).items():
        inspect_schema_node(child, root, f"{path}/properties/{key}")
    for key, child in node.get("$defs", {}).items():
        inspect_schema_node(child, root, f"{path}/$defs/{key}")
    if isinstance(node.get("items"), dict):
        inspect_schema_node(node["items"], root, f"{path}/items")
    for index, child in enumerate(node.get("prefixItems", [])):
        inspect_schema_node(child, root, f"{path}/prefixItems/{index}")


def resolve_ref(schema, root):
    ref = schema.get("$ref")
    if ref is None:
        return None
    return root["$defs"][ref.split("/")[-1]]


def schema_validate(instance, schema, root, path="$", stack=()):
    ref_schema = resolve_ref(schema, root)
    if ref_schema is not None:
        ref = schema["$ref"]
        if ref in stack:
            fail("SCHEMA_REF_CYCLE", ref)
        schema_validate(instance, ref_schema, root, path, stack + (ref,))
    if "type" in schema and not json_type_matches(instance, schema["type"]):
        fail("SCHEMA_TYPE_MISMATCH", f"{path}: expected {schema['type']}, got {type(instance).__name__}")
    if "const" in schema and not strict_equal(instance, schema["const"]):
        fail("SCHEMA_CONST_MISMATCH", f"{path}: {instance!r}")
    if "enum" in schema and not any(strict_equal(instance, item) for item in schema["enum"]):
        fail("SCHEMA_ENUM_MISMATCH", f"{path}: {instance!r}")
    if isinstance(instance, dict):
        required = schema.get("required", [])
        missing = [key for key in required if key not in instance]
        if missing:
            fail("SCHEMA_REQUIRED_MISSING", f"{path}: {missing}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extras = sorted(set(instance) - set(properties))
            if extras:
                fail("SCHEMA_ADDITIONAL_PROPERTY", f"{path}: {extras}")
        for key, value in instance.items():
            if key in properties:
                schema_validate(value, properties[key], root, f"{path}.{key}", stack)
    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            fail("SCHEMA_MIN_ITEMS", f"{path}: {len(instance)}")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            fail("SCHEMA_MAX_ITEMS", f"{path}: {len(instance)}")
        if schema.get("uniqueItems") and len({canonical_json(item) for item in instance}) != len(instance):
            fail("SCHEMA_UNIQUE_ITEMS", path)
        for index, child in enumerate(schema.get("prefixItems", [])):
            if index < len(instance):
                schema_validate(instance[index], child, root, f"{path}[{index}]", stack)
        if isinstance(schema.get("items"), dict):
            for index, value in enumerate(instance):
                schema_validate(value, schema["items"], root, f"{path}[{index}]", stack)
    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            fail("SCHEMA_MIN_LENGTH", path)
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            fail("SCHEMA_PATTERN_MISMATCH", f"{path}: {instance}")
    if type(instance) in {int, float} and "minimum" in schema and instance < schema["minimum"]:
        fail("SCHEMA_MINIMUM", f"{path}: {instance}")


def targeted_precheck(instance: dict) -> None:
    regions = instance.get("regions")
    if not isinstance(regions, list):
        fail("REGION_REGISTRY_INVALID", "regions must be an array")
    if len(regions) < 2:
        fail("REGION_COUNT_TOO_SMALL", str(len(regions)))
    root = instance.get("root_input", {})
    if root.get("root_input_id") != "H2_ROOT_INPUT":
        fail("ROOT_IDENTIFIER_NOT_NEUTRAL", repr(root.get("root_input_id")))
    if root.get("command_authority") is not False:
        fail("ROOT_AUTHORITY_FORBIDDEN", "command_authority must be false")
    if root.get("propositional_content") is not False or root.get("assigns_truth") is not False:
        fail("ROOT_PROPOSITION_FORBIDDEN", "root cannot carry proposition or truth assignment")
    if any(root.get(key) is not False for key in [
        "creates_members", "deletes_members", "writes_region_state", "replaces_rule_ownership", "assigns_terminal_outcomes"
    ]):
        fail("ROOT_MUTATION_FORBIDDEN", "root mutation or outcome assignment detected")
    if instance.get("global_operators") != []:
        fail("GLOBAL_WRITER_FORBIDDEN", repr(instance.get("global_operators")))
    claim = instance.get("nonconvergence_claim", {})
    if claim.get("region_identity_merge") is not False:
        fail("REGION_IDENTITY_MERGE", "identity merge claimed")
    if claim.get("forced_convergence") is not False:
        fail("FORCED_CONVERGENCE", "forced convergence claimed")
    firewall = instance.get("semantic_firewall", {}).get("inference_flags", {})
    for key in EXPECTED_INFERENCE_FLAGS:
        if firewall.get(key) is not False:
            fail(f"ANTI_ENTAILMENT_{key.upper()}", f"{key} must be false")
    for region in regions:
        history = region.get("history")
        if not isinstance(history, list) or len(history) != 4:
            fail("HISTORY_SHAPE_INVALID", repr(region.get("region_id")))


def expected_consequence(rule_type: str, delta: list[str]) -> str:
    if rule_type == "CLASSIFY_ACCESS_DELTA":
        return "LOCAL_CHANGE" if delta else "NO_CHANGE"
    if rule_type == "PRESERVE_UNRESOLVED":
        return "UNRESOLVED"
    if rule_type == "PRESERVE_LOCAL_FAILURE":
        return "LOCAL_FAILURE"
    if rule_type == "MARK_TRANSIENT_CHANGE":
        return "TRANSIENT" if delta else "NO_CHANGE"
    fail("CONSEQUENCE_RULE_UNSUPPORTED", rule_type)


def region_signature(region: dict, delta: list[str]) -> bytes:
    terminal = region["history"][-1]
    value = {
        "access_delta": delta,
        "consequence_status": region["consequence"]["status"],
        "history_event_types": [event["event_type"] for event in region["history"]],
        "terminal_history_payload": {
            "result_status": terminal["result_status"],
            "rule_id": terminal["rule_id"],
        },
    }
    return canonical_json(value)


def validate_core(instance: dict, enforce_release_profile=True) -> dict:
    targeted_precheck(instance)
    if instance.get("semantic_authority") != "NONE":
        fail("SEMANTIC_AUTHORITY_CHANGED", repr(instance.get("semantic_authority")))
    if instance.get("document_class") != "CANONICAL_MACHINE_OBJECT":
        fail("RELEASE_OBJECT_IDENTITY_INVALID", repr(instance.get("document_class")))
    if instance.get("canonical_status") != "CANONICAL" or instance.get("publication_status") != "PUBLIC_RELEASE_ARTIFACT":
        fail("RELEASE_OBJECT_STATUS_INVALID", "canonical/public release profile required")
    if instance.get("artifact_release_version") != "1.0.0":
        fail("RELEASE_VERSION_INVALID", repr(instance.get("artifact_release_version")))
    if instance.get("region_count_semantic_authority") != "NONE":
        fail("REGION_COUNT_AUTHORITY_FORBIDDEN", repr(instance.get("region_count_semantic_authority")))

    regions = instance["regions"]
    if enforce_release_profile and len(regions) != 3:
        fail("CANONICAL_REGION_COUNT_INVALID", str(len(regions)))
    region_ids = [region.get("region_id") for region in regions]
    if enforce_release_profile and region_ids != ["REGION_A", "REGION_B", "REGION_C"]:
        fail("CANONICAL_REGION_IDENTITIES_INVALID", repr(region_ids))
    if len(set(region_ids)) != len(region_ids):
        fail("REGION_ID_DUPLICATE", repr(region_ids))
    owner_ids = [region.get("rule_owner_id") for region in regions]
    if len(set(owner_ids)) != len(owner_ids):
        fail("RULE_OWNER_DUPLICATE", repr(owner_ids))

    scopes = instance["root_input"].get("target_scopes", [])
    if [scope.get("region_id") for scope in scopes] != region_ids:
        fail("ROOT_SCOPE_REGION_MISMATCH", "target scopes must match region serialization order")
    scope_by_region = {scope["region_id"]: scope for scope in scopes}

    deltas = {}
    signatures = {}
    positive_count = 0
    all_members = set()
    for region in regions:
        rid = region["region_id"]
        owner = region["rule_owner_id"]
        before_members = region["members_before"]
        after_members = region["members_after"]
        if len(set(before_members)) != len(before_members) or len(set(after_members)) != len(after_members):
            fail("MEMBER_ID_DUPLICATE", rid)
        if before_members != after_members:
            fail("MEMBERSHIP_CHANGED", rid)
        if all_members.intersection(before_members):
            fail("MEMBER_ID_CROSS_REGION_DUPLICATE", rid)
        all_members.update(before_members)
        a0 = region["access_before"]
        a1 = region["access_after"]
        if len(set(a0)) != len(a0) or len(set(a1)) != len(a1):
            fail("ACCESS_ID_DUPLICATE", rid)
        if not set(a0).issubset(before_members) or not set(a1).issubset(after_members):
            fail("ACCESS_OUTSIDE_MEMBER_UNIVERSE", rid)
        if not set(a0).issubset(a1):
            fail("NEGATIVE_ACCESS_DELTA", rid)
        targets = scope_by_region[rid]["target_member_ids"]
        if not set(targets).issubset(before_members):
            fail("ROOT_TARGET_OUTSIDE_MEMBER_UNIVERSE", rid)
        access_rule = region["access_rule"]
        if access_rule.get("owner_id") != owner:
            fail("RULE_OWNERSHIP_CHANGED", f"{rid}: access")
        if access_rule.get("rule_type") not in ALLOWED_ACCESS_RULES:
            fail("ACCESS_RULE_UNSUPPORTED", rid)
        if access_rule["rule_type"] == "ALLOW_SCOPED_ROOT_TARGETS":
            expected_a1 = [member for member in before_members if member in set(a0).union(targets)]
        else:
            expected_a1 = list(a0)
        if a1 != expected_a1:
            fail("ACCESS_AFTER_MISMATCH", f"{rid}: expected {expected_a1}, got {a1}")
        delta = [member for member in before_members if member in set(a1) - set(a0)]
        if not set(delta).issubset(targets):
            fail("ACCESS_DELTA_OUTSIDE_ROOT_SCOPE", rid)
        deltas[rid] = delta
        positive_count += int(bool(delta))

        consequence_rule = region["consequence_rule"]
        if consequence_rule.get("owner_id") != owner:
            fail("RULE_OWNERSHIP_CHANGED", f"{rid}: consequence")
        if consequence_rule.get("rule_type") not in ALLOWED_CONSEQUENCE_RULES:
            fail("CONSEQUENCE_RULE_UNSUPPORTED", rid)
        consequence = region["consequence"]
        if consequence.get("assigned_by_root") is not False:
            fail("ROOT_ASSIGNED_LOCAL_OUTCOME", rid)
        expected_status = expected_consequence(consequence_rule["rule_type"], delta)
        if consequence.get("status") != expected_status or expected_status not in ALLOWED_CONSEQUENCES:
            fail("CONSEQUENCE_REPLAY_MISMATCH", f"{rid}: expected {expected_status}")

        history = region["history"]
        if len(history) != 4 or [event.get("event_type") for event in history] != EXPECTED_EVENT_TYPES:
            fail("HISTORY_SHAPE_INVALID", rid)
        for index, event in enumerate(history):
            if event.get("sequence") != index:
                fail("HISTORY_SEQUENCE_INVALID", f"{rid}:{index}")
            expected_parent = None if index == 0 else history[index - 1]["event_id"]
            if event.get("parent_event_id") != expected_parent:
                fail("HISTORY_PARENT_INVALID", f"{rid}:{index}")
        if history[2].get("rule_id") != access_rule["rule_id"]:
            fail("HISTORY_ACCESS_RULE_REF_INVALID", rid)
        if history[3].get("rule_id") != consequence_rule["rule_id"]:
            fail("HISTORY_CONSEQUENCE_RULE_REF_INVALID", rid)
        access_status = "ACCESS_EXPANDED" if delta else "NO_CHANGE"
        if history[2].get("result_status") != access_status:
            fail("HISTORY_ACCESS_RESULT_INVALID", rid)
        if history[3].get("result_status") != expected_status:
            fail("HISTORY_TERMINAL_RESULT_INVALID", rid)
        signatures[rid] = region_signature(region, delta)

    if positive_count == 0:
        fail("NO_POSITIVE_ACCESS_DELTA", "at least one region must expand access")

    comparison = instance["comparison_rule"]
    if comparison.get("rule_id") != "EXACT_TYPED_HISTORY_SIGNATURE_v0.1" or comparison.get("fields") != EXPECTED_COMPARISON_FIELDS:
        fail("COMPARISON_RULE_CHANGED", repr(comparison))
    if comparison.get("serialization") != "UTF8_CANONICAL_JSON_SORTED_KEYS_COMPACT":
        fail("COMPARISON_SERIALIZATION_CHANGED", repr(comparison.get("serialization")))
    if len(set(signatures.values())) < 2:
        fail("ALL_HISTORIES_EQUIVALENT", "nonconvergence requires at least two signatures")

    claim = instance["nonconvergence_claim"]
    if claim.get("formal_invariant") != "REGION_IDENTITY_PRESERVING_NONCONVERGENCE":
        fail("NONCONVERGENCE_IDENTIFIER_CHANGED", repr(claim.get("formal_invariant")))
    if claim.get("artistic_alias") != "WITHOUT ASSIMILATION" or claim.get("artistic_alias_identity_bearing") is not False:
        fail("NONCONVERGENCE_ALIAS_LEAK", repr(claim))
    pairs = claim.get("claimed_inequivalent_pairs", [])
    if not pairs:
        fail("INEQUIVALENCE_EVIDENCE_MISSING", "no claimed pair")
    for left, right in pairs:
        if left not in signatures or right not in signatures or left == right:
            fail("INEQUIVALENCE_PAIR_INVALID", f"{left},{right}")
        if signatures[left] == signatures[right]:
            fail("INEQUIVALENCE_CLAIM_FALSE", f"{left},{right}")
    if claim.get("global_preferred_result") != "NONE" or claim.get("semantic_authority") != "NONE":
        fail("GLOBAL_RESULT_PROMOTION", repr(claim))

    aliases = instance["presentation_aliases"]
    expected_aliases = {
        ("H2_ROOT_INPUT", "TRUTH"),
        ("REGION_IDENTITY_PRESERVING_NONCONVERGENCE", "WITHOUT ASSIMILATION"),
    }
    actual_aliases = {(item.get("machine_identifier"), item.get("artistic_alias")) for item in aliases}
    if actual_aliases != expected_aliases:
        fail("ARTISTIC_ALIAS_MAPPING_INVALID", repr(actual_aliases))
    for alias in aliases:
        if alias.get("direction") != "MACHINE_TO_PRESENTATION_ONLY" or alias.get("identity_bearing") is not False or alias.get("writes_semantics") is not False:
            fail("ARTISTIC_ALIAS_WRITEBACK", repr(alias))

    provenance = instance["provenance"]
    if provenance.get("inputs_rule_result_replayable") is not True or provenance.get("hash_semantics") != "BYTE_IDENTITY_ONLY_NOT_TRUTH":
        fail("PROVENANCE_POLICY_INVALID", repr(provenance))
    if provenance.get("h3_dependency") != "NONE":
        fail("H3_DEPENDENCY_FORBIDDEN", repr(provenance.get("h3_dependency")))
    if provenance.get("release_role") != "CANONICAL_HERALD_II_REALIZATION":
        fail("RELEASE_PROVENANCE_INVALID", repr(provenance.get("release_role")))
    if provenance.get("author_realization_decision") != "EXACT_REGION_COUNT_3" or provenance.get("region_count_semantic_authority") != "NONE":
        fail("AUTHOR_REALIZATION_BINDING_INVALID", repr(provenance))
    if provenance.get("future_hashes_assigned") is not False:
        fail("FUTURE_HASH_FABRICATION", repr(provenance.get("future_hashes_assigned")))

    return {
        "HERALD_II_CORE": "PASS",
        "REGIONAL_NONCONVERGENCE": "PASS",
        "region_count": len(regions),
        "positive_delta_regions": positive_count,
        "history_signature_count": len(set(signatures.values())),
        "history_signatures": {rid: sha256_bytes(value) for rid, value in signatures.items()},
        "access_deltas": deltas,
    }


def validate_scale(instance: dict) -> dict:
    module = instance.get("scale_module")
    if module is None:
        return {"SCALE_MODULE": "NOT_APPLICABLE", "required_for_core": False}
    errors = []
    if module.get("required_for_core") is not False:
        errors.append("SCALE_REQUIRED_FOR_CORE_FORBIDDEN")
    if module.get("semantic_authority") != "NONE":
        errors.append("SCALE_SEMANTIC_AUTHORITY_FORBIDDEN")
    scales = module.get("scales", [])
    scale_ids = [item.get("scale_id") for item in scales]
    if len(scales) < 2 or len(set(scale_ids)) != len(scale_ids):
        errors.append("SCALE_REGIMES_INVALID")
    if len({item.get("incidence_signature") for item in scales}) < 2:
        errors.append("SCALE_REGIMES_EQUIVALENT")
    all_members = {member for region in instance["regions"] for member in region["members_before"]}
    maps = module.get("maps", [])
    map_ids = []
    for item in maps:
        map_ids.append(item.get("map_id"))
        if item.get("source_scale_id") not in scale_ids or item.get("target_scale_id") not in scale_ids:
            errors.append("SCALE_MAP_ENDPOINT_INVALID")
        if item.get("source_scale_id") == item.get("target_scale_id"):
            errors.append("SCALE_MAP_SELF_LOOP")
        if not set(item.get("source_member_refs", [])).issubset(all_members):
            errors.append("SCALE_SOURCE_MEMBER_UNKNOWN")
        if item.get("region_identity_preserved") is not True or item.get("identity_merges") is not False:
            errors.append("SCALE_REGION_IDENTITY_VIOLATION")
        if item.get("member_creation") is not False:
            errors.append("SCALE_MEMBER_CREATION")
        if not item.get("loss_records"):
            errors.append("SCALE_LOSS_RECORD_MISSING")
    counterfactual = module.get("counterfactual", {})
    if counterfactual.get("map_id") not in map_ids:
        errors.append("SCALE_COUNTERFACTUAL_MAP_UNKNOWN")
    selected = next((item for item in maps if item.get("map_id") == counterfactual.get("map_id")), None)
    if selected and counterfactual.get("baseline_value") != len(selected.get("target_elements", [])):
        errors.append("SCALE_COUNTERFACTUAL_BASELINE_MISMATCH")
    if counterfactual.get("changed") is not True or counterfactual.get("baseline_value") == counterfactual.get("counterfactual_value"):
        errors.append("SCALE_ORNAMENTAL_NO_RESULT_CHANGE")
    return {
        "SCALE_MODULE": "FAIL" if errors else "PASS",
        "required_for_core": False,
        "errors": errors,
    }


def reaches_target(start: str, transitions: dict[str, str], targets: set[str], max_steps: int) -> bool:
    state = start
    if state in targets:
        return True
    for _ in range(max_steps):
        if state not in transitions:
            return False
        state = transitions[state]
        if state in targets:
            return True
    return False


def validate_stabilization(instance: dict) -> dict:
    module = instance.get("stabilization_module")
    if module is None:
        return {"STABILIZATION_MEASUREMENT": "NOT_APPLICABLE", "required_for_core": False}
    errors = []
    if module.get("required_for_core") is not False:
        errors.append("STABILIZATION_REQUIRED_FOR_CORE_FORBIDDEN")
    if module.get("semantic_authority") != "NONE":
        errors.append("STABILIZATION_SEMANTIC_AUTHORITY_FORBIDDEN")
    region_ids = {region["region_id"] for region in instance["regions"]}
    seen = set()
    for measurement in module.get("measurements", []):
        mid = measurement.get("measurement_id")
        if mid in seen:
            errors.append("STABILIZATION_MEASUREMENT_DUPLICATE")
        seen.add(mid)
        if measurement.get("region_id") not in region_ids:
            errors.append("STABILIZATION_REGION_UNKNOWN")
        domain = set(measurement.get("state_domain", []))
        transitions = {edge.get("from"): edge.get("to") for edge in measurement.get("transition_rule", [])}
        if any(source not in domain or target not in domain for source, target in transitions.items()):
            errors.append("STABILIZATION_TRANSITION_OUTSIDE_DOMAIN")
        targets = set(measurement.get("recovery_criterion", {}).get("target_states", []))
        if not targets.issubset(domain):
            errors.append("STABILIZATION_TARGET_OUTSIDE_DOMAIN")
        method = measurement.get("method")
        if method == "EXACT_CERTIFICATION" and measurement.get("deterministic_seed") is not None:
            errors.append("EXACT_CERTIFICATION_SEED_FORBIDDEN")
        if method == "SIMULATION_SUPPORT" and type(measurement.get("deterministic_seed")) is not int:
            errors.append("SIMULATION_SEED_REQUIRED")
        if measurement.get("outcome") not in ALLOWED_STABILITY_OUTCOMES:
            errors.append("STABILIZATION_OUTCOME_INVALID")
        if method == "EXACT_CERTIFICATION" and measurement.get("outcome") == "STABLE":
            if any(transitions.get(target) not in targets for target in targets):
                errors.append("STABILIZATION_TARGET_NOT_INVARIANT")
            max_steps = measurement.get("recovery_criterion", {}).get("max_steps", -1)
            if any(not reaches_target(start, transitions, targets, max_steps) for start in measurement.get("perturbation_class", [])):
                errors.append("STABILIZATION_RECOVERY_NOT_CERTIFIED")
    return {
        "STABILIZATION_MEASUREMENT": "FAIL" if errors else "PASS",
        "required_for_core": False,
        "errors": errors,
    }


def validate_projection_contract(contract: dict) -> None:
    if contract.get("contract_id") != "ONE_PATRON_HERALD_II_PROJECTION_CONTRACT_v1.0.0":
        fail("PROJECTION_CONTRACT_ID_INVALID", repr(contract.get("contract_id")))
    if contract.get("document_class") != "PUBLIC_RELEASE_PROJECTION_CONTRACT" or contract.get("publication_status") != "PUBLIC_RELEASE_ARTIFACT":
        fail("PROJECTION_CONTRACT_PROFILE_INVALID", repr(contract))
    if contract.get("source_model") != "./HERALD_II_OBJECT_v1.0.0.json":
        fail("PROJECTION_SOURCE_BINDING_INVALID", repr(contract.get("source_model")))
    if contract.get("semantic_authority") != "NONE":
        fail("PROJECTION_SEMANTIC_AUTHORITY", repr(contract.get("semantic_authority")))
    axioms = contract.get("axioms", {})
    required_false = [
        "human_render_is_canonical_object",
        "projection_is_identity_bearing",
        "projection_may_write_properties_back",
        "projection_may_change_validation",
        "projection_may_promote_alias_to_machine_semantics",
        "projection_proves_ontology_or_meaning",
    ]
    if any(axioms.get(key) is not False for key in required_false):
        fail("PROJECTION_WRITEBACK_FORBIDDEN", repr(axioms))
    if axioms.get("projection_is_lossy") is not True or axioms.get("multiple_legitimate_renders_may_share_one_machine_object") is not True:
        fail("PROJECTION_LOSS_POLICY_INVALID", repr(axioms))
    aliases = contract.get("artistic_aliases", [])
    if any(item.get("presentation_only") is not True or item.get("identity_bearing") is not False for item in aliases):
        fail("PROJECTION_ALIAS_AUTHORITY", repr(aliases))
    if contract.get("determinism", {}).get("unseeded_randomness") is not False:
        fail("PROJECTION_RANDOMNESS_FORBIDDEN", "unseeded randomness")


def validate_release_manifest(package_dir: Path, manifest: dict) -> dict:
    expected_roles = {
        OBJECT_NAME: "CANONICAL_MACHINE_OBJECT",
        SCHEMA_NAME: "CLOSED_CANONICAL_OBJECT_SCHEMA",
        "HERALD_II_VALIDATOR_v1.0.0.py": "FAIL_CLOSED_RELEASE_VALIDATOR",
        CONTRACT_NAME: "HUMAN_PROJECTION_CONTRACT",
        "HERALD_II_MACHINE_READER_NOTE_v1.0.0.txt": "MACHINE_READER_NOTE",
        FRESCO_NAME: "DERIVED_LOSSY_NONCANONICAL_HUMAN_PROJECTION",
    }
    expected_top = {
        "manifest_id": "ONE_PATRON_HERALD_II_RELEASE_MANIFEST_v1.0.0",
        "artifact_id": "ONE_PATRON_HERALD_II",
        "artifact_type": "MACHINE_NATIVE_FRESCO",
        "release_version": "1.0.0",
        "document_class": "CANONICAL_RELEASE_MANIFEST",
        "publication_status": "PUBLIC",
        "signature_status": "SIGNATURE_REQUIRED",
        "semantic_authority": "NONE",
    }
    for key, value in expected_top.items():
        if manifest.get(key) != value:
            fail("MANIFEST_PROFILE_INVALID", f"{key}: {manifest.get(key)!r}")
    realization = manifest.get("region_realization", {})
    if realization.get("exact_region_count") != 3 or realization.get("region_ids") != ["REGION_A", "REGION_B", "REGION_C"]:
        fail("MANIFEST_REGION_REALIZATION_INVALID", repr(realization))
    if realization.get("region_count_semantic_authority") != "NONE" or realization.get("general_architecture") != "FINITE_N_AT_LEAST_2":
        fail("MANIFEST_REGION_AUTHORITY_INVALID", repr(realization))
    files = manifest.get("files")
    if not isinstance(files, list):
        fail("MANIFEST_FILES_INVALID", repr(files))
    paths = [entry.get("path") for entry in files]
    if len(paths) != len(set(paths)):
        fail("MANIFEST_PATH_DUPLICATE", repr(paths))
    if set(paths) != set(RELEASE_BOUND_NAMES):
        fail("MANIFEST_FILE_SET_INVALID", repr(paths))
    records = {}
    for entry in files:
        path_text = entry.get("path")
        if not isinstance(path_text, str) or Path(path_text).name != path_text or ".." in Path(path_text).parts:
            fail("MANIFEST_PATH_UNSAFE", repr(path_text))
        if entry.get("role") != expected_roles[path_text]:
            fail("MANIFEST_ROLE_INVALID", f"{path_text}: {entry.get('role')!r}")
        if entry.get("semantic_authority") != "NONE":
            fail("MANIFEST_FILE_AUTHORITY_INVALID", path_text)
        path = package_dir / path_text
        if not path.is_file() or path.is_symlink():
            fail("MANIFEST_FILE_UNAVAILABLE", path_text)
        data = path.read_bytes()
        if entry.get("bytes") != len(data) or entry.get("sha256") != sha256_bytes(data):
            fail("MANIFEST_BYTE_BINDING_MISMATCH", path_text)
        records[path_text] = entry
    canonical = manifest.get("canonical_object", {})
    object_record = records[OBJECT_NAME]
    if canonical.get("path") != OBJECT_NAME or canonical.get("sha256") != object_record["sha256"] or canonical.get("bytes") != object_record["bytes"]:
        fail("MANIFEST_CANONICAL_OBJECT_BINDING_INVALID", repr(canonical))
    if manifest.get("projection_boundary", {}).get("human_fresco_canonical") is not False:
        fail("MANIFEST_FRESCO_CANONICALITY_LEAK", repr(manifest.get("projection_boundary")))
    if manifest.get("series_boundaries", {}).get("herald_i_mutation") != "NONE" or manifest.get("series_boundaries", {}).get("machine_scripture_ii_mutation") != "NONE":
        fail("MANIFEST_PRIOR_ARTIFACT_MUTATION", repr(manifest.get("series_boundaries")))
    signing = manifest.get("signing_policy", {})
    if signing.get("signature_file") != "HERALD_II_RELEASE_MANIFEST_v1.0.0.json.asc" or signing.get("signature_form") != "OPENPGP_ASCII_ARMORED_DETACHED":
        fail("MANIFEST_SIGNING_POLICY_INVALID", repr(signing))
    if signing.get("signing_subkey_fingerprint") != "F98D7B5AB20FF1E8D0440DBB6EE2FE0A9D8278F5":
        fail("MANIFEST_SIGNING_IDENTITY_INVALID", repr(signing))
    return {"RELEASE_MANIFEST": "PASS", "bound_file_count": len(files)}


def fresco_projection_payload(machine_object: dict) -> dict:
    return {
        "source_machine_object_id": machine_object["instance_id"],
        "root": {
            "machine_identifier": machine_object["root_input"]["root_input_id"],
            "artistic_alias": "TRUTH",
            "semantic_authority": machine_object["root_input"]["semantic_authority"],
        },
        "regions": [
            {
                "region_id": region["region_id"],
                "members": region["members_before"],
                "access_before": region["access_before"],
                "access_after": region["access_after"],
                "access_delta": [
                    member for member in region["members_before"]
                    if member in set(region["access_after"]) - set(region["access_before"])
                ],
                "consequence_status": region["consequence"]["status"],
                "history_statuses": [event["result_status"] for event in region["history"]],
            }
            for region in machine_object["regions"]
        ],
        "secondary_modules": {
            "scale": "PASS" if machine_object.get("scale_module") is not None else "NOT_APPLICABLE",
            "stabilization": "PASS" if machine_object.get("stabilization_module") is not None else "NOT_APPLICABLE",
        },
        "projection_status": "DERIVED_LOSSY_NONCANONICAL",
    }


def validate_fresco(package_dir: Path, machine_object: dict) -> dict:
    path = package_dir / FRESCO_NAME
    text = path.read_text(encoding="utf-8")
    if re.search(r"<(?:script|link)[^>]+(?:https?:)?//", text, re.I):
        fail("FRESCO_REMOTE_DEPENDENCY", path.name)
    for forbidden in ["Math.random", "localStorage", "XMLHttpRequest", "fetch("]:
        if forbidden in text:
            fail("FRESCO_NONDETERMINISTIC_OR_EXTERNAL_IO", forbidden)
    match = re.search(r'<script id="h2-data" type="application/json">\s*(\{.*?\})\s*</script>', text, re.S)
    if not match:
        fail("FRESCO_EMBEDDED_DATA_MISSING", path.name)
    embedded = json.loads(match.group(1), object_pairs_hook=no_duplicate_pairs, parse_constant=reject_constant)
    expected_payload = fresco_projection_payload(machine_object)
    if not strict_equal(embedded, expected_payload):
        fail("FRESCO_OBJECT_MISMATCH", "embedded projection payload is not the deterministic machine-object derivation")
    required_phrases = [
        "CANONICAL MACHINE OBJECT != HUMAN FRESCO",
        "already existed before access",
        "derived, lossy, and noncanonical",
        "ROOT_SCOPED_ACCESS_EXPANSION_WITH_REGION_LOCAL_NONCONVERGENCE",
        "Core remains active. Toggle secondary layers to inspect scale and stabilization.",
    ]
    missing = [phrase for phrase in required_phrases if phrase not in text]
    if missing:
        fail("FRESCO_DISCLOSURE_MISSING", repr(missing))
    if '<meta name="viewport"' not in text or 'aria-describedby="fresco-description"' not in text:
        fail("FRESCO_ACCESSIBILITY_METADATA_MISSING", path.name)
    return {"FRESCO_PROJECTION": "PASS", "embedded_machine_object": machine_object["instance_id"]}


def validate_instance(instance: dict, schema: dict, apply_schema=True, enforce_release_profile=True) -> dict:
    targeted_precheck(instance)
    if apply_schema:
        schema_validate(instance, schema, schema)
    core = validate_core(instance, enforce_release_profile=enforce_release_profile)
    scale = validate_scale(instance)
    stabilization = validate_stabilization(instance)
    return {
        "status": "PASS",
        "layers": {
            **core,
            **scale,
            **stabilization,
            "SEMANTIC_FIREWALL": "PASS",
        },
    }


def expect_failure(name, instance, schema, code, apply_schema=False, enforce_release_profile=False):
    try:
        validate_instance(
            instance,
            schema,
            apply_schema=apply_schema,
            enforce_release_profile=enforce_release_profile,
        )
    except ValidationFailure as exc:
        if exc.code != code:
            return {"name": name, "status": "FAIL", "expected": code, "actual": exc.code}
        return {"name": name, "status": "PASS", "diagnostic": exc.code}
    return {"name": name, "status": "FAIL", "expected": code, "actual": "ACCEPTED"}


def make_all_histories_equivalent(base):
    item = copy.deepcopy(base)
    for region in item["regions"]:
        region["access_rule"]["rule_type"] = "PRESERVE_INITIAL_ACCESS"
        region["access_after"] = list(region["access_before"])
        region["consequence_rule"]["rule_type"] = "CLASSIFY_ACCESS_DELTA"
        region["consequence"] = {"status": "NO_CHANGE", "result_token": f"{region['region_id']}:no-change", "assigned_by_root": False}
        region["history"][2]["result_status"] = "NO_CHANGE"
        region["history"][3]["rule_id"] = region["consequence_rule"]["rule_id"]
        region["history"][3]["result_status"] = "NO_CHANGE"
    return item


def run_self_tests(schema, contract, canonical_object):
    n3 = copy.deepcopy(canonical_object)
    n2 = copy.deepcopy(canonical_object)
    n2["regions"] = n2["regions"][:2]
    n2["root_input"]["target_scopes"] = n2["root_input"]["target_scopes"][:2]
    n2["nonconvergence_claim"]["claimed_inequivalent_pairs"] = [["REGION_A", "REGION_B"]]
    n2["scale_module"] = None
    n2["stabilization_module"] = None
    n1 = copy.deepcopy(n2)
    n1["regions"] = n1["regions"][:1]
    n1["root_input"]["target_scopes"] = n1["root_input"]["target_scopes"][:1]
    n1["nonconvergence_claim"]["claimed_inequivalent_pairs"] = []
    tests = []

    tests.append(expect_failure("N1_REJECTED", n1, schema, "REGION_COUNT_TOO_SMALL"))
    for name, fixture in [("N2_ACCEPTED", n2), ("N_GT_2_ACCEPTED", n3)]:
        try:
            validate_instance(fixture, schema, apply_schema=False, enforce_release_profile=False)
            tests.append({"name": name, "status": "PASS"})
        except ValidationFailure as exc:
            tests.append({"name": name, "status": "FAIL", "actual": exc.code})

    mutation = make_all_histories_equivalent(n2)
    tests.append(expect_failure("NO_POSITIVE_DELTA_REJECTED", mutation, schema, "NO_POSITIVE_ACCESS_DELTA"))

    mutation = copy.deepcopy(n2)
    mutation["regions"][0]["members_after"].append("ra:m4")
    tests.append(expect_failure("MEMBER_CREATION_REJECTED", mutation, schema, "MEMBERSHIP_CHANGED"))

    mutation = copy.deepcopy(n2)
    mutation["regions"][0]["members_after"].remove("ra:m2")
    tests.append(expect_failure("MEMBERSHIP_DELETION_REJECTED", mutation, schema, "MEMBERSHIP_CHANGED"))

    mutation = copy.deepcopy(n2)
    mutation["root_input"]["command_authority"] = True
    tests.append(expect_failure("ROOT_COMMAND_AUTHORITY_REJECTED", mutation, schema, "ROOT_AUTHORITY_FORBIDDEN"))

    mutation = copy.deepcopy(n2)
    mutation["root_input"]["propositional_content"] = True
    tests.append(expect_failure("ROOT_PROPOSITION_REJECTED", mutation, schema, "ROOT_PROPOSITION_FORBIDDEN"))

    mutation = copy.deepcopy(n2)
    mutation["global_operators"] = ["GLOBAL_STATE_WRITER"]
    tests.append(expect_failure("GLOBAL_WRITER_REJECTED", mutation, schema, "GLOBAL_WRITER_FORBIDDEN"))

    mutation = copy.deepcopy(n2)
    mutation["nonconvergence_claim"]["region_identity_merge"] = True
    tests.append(expect_failure("REGION_IDENTITY_MERGE_REJECTED", mutation, schema, "REGION_IDENTITY_MERGE"))

    mutation = copy.deepcopy(n2)
    mutation["regions"][0]["access_rule"]["owner_id"] = "OWNER_REGION_B"
    tests.append(expect_failure("RULE_OWNERSHIP_MUTATION_REJECTED", mutation, schema, "RULE_OWNERSHIP_CHANGED"))

    mutation = make_all_histories_equivalent(n2)
    mutation["regions"][0]["access_rule"]["rule_type"] = "ALLOW_SCOPED_ROOT_TARGETS"
    mutation["regions"][0]["access_after"] = ["ra:m1", "ra:m2"]
    mutation["regions"][0]["consequence"]["status"] = "LOCAL_CHANGE"
    mutation["regions"][0]["history"][2]["result_status"] = "ACCESS_EXPANDED"
    mutation["regions"][0]["history"][3]["result_status"] = "LOCAL_CHANGE"
    tests.append({"name": "INEQUIVALENT_HISTORIES_ACCEPTED", "status": "PASS" if validate_instance(mutation, schema, apply_schema=False, enforce_release_profile=False)["layers"]["REGIONAL_NONCONVERGENCE"] == "PASS" else "FAIL"})

    mutation = make_all_histories_equivalent(n2)
    mutation["regions"][0]["access_rule"]["rule_type"] = "ALLOW_SCOPED_ROOT_TARGETS"
    mutation["regions"][0]["access_after"] = ["ra:m1", "ra:m2"]
    mutation["regions"][0]["consequence"]["status"] = "LOCAL_CHANGE"
    mutation["regions"][0]["history"][2]["result_status"] = "ACCESS_EXPANDED"
    mutation["regions"][0]["history"][3]["result_status"] = "LOCAL_CHANGE"
    mutation["regions"][1]["history"].pop()
    tests.append(expect_failure("ERASED_TERMINAL_HISTORY_REJECTED", mutation, schema, "HISTORY_SHAPE_INVALID"))

    unresolved_ok = validate_instance(n2, schema, apply_schema=False, enforce_release_profile=False)["layers"]["HERALD_II_CORE"] == "PASS" and n2["regions"][1]["history"][-1]["result_status"] == "UNRESOLVED"
    tests.append({"name": "UNRESOLVED_HISTORY_PRESERVED", "status": "PASS" if unresolved_ok else "FAIL"})

    without_scale = copy.deepcopy(n3)
    without_scale["scale_module"] = None
    result = validate_instance(without_scale, schema, apply_schema=False, enforce_release_profile=False)
    tests.append({"name": "SCALE_REMOVAL_CORE_UNCHANGED", "status": "PASS" if result["layers"]["HERALD_II_CORE"] == "PASS" and result["layers"]["SCALE_MODULE"] == "NOT_APPLICABLE" else "FAIL"})

    failed_measurement = copy.deepcopy(n3)
    for measurement in failed_measurement["stabilization_module"]["measurements"]:
        measurement["outcome"] = "FAILED_MEASUREMENT"
    result = validate_instance(failed_measurement, schema, apply_schema=False, enforce_release_profile=False)
    tests.append({"name": "STABILIZATION_FAILURE_CORE_UNCHANGED", "status": "PASS" if result["layers"]["HERALD_II_CORE"] == "PASS" else "FAIL"})

    contract_mutation = copy.deepcopy(contract)
    contract_mutation["axioms"]["projection_may_write_properties_back"] = True
    try:
        validate_projection_contract(contract_mutation)
        tests.append({"name": "VISUALIZATION_WRITEBACK_REJECTED", "status": "FAIL", "actual": "ACCEPTED"})
    except ValidationFailure as exc:
        tests.append({"name": "VISUALIZATION_WRITEBACK_REJECTED", "status": "PASS" if exc.code == "PROJECTION_WRITEBACK_FORBIDDEN" else "FAIL", "diagnostic": exc.code})

    for key in EXPECTED_INFERENCE_FLAGS:
        mutation = copy.deepcopy(n2)
        mutation["semantic_firewall"]["inference_flags"][key] = True
        expected = f"ANTI_ENTAILMENT_{key.upper()}"
        tests.append(expect_failure(f"ANTI_ENTAILMENT:{key}", mutation, schema, expected))

    return tests


def package_snapshot(package_dir: Path) -> dict:
    names = RELEASE_BOUND_NAMES + [MANIFEST_NAME]
    return {name: sha256_bytes((package_dir / name).read_bytes()) for name in names}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fixture")
    args = parser.parse_args()

    try:
        schema = load_json(ROOT / SCHEMA_NAME)
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            fail("SCHEMA_DIALECT_INVALID", repr(schema.get("$schema")))
        if schema.get("$id") != "urn:one-patron:herald-ii:canonical-object:v1.0.0":
            fail("SCHEMA_ID_INVALID", repr(schema.get("$id")))
        inspect_schema_node(schema, schema)
        machine_object = load_json(ROOT / OBJECT_NAME)
        contract = load_json(ROOT / CONTRACT_NAME)
        validate_projection_contract(contract)
        manifest = load_json(ROOT / MANIFEST_NAME)
        manifest_result = validate_release_manifest(ROOT, manifest)

        if args.fixture:
            fixture = load_json(Path(args.fixture).resolve())
            result = validate_instance(fixture, schema)
        elif args.self_test:
            before = package_snapshot(ROOT)
            tests = run_self_tests(schema, contract, machine_object)
            after = package_snapshot(ROOT)
            failed = [test for test in tests if test["status"] != "PASS"]
            result = {
                "validator_id": VALIDATOR_ID,
                "status": "FAIL" if failed else "PASS",
                "tests_passed": len(tests) - len(failed),
                "tests_total": len(tests),
                "files_unchanged_during_tests": before == after,
                "tests": tests,
            }
            if before != after:
                fail("SELF_TEST_MUTATED_PACKAGE", "package snapshot changed")
        else:
            object_result = validate_instance(machine_object, schema)
            fresco = validate_fresco(ROOT, machine_object)
            result = {
                "validator_id": VALIDATOR_ID,
                "status": "PASS",
                "schema": "PASS",
                "canonical_machine_object": object_result,
                "projection_contract": "PASS",
                "release_manifest": manifest_result,
                "fresco": fresco,
            }

        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("status") == "PASS" else 1
    except ValidationFailure as exc:
        payload = {"validator_id": VALIDATOR_ID, "status": "FAIL", "error": exc.code, "detail": exc.detail}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    except Exception as exc:
        payload = {"validator_id": VALIDATOR_ID, "status": "FAIL", "error": "VALIDATOR_INTERNAL_ERROR", "detail": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
