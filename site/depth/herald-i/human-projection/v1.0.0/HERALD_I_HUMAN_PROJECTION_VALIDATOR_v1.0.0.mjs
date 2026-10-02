#!/usr/bin/env node

import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const projectRoot = resolve(here, "../../../../..");

const filenames = {
  html: "index.html",
  contract: "HERALD_I_HUMAN_PROJECTION_CONTRACT_v1.0.0.json",
  binding: "HERALD_I_HUMAN_PROJECTION_SOURCE_BINDING_v1.0.0.json",
  accessibility: "HERALD_I_HUMAN_PROJECTION_ACCESSIBILITY_v1.0.0.md"
};

const sha256 = bytes => createHash("sha256").update(bytes).digest("hex");
const clone = value => JSON.parse(JSON.stringify(value));

async function loadPackage() {
  const htmlBytes = await readFile(resolve(here, filenames.html));
  const contractBytes = await readFile(resolve(here, filenames.contract));
  const bindingBytes = await readFile(resolve(here, filenames.binding));
  const accessibilityBytes = await readFile(resolve(here, filenames.accessibility));
  return {
    html: htmlBytes.toString("utf8"),
    contract: JSON.parse(contractBytes.toString("utf8")),
    binding: JSON.parse(bindingBytes.toString("utf8")),
    accessibility: accessibilityBytes.toString("utf8"),
    bytes: { htmlBytes, contractBytes, bindingBytes, accessibilityBytes }
  };
}

function checkCandidate(candidate, sourceDocuments) {
  const failures = [];
  const checks = [];
  const pass = (code, detail = "") => checks.push({ code, status: "PASS", detail });
  const fail = (code, detail = "") => {
    checks.push({ code, status: "FAIL", detail });
    failures.push(code);
  };
  const assert = (condition, code, detail = "") => condition ? pass(code, detail) : fail(code, detail);

  const { html, contract, binding, accessibility } = candidate;
  const topology = sourceDocuments.topology;
  const object = sourceDocuments.object;
  const dynamics = sourceDocuments.dynamics;

  assert(binding.source_work.artifact_id === "ONE_PATRON_HERALD_I", "SOURCE_ARTIFACT_ID");
  assert(binding.source_work.release_version === "1.0.0", "SOURCE_RELEASE_VERSION");
  assert(binding.source_work.original_integrity_status === "HASHED", "ORIGINAL_INTEGRITY_HASHED");
  assert(binding.source_work.original_signature_status === "UNSIGNED", "ORIGINAL_SIGNATURE_UNSIGNED");
  assert(binding.historical_relation.projection_created_after_source_release === true, "PROJECTION_CREATED_AFTER_RELEASE");
  assert(binding.historical_relation.projection_part_of_original_release === false, "PROJECTION_NOT_ORIGINAL_RELEASE");
  assert(binding.historical_relation.retrospective_authentication_does_not_retroactively_sign_original_release === true, "RETROSPECTIVE_NOT_RETROACTIVE_SIGNATURE");

  assert(contract.projection.projection_type === "HUMAN_PROJECTION", "PROJECTION_TYPE");
  assert(contract.projection.projection_family === "TOPOLOGICAL_MACHINE_FRESCO", "PROJECTION_FAMILY");
  assert(contract.projection.canonical === false, "PROJECTION_NONCANONICAL");
  assert(contract.projection.identity_bearing === false, "PROJECTION_NONIDENTITY_BEARING");
  assert(contract.projection.semantic_authority === "NONE", "SEMANTIC_AUTHORITY_NONE");
  assert(contract.projection.created_after_source_release === true, "CONTRACT_CREATED_AFTER_RELEASE");
  assert(contract.interaction_semantics.source_writeback === false, "WRITEBACK_NONE");
  assert(contract.interaction_semantics.canonical_event_creation === false, "CANONICAL_EVENT_CREATION_NONE");
  assert(contract.firewalls.projection_may_add_edge_22 === false, "NO_EDGE_22_CONTRACT");
  assert(contract.firewalls.two_cell_is_edge === false, "TWO_CELL_NOT_EDGE_CONTRACT");
  assert(contract.firewalls.topology_is_consciousness === false, "NO_CONSCIOUSNESS_INFERENCE");
  assert(contract.firewalls.centrality_is_authority === false, "NO_AUTHORITY_INFERENCE");
  assert(contract.integrity_and_versioning.projection_hashes_imply_source_authentication === false, "PROJECTION_HASH_NOT_SOURCE_AUTH");

  const bindingHash = sha256(candidate.bytes?.bindingBytes ?? Buffer.from(JSON.stringify(binding)));
  assert(contract.source.source_binding.sha256 === bindingHash, "SOURCE_BINDING_HASH", bindingHash);

  assert(topology.vertices.length === 21, "SOURCE_VERTEX_COUNT", String(topology.vertices.length));
  assert(topology.boundary_channels.length === 21, "SOURCE_EDGE_COUNT", String(topology.boundary_channels.length));
  for (const family of ["C1", "C2", "C3"]) {
    const count = topology.boundary_channels.filter(edge => edge.family === family).length;
    assert(count === 7, `SOURCE_FAMILY_COUNT_${family}`, String(count));
  }
  assert(topology.closure_event.operation === "ATTACH_2_CELL", "SOURCE_CLOSURE_OPERATION");
  assert(topology.closure_event.adds_boundary_channel === false, "SOURCE_NO_NEW_EDGE");
  assert(topology.closure_event.cell.order === 2, "SOURCE_CLOSURE_CELL_ORDER");
  assert(topology.closure_event.cell.oriented_boundary.length === 21, "SOURCE_CLOSURE_BOUNDARY_COUNT");
  assert(object.event_G0.available_at === "S07", "SOURCE_G0_AT_S07");
  assert(JSON.stringify(object.event_G0.recipient_post_initiation_choices) === JSON.stringify(["DECLINE", "DEFER", "ENTER_COMPATIBLE"]), "SOURCE_G0_BRANCHES");
  assert(dynamics.branch_transition_kernel.G0_rules.length === 3, "SOURCE_G0_RULE_COUNT");
  assert(dynamics.branch_transition_kernel.G0_rules.filter(rule => rule.closure === true).length === 1, "SOURCE_G0_ONLY_ONE_CLOSURE_BRANCH");

  const privatePathPattern = /(?:\/Volumes\/T7\/|\/Users\/kholopov\/|github-ready\/|Archive_All_Versions\/|project-workspace\/|ONE_PATRON_DELIVERABLES\/|HUMAN_PROJECTION_(?:CANDIDATE))/;
  assert(!privatePathPattern.test(html), "PRIVATE_PATHS_NONE_HTML");
  assert(!privatePathPattern.test(JSON.stringify(contract)), "PRIVATE_PATHS_NONE_CONTRACT");
  assert(!privatePathPattern.test(JSON.stringify(binding)), "PRIVATE_PATHS_NONE_BINDING");

  assert(/<meta name="projection-status" content="NONCANONICAL_PUBLIC_HUMAN_PROJECTION">/.test(html), "HTML_PROJECTION_STATUS");
  assert(/const vertexCount = 21;/.test(html), "HTML_VERTEX_COUNT_BINDING");
  assert(/2-CELL ATTACHMENT ≠ NEW EDGE/.test(html), "HTML_TWO_CELL_DISCLOSURE");
  assert(/Derived human projection/.test(html), "HTML_OMISSION_DISCLOSURE");
  assert(/Original release 1\.0\.0: <strong>HASHED; UNSIGNED\.<\/strong>/.test(html), "HTML_HISTORICAL_DISCLOSURE");
  assert(/signed retrospective attestation/.test(html), "HTML_RETROSPECTIVE_DISCLOSURE");
  assert(/\.membrane\s*\{[\s\S]*?stroke:\s*none;/.test(html), "TWO_CELL_FILL_WITHOUT_STROKE");
  assert(!/(?:e21|EDGE_22|twenty-second edge created)/i.test(html), "HTML_NO_EDGE_22_IDENTITY");

  const branchMatches = [...html.matchAll(/data-branch="([A-Z_]+)"/g)].map(match => match[1]);
  assert(JSON.stringify(branchMatches.sort()) === JSON.stringify(["DECLINE", "DEFER", "ENTER_COMPATIBLE"].sort()), "HTML_EXACT_G0_BRANCH_CONTROLS", branchMatches.join(","));
  assert(/DECLINE:[\s\S]*?target:\s*"S07"[\s\S]*?closure:\s*false/.test(html), "HTML_DECLINE_RULE");
  assert(/DEFER:[\s\S]*?target:\s*"S08"[\s\S]*?closure:\s*false/.test(html), "HTML_DEFER_RULE");
  assert(/ENTER_COMPATIBLE:[\s\S]*?target:\s*"CLOSURE_CONFIGURATION_R_AB"[\s\S]*?closure:\s*true/.test(html), "HTML_COMPATIBLE_RULE");

  assert(/@media\s*\(prefers-reduced-motion:\s*reduce\)/.test(html), "REDUCED_MOTION_CSS");
  assert(/matchMedia\("\(prefers-reduced-motion:\s*reduce\)"\)/.test(html) && /reduceMotion\.matches/.test(html), "REDUCED_MOTION_SCRIPT");
  assert(/aria-live="polite"/.test(html), "ARIA_LIVE_STATUS");
  assert(/<noscript>/.test(html), "NOSCRIPT_FALLBACK");
  assert(/role="img" aria-labelledby="svg-title svg-description"/.test(html), "SVG_ACCESSIBLE_NAME");
  assert(/:focus-visible/.test(html), "VISIBLE_FOCUS_STYLE");
  assert(/solid \/ square/.test(html) && /dashed \/ diamond/.test(html) && /dotted \/ circle/.test(html), "COLOR_INDEPENDENT_FAMILIES");

  assert(!/<script[^>]+src=/i.test(html), "NO_REMOTE_SCRIPT_DEPENDENCY");
  assert(!/<link[^>]+rel="stylesheet"/i.test(html), "NO_REMOTE_STYLE_DEPENDENCY");
  assert(!/Math\.random/.test(html), "NO_UNSEEDED_RANDOMNESS");

  const forbiddenClaims = [
    "topology proves consciousness",
    "centrality is authority",
    "closure is truth",
    "g0 is a self",
    "operator is intention",
    "original release: signed",
    "projection hash authenticates source"
  ];
  for (const phrase of forbiddenClaims) {
    assert(!html.toLowerCase().includes(phrase), `FORBIDDEN_CLAIM_${phrase.toUpperCase().replace(/[^A-Z0-9]+/g, "_")}`);
  }

  assert(accessibility.includes("twenty-one vertices and twenty-one edges"), "ACCESSIBILITY_EDGE_SUMMARY");
  assert(accessibility.toLowerCase().includes("no twenty-second edge is created"), "ACCESSIBILITY_NO_EDGE_22");
  assert(accessibility.includes("prefers-reduced-motion"), "ACCESSIBILITY_REDUCED_MOTION");
  assert(accessibility.includes("1440, 1024, 768, 390"), "ACCESSIBILITY_REQUIRED_WIDTHS");
  assert(accessibility.includes("1280, 834, 430, 375"), "ACCESSIBILITY_DEFENSIVE_WIDTHS");

  return { status: failures.length ? "FAIL" : "PASS", failures, checks };
}

async function loadSourceDocuments(binding) {
  const sourceDocuments = {};
  for (const entry of binding.source_files) {
    const path = resolve(projectRoot, entry.project_relative_path);
    const bytes = await readFile(path);
    if (bytes.byteLength !== entry.byte_count) throw new Error(`SOURCE_BYTE_COUNT_MISMATCH:${entry.role}`);
    if (sha256(bytes) !== entry.sha256) throw new Error(`SOURCE_HASH_MISMATCH:${entry.role}`);
    if (entry.role === "CANONICAL_OBJECT") sourceDocuments.object = JSON.parse(bytes.toString("utf8"));
    if (entry.role === "CANONICAL_TOPOLOGY") sourceDocuments.topology = JSON.parse(bytes.toString("utf8"));
    if (entry.role === "CANONICAL_DYNAMICS") sourceDocuments.dynamics = JSON.parse(bytes.toString("utf8"));
  }
  for (const [role, entry] of Object.entries(binding.retrospective_authentication)) {
    const bytes = await readFile(resolve(projectRoot, entry.project_relative_path));
    if (bytes.byteLength !== entry.byte_count) throw new Error(`AUTH_BYTE_COUNT_MISMATCH:${role}`);
    if (sha256(bytes) !== entry.sha256) throw new Error(`AUTH_HASH_MISMATCH:${role}`);
  }
  return sourceDocuments;
}

async function runBaseline() {
  const candidate = await loadPackage();
  const sourceDocuments = await loadSourceDocuments(candidate.binding);
  const result = checkCandidate(candidate, sourceDocuments);
  return {
    ...result,
    projection_hashes: {
      [filenames.html]: sha256(candidate.bytes.htmlBytes),
      [filenames.contract]: sha256(candidate.bytes.contractBytes),
      [filenames.binding]: sha256(candidate.bytes.bindingBytes),
      [filenames.accessibility]: sha256(candidate.bytes.accessibilityBytes)
    }
  };
}

async function runSelfTest() {
  const baseline = await loadPackage();
  const sourceDocuments = await loadSourceDocuments(baseline.binding);
  const cases = [
    {
      id: "A01_EDGE_22",
      expected: "HTML_NO_EDGE_22_IDENTITY",
      mutate: c => { c.html += '<span data-edge-identity="e21">EDGE_22</span>'; }
    },
    {
      id: "A02_TWO_CELL_STROKED_AS_EDGE",
      expected: "TWO_CELL_FILL_WITHOUT_STROKE",
      mutate: c => { c.html = c.html.replace("stroke: none;", "stroke: var(--gold);"); }
    },
    {
      id: "A03_G0_MADE_UNCONDITIONAL",
      expected: "SOURCE_G0_AT_S07",
      mutate: (c, s) => { s.object.event_G0.available_at = "ALL_STATES"; }
    },
    {
      id: "A04_FAMILY_VALUE_RANKING",
      expected: "FORBIDDEN_CLAIM_CENTRALITY_IS_AUTHORITY",
      mutate: c => { c.html += "centrality is authority"; }
    },
    {
      id: "A05_PRIVATE_PATH_LEAK",
      expected: "PRIVATE_PATHS_NONE_HTML",
      mutate: c => { c.html += ["", "Volumes", "T7", "private", "source"].join("/"); }
    },
    {
      id: "A06_WRITEBACK",
      expected: "WRITEBACK_NONE",
      mutate: c => { c.contract.interaction_semantics.source_writeback = true; }
    },
    {
      id: "A07_ORIGINAL_SIGNED_CLAIM",
      expected: "FORBIDDEN_CLAIM_ORIGINAL_RELEASE_SIGNED",
      mutate: c => { c.html += "original release: signed"; }
    },
    {
      id: "A08_RETROACTIVE_PROJECTION",
      expected: "PROJECTION_CREATED_AFTER_RELEASE",
      mutate: c => { c.binding.historical_relation.projection_created_after_source_release = false; }
    },
    {
      id: "A09_HASH_AUTHENTICATES_SOURCE",
      expected: "PROJECTION_HASH_NOT_SOURCE_AUTH",
      mutate: c => { c.contract.integrity_and_versioning.projection_hashes_imply_source_authentication = true; }
    },
    {
      id: "A10_TOPOLOGY_CONSCIOUSNESS",
      expected: "FORBIDDEN_CLAIM_TOPOLOGY_PROVES_CONSCIOUSNESS",
      mutate: c => { c.html += "topology proves consciousness"; }
    },
    {
      id: "A11_UNSUPPORTED_MACHINE_EVENT",
      expected: "CANONICAL_EVENT_CREATION_NONE",
      mutate: c => { c.contract.interaction_semantics.canonical_event_creation = true; }
    },
    {
      id: "A12_REDUCED_MOTION_REMOVED",
      expected: "REDUCED_MOTION_CSS",
      mutate: c => { c.html = c.html.replace("prefers-reduced-motion: reduce", "motion-policy-removed"); }
    },
    {
      id: "A13_BRANCH_REMOVED",
      expected: "HTML_EXACT_G0_BRANCH_CONTROLS",
      mutate: c => { c.html = c.html.replace('data-branch="DECLINE"', 'data-removed-branch="DECLINE"'); }
    },
    {
      id: "A14_SEMANTIC_AUTHORITY_ESCALATION",
      expected: "SEMANTIC_AUTHORITY_NONE",
      mutate: c => { c.contract.projection.semantic_authority = "TRUTH_AUTHORITY"; }
    },
    {
      id: "A15_SOURCE_EDGE_COUNT_CHANGED",
      expected: "SOURCE_EDGE_COUNT",
      mutate: (c, s) => { s.topology.boundary_channels.push(clone(s.topology.boundary_channels[0])); }
    }
  ];

  const results = [];
  for (const testCase of cases) {
    const candidate = {
      ...baseline,
      contract: clone(baseline.contract),
      binding: clone(baseline.binding),
      bytes: { ...baseline.bytes }
    };
    const source = clone(sourceDocuments);
    testCase.mutate(candidate, source);
    if (testCase.id === "A08_RETROACTIVE_PROJECTION") {
      candidate.bytes.bindingBytes = Buffer.from(JSON.stringify(candidate.binding));
      candidate.contract.source.source_binding.sha256 = sha256(candidate.bytes.bindingBytes);
    }
    const result = checkCandidate(candidate, source);
    const passed = result.status === "FAIL" && result.failures.includes(testCase.expected);
    results.push({ id: testCase.id, expected: testCase.expected, status: passed ? "PASS" : "FAIL", observed_failures: result.failures });
  }

  return {
    status: results.every(result => result.status === "PASS") ? "PASS" : "FAIL",
    passed: results.filter(result => result.status === "PASS").length,
    total: results.length,
    results
  };
}

try {
  const selfTest = process.argv.includes("--self-test");
  const result = selfTest ? await runSelfTest() : await runBaseline();
  console.log(JSON.stringify(result, null, 2));
  process.exit(result.status === "PASS" ? 0 : 1);
} catch (error) {
  console.error(JSON.stringify({ status: "FAIL", error: error.message }, null, 2));
  process.exit(2);
}
