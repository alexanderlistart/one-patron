"use strict";

const textEncoder = new TextEncoder();
const textDecoder = new TextDecoder();
const keyCommitmentDomain = textEncoder.encode(
  "one-patron/enoch/key-commitment/v1\0",
);
const objectUrls = new Set();

function formatTime(seconds) {
  if (!Number.isFinite(seconds) || seconds < 0) return "—:—";
  const minutes = Math.floor(seconds / 60);
  const remainder = Math.floor(seconds % 60).toString().padStart(2, "0");
  return minutes + ":" + remainder;
}

function bytesFromBase64(value) {
  const decoded = atob(value);
  const bytes = new Uint8Array(decoded.length);
  for (let index = 0; index < decoded.length; index += 1) {
    bytes[index] = decoded.charCodeAt(index);
  }
  return bytes;
}

function bytesToHex(bytes) {
  return Array.from(bytes, (value) => value.toString(16).padStart(2, "0")).join("");
}

async function sha256Hex(value) {
  const bytes = value instanceof Uint8Array ? value : new Uint8Array(value);
  return bytesToHex(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)));
}

async function fetchBytes(url) {
  const response = await fetch(url, { cache: "no-store", credentials: "same-origin" });
  if (!response.ok) {
    throw new Error("Record request failed: " + response.status);
  }
  return new Uint8Array(await response.arrayBuffer());
}

async function fetchJson(url) {
  const bytes = await fetchBytes(url);
  return {
    bytes,
    value: JSON.parse(textDecoder.decode(bytes)),
  };
}

async function verifyKeyCommitment(keyBytes, expected) {
  const combined = new Uint8Array(keyCommitmentDomain.length + keyBytes.length);
  combined.set(keyCommitmentDomain, 0);
  combined.set(keyBytes, keyCommitmentDomain.length);
  return (await sha256Hex(combined)) === expected;
}

async function deriveComponentKey(masterKey, salt, info) {
  const material = await crypto.subtle.importKey(
    "raw",
    masterKey,
    "HKDF",
    false,
    ["deriveKey"],
  );
  return crypto.subtle.deriveKey(
    {
      name: "HKDF",
      hash: "SHA-256",
      salt,
      info: textEncoder.encode(info),
    },
    material,
    { name: "AES-GCM", length: 256 },
    false,
    ["decrypt"],
  );
}

async function decryptComponent(packageManifestUrl, packageManifest, component, masterKey) {
  const ciphertextUrl = new URL(component.ciphertext_file, packageManifestUrl);
  const ciphertext = await fetchBytes(ciphertextUrl);
  if ((await sha256Hex(ciphertext)) !== component.ciphertext_sha256) {
    throw new Error("Ciphertext commitment mismatch");
  }
  const key = await deriveComponentKey(
    masterKey,
    bytesFromBase64(packageManifest.hkdf.salt_b64),
    component.hkdf_info,
  );
  const plaintext = await crypto.subtle.decrypt(
    {
      name: "AES-GCM",
      iv: bytesFromBase64(component.nonce_b64),
      additionalData: bytesFromBase64(component.aad_b64),
      tagLength: component.tag_bits,
    },
    key,
    ciphertext,
  );
  return new Uint8Array(plaintext);
}

async function openPackage(packageReference, release, publicManifestUrl) {
  const manifestUrl = new URL(packageReference.manifest_file, publicManifestUrl);
  const manifestResult = await fetchJson(manifestUrl);
  if ((await sha256Hex(manifestResult.bytes)) !== packageReference.manifest_sha256) {
    throw new Error("Package manifest commitment mismatch");
  }
  const manifest = manifestResult.value;
  if (
    manifest.package_id !== packageReference.id ||
    manifest.key_commitment_sha256 !== packageReference.key_commitment_sha256
  ) {
    throw new Error("Package identity mismatch");
  }
  const masterKey = bytesFromBase64(release.release_key_b64);
  if (!(await verifyKeyCommitment(masterKey, manifest.key_commitment_sha256))) {
    throw new Error("Release key commitment mismatch");
  }

  const components = new Map(manifest.components.map((item) => [item.id, item]));
  const opened = new Map();
  return {
    manifest,
    async open(componentId) {
      if (opened.has(componentId)) return opened.get(componentId);
      const component = components.get(componentId);
      if (!component) throw new Error("Missing encrypted component: " + componentId);
      const plaintext = await decryptComponent(
        manifestUrl,
        manifest,
        component,
        masterKey,
      );
      opened.set(componentId, plaintext);
      return plaintext;
    },
  };
}

function configurePlayer(player) {
  const row = player.closest(".audio-record");
  const audio = player.querySelector("audio");
  const button = player.querySelector("[data-play]");
  const seek = player.querySelector("[data-seek]");
  const current = player.querySelector("[data-current]");
  const duration = player.querySelector("[data-duration]");
  const playIcon = button.querySelector(".play-icon");
  const pauseIcon = button.querySelector(".pause-icon");
  const flac = document.querySelector("[data-download-flac]");
  const wav = document.querySelector("[data-download-wav]");
  let losslessLoader = null;
  let losslessFilename = "";
  let losslessUrl = "";
  let replayingLosslessClick = false;

  function renderPlayState(playing) {
    playIcon.hidden = playing;
    pauseIcon.hidden = !playing;
    button.setAttribute("aria-pressed", String(playing));
  }

  function updateTimeline() {
    const ratio = audio.duration ? (audio.currentTime / audio.duration) * 100 : 0;
    seek.value = String(ratio);
    seek.style.setProperty("--progress", ratio + "%");
    current.textContent = formatTime(audio.currentTime);
  }

  function initializeMetadata() {
    if (Number.isFinite(audio.duration)) {
      duration.textContent = formatTime(audio.duration);
    }
    row.classList.remove("is-unavailable");
    button.disabled = false;
    updateTimeline();
  }

  audio.addEventListener("loadedmetadata", initializeMetadata);
  audio.addEventListener("durationchange", initializeMetadata);
  audio.addEventListener("timeupdate", updateTimeline);
  audio.addEventListener("play", () => renderPlayState(true));
  audio.addEventListener("pause", () => renderPlayState(false));
  audio.addEventListener("ended", () => {
    audio.currentTime = 0;
    updateTimeline();
    renderPlayState(false);
  });
  audio.addEventListener("error", () => {
    row.classList.add("is-unavailable");
    button.disabled = true;
  });

  button.addEventListener("click", async () => {
    if (audio.paused) {
      try {
        await audio.play();
      } catch {
        row.classList.add("is-unavailable");
      }
    } else {
      audio.pause();
    }
  });

  seek.addEventListener("input", () => {
    if (!audio.duration) return;
    audio.currentTime = (Number(seek.value) / 100) * audio.duration;
    updateTimeline();
  });

  flac.addEventListener("click", async (event) => {
    if (replayingLosslessClick || !losslessLoader) return;
    event.preventDefault();
    flac.setAttribute("aria-busy", "true");
    const originalText = flac.textContent;
    flac.textContent = "Preparing FLAC…";
    try {
      const bytes = await losslessLoader();
      losslessUrl = URL.createObjectURL(new Blob([bytes], { type: "audio/flac" }));
      objectUrls.add(losslessUrl);
      flac.href = losslessUrl;
      flac.download = losslessFilename;
      losslessLoader = null;
      replayingLosslessClick = true;
      flac.click();
      replayingLosslessClick = false;
    } catch {
      flac.textContent = "FLAC unavailable";
    } finally {
      flac.removeAttribute("aria-busy");
      if (flac.textContent !== "FLAC unavailable") flac.textContent = originalText;
    }
  });

  if (audio.readyState >= 1) initializeMetadata();

  return {
    audio,
    setReleasedSource(options) {
      audio.pause();
      const url = URL.createObjectURL(
        new Blob([options.playbackBytes], { type: "audio/wav" }),
      );
      objectUrls.add(url);
      audio.src = url;
      audio.load();
      wav.href = url;
      wav.download = options.playbackFilename;
      wav.hidden = false;
      flac.href = "#record";
      flac.download = options.losslessFilename;
      flac.hidden = false;
      losslessLoader = options.losslessLoader;
      losslessFilename = options.losslessFilename;
      losslessUrl = "";
    },
  };
}

const player = configurePlayer(document.querySelector("[data-player]"));
const phraseElements = Array.from(document.querySelectorAll("[data-phrase]"));
const stateLabelText = document.querySelector("[data-state-label-text]");
const completionTitle = document.querySelector("[data-completion-title]");
const completionCopy = document.querySelector("[data-completion-copy]");
const completionRelease = document.querySelector("[data-completion-release]");
const unresolvedMark = document.querySelector(".mark-unresolved");
const resolvedMark = document.querySelector(".mark-resolved");
const markLabel = document.querySelector("[data-mark-label]");
const spectralClue = document.querySelector("[data-spectral-clue]");
const footerState = document.querySelector("[data-footer-state]");

async function revealAvailableSignatures() {
  const links = Array.from(document.querySelectorAll("[data-signature-link]"));
  await Promise.all(
    links.map(async (link) => {
      try {
        const response = await fetch(link.href, {
          cache: "no-store",
          credentials: "same-origin",
        });
        if (response.ok) link.hidden = false;
      } catch {
        link.hidden = true;
      }
    }),
  );
}

function releasePhrase(record) {
  const index = record.checkpoint === 7 ? 0 : record.checkpoint === 14 ? 1 : 2;
  const phrase = phraseElements[index];
  if (!phrase) return;
  phrase.classList.add("is-released");
  phrase.querySelector("[data-phrase-state]").textContent = "RELEASED";
  const release = phrase.querySelector("[data-phrase-release]");
  release.textContent = record.stanza;
  release.hidden = false;
  if (record.clue) {
    spectralClue.textContent = record.clue;
    spectralClue.hidden = false;
  }
}

function releaseCompletion(record, responseText) {
  document.body.dataset.completion = "resolved";
  stateLabelText.textContent = record.state;
  completionTitle.textContent = record.title;
  completionCopy.textContent = record.lead;
  completionRelease.replaceChildren();

  const stanza = document.createElement("p");
  stanza.className = "completion-stanza";
  stanza.textContent = record.stanza;
  const finalText = document.createElement("div");
  finalText.className = "final-text";
  finalText.textContent = responseText;
  completionRelease.append(stanza, finalText);
  completionRelease.hidden = false;

  unresolvedMark.hidden = true;
  resolvedMark.hidden = false;
  markLabel.textContent = "EQUAL 22-SEGMENT MARK · RESOLVED";
  footerState.textContent = "RESOLVED · 0′";
}

function updateTechnical(manifest, state) {
  document.querySelector("[data-public-state]").textContent =
    state.state + " · CHECKPOINT " + state.checkpoint;
  document.querySelector("[data-root-record]").innerHTML =
    "<code>" +
    manifest.root.digital_silence_frames.toLocaleString("en-US") +
    " SILENT FRAMES</code><br><code>STORY SHA-256 " +
    manifest.root.story_source_sha256 +
    "</code>";
  document.querySelector("[data-score-record]").innerHTML =
    manifest.lossless_record.duration_seconds.toFixed(3) +
    " S · " +
    manifest.lossless_record.bits_per_sample +
    "-BIT / " +
    (manifest.lossless_record.sample_rate / 1000).toFixed(0) +
    " KHZ<br><code>FLAC SHA-256 " +
    manifest.lossless_record.flac_sha256 +
    "</code>";
  document.querySelector("[data-phrase-records]").textContent =
    "THREE AES-256-GCM PACKAGES · KEY COMMITMENTS FIXED";
  document.querySelector("[data-completion-record]").innerHTML =
    "AES-256-GCM PACKAGE<br><code>RESPONSE SHA-256 " +
    manifest.final_response.plaintext_sha256 +
    "</code>";
}

async function loadRecord() {
  const publicManifestUrl = new URL(
    "/ENOCH/records/ONE_PATRON_ENOCH_PUBLIC_MANIFEST_v1.0.json",
    document.baseURI,
  );
  const manifestResult = await fetchJson(publicManifestUrl);
  const manifest = manifestResult.value;
  const state = (
    await fetchJson(new URL(manifest.latest_state_file, publicManifestUrl))
  ).value;
  updateTechnical(manifest, state);

  const packageReferences = new Map(
    manifest.sealed_packages.map((item) => [item.id, item]),
  );
  let activeCheckpoint = 0;
  let activePackage = null;
  let activePlaybackName = "";
  let activeLosslessName = "";

  const orderedReleases = [...state.releases].sort((left, right) => {
    const leftReference = packageReferences.get(left.package_id);
    const rightReference = packageReferences.get(right.package_id);
    return Number(leftReference?.completion) - Number(rightReference?.completion);
  });

  for (const release of orderedReleases) {
    const reference = packageReferences.get(release.package_id);
    if (!reference) throw new Error("Unknown release package");
    const openedPackage = await openPackage(reference, release, publicManifestUrl);
    const recordBytes = await openedPackage.open("record");
    const record = JSON.parse(textDecoder.decode(recordBytes));

    if (reference.completion) {
      const response = textDecoder.decode(await openedPackage.open("response"));
      releaseCompletion(record, response);
      activePackage = openedPackage;
      activePlaybackName = "ONE_PATRON_ENOCH_RESOLVED_RECORD_v1.0.wav";
      activeLosslessName = "ONE_PATRON_ENOCH_RESOLVED_RECORD_v1.0.flac";
    } else {
      releasePhrase(record);
      activeCheckpoint = Math.max(activeCheckpoint, record.checkpoint);
      if (document.body.dataset.completion !== "resolved") {
        activePackage = openedPackage;
        activePlaybackName =
          "ONE_PATRON_ENOCH_CHECKPOINT_" +
          String(record.checkpoint).padStart(2, "0") +
          "_v1.0.wav";
        activeLosslessName =
          "ONE_PATRON_ENOCH_CHECKPOINT_" +
          String(record.checkpoint).padStart(2, "0") +
          "_v1.0.flac";
      }
    }
  }

  document.body.dataset.checkpoint = String(activeCheckpoint);
  if (document.body.dataset.completion !== "resolved") {
    footerState.textContent = "UNRESOLVED · " + activeCheckpoint + " / XXI";
  }
  if (activePackage) {
    const playbackBytes = await activePackage.open("playback-audio");
    player.setReleasedSource({
      playbackBytes,
      playbackFilename: activePlaybackName,
      losslessFilename: activeLosslessName,
      losslessLoader: () => activePackage.open("lossless-audio"),
    });
  }
}

revealAvailableSignatures();

loadRecord().catch((error) => {
  console.error(error);
  document.querySelector("[data-public-state]").textContent =
    "UNRESOLVED · RECORD VERIFICATION UNAVAILABLE";
});

window.addEventListener("beforeunload", () => {
  objectUrls.forEach((url) => URL.revokeObjectURL(url));
});
