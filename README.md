# LPlayer Ad-Free Mod (Reverse Engineering Analysis)

[![CI](https://github.com/berbersoft02/lplayer-adfree/actions/workflows/ci.yml/badge.svg)](https://github.com/berbersoft02/lplayer-adfree/actions/workflows/ci.yml)

A reverse-engineering case study, automated Smali patch engine, and ad-free modification of LPlayer (Android media and streaming player). This project documents the analysis, PairIP anti-tamper bypass, and neutralization of interstitial and banner ad networks to provide uninterrupted media playback.

---

## Technical Overview

LPlayer is an Android video player frequently used for HLS/DASH streaming and IPTV playback. Recent versions introduced aggressive interstitial ads, tracking SDKs, and integrity protections (PairIP / DEX verification) to detect tampering.

### Scope of Modification

1. **Anti-Tamper Bypass (PairIP):**
   * Neutralized integrity checks and signature validations within secondary DEX (`classes2.dex`).
   * Bypassed runtime tamper-detection and forced-exit handlers (`System.exit`, `Process.killProcess`).

2. **Ad Network Neutralization:**
   * Disabled initialization calls and lifecycle hooks for **Google Mobile Ads (GMA)**, **Pangle**, and **Audience Network**.
   * Removed interstitial ad placement triggers inside player control activities (`MainActivity` playback overlays).
   * Stripped background telemetry and analytics beacons.

3. **Rebuild & Packaging:**
   * Decompiled with `Apktool` and analyzed via `JADX`.
   * Patched via the automated Smali Patch Engine (`patch_engine/`).
   * Reassembled DEX files, 4-byte aligned via `zipalign`, and signed with `apksigner`.

---

## Automated Smali Patch Engine

The repository includes a modular Python patch engine (`patch_engine/`) to automate scanning, bytecode transformations, and integrity verification across decompiled APK trees.

### Usage

```bash
# 1. Scan a decompiled smali directory for targets
python -m patch_engine scan ./decompiled_lplayer/

# 2. Preview planned modifications in dry-run mode
python -m patch_engine patch ./decompiled_lplayer/ --dry-run

# 3. Apply patches with automated backups (.bak) and generate an audit report
python -m patch_engine patch ./decompiled_lplayer/ --report ./audit_report.md

# 4. Verify that all target signatures are neutralized
python -m patch_engine verify ./decompiled_lplayer/
```

### Rule-Based Configuration

Patch rules are defined declaratively in [`patch_engine/rules.json`](patch_engine/rules.json), mapping target class patterns and method signatures to transformation strategies:
- `stub_return_void`: Clears method body and emits `return-void` (for ad SDK initializers).
- `stub_return_bool_true`: Clears method body and emits `const/4 v0, 0x1` / `return v0` (for PairIP signature check).
- `neutralize_exit_calls`: Comments out or bypasses `System.exit` / `Process.killProcess` invocations.

---

## Testing & CI

A comprehensive unit test suite validates the scanner, bytecode transformer, idempotency, and CLI functionality:

```bash
python -m unittest discover -s tests -v
```

All modifications are validated across Python 3.10 through 3.13 in [GitHub Actions CI](.github/workflows/ci.yml).

---

## Tools Used

* **Decompilation & Static Analysis:** JADX-GUI, Apktool, Ghidra
* **DEX / Smali Editing:** Smali / Baksmali, `patch_engine`
* **Packaging:** `zipalign`, `uber-apk-signer`

---

## Downloads

Pre-built, aligned, and signed APK packages are available in the [Releases](https://github.com/berbersoft02/lplayer-adfree/releases) section:

* **[Download Latest APK](https://github.com/berbersoft02/lplayer-adfree/releases/latest)**

---

## Disclaimer

This repository is provided strictly for educational and security research purposes, demonstrating Android application analysis, Smali patching, and reverse engineering techniques.
