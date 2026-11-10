# LPlayer Ad-Free Mod (Reverse Engineering Analysis)

A reverse-engineering case study and ad-free modification of LPlayer (Android media and streaming player). This project documents the analysis, PairIP anti-tamper bypass, and neutralization of interstitial and banner ad networks to provide uninterrupted media playback.

---

## Technical Overview

LPlayer is an Android video player frequently used for HLS/DASH streaming and IPTV playback. Recent versions introduced aggressive interstitial ads, tracking SDKs, and integrity protections (PairIP / DEX verification) to detect tampering.

### Scope of Modification

1. **Anti-Tamper Bypass (PairIP):**
   * Neutralized integrity checks and signature validations within secondary DEX (`classes2.dex`).
   * Bypassed runtime tamper-detection and forced-exit handlers.

2. **Ad Network Neutralization:**
   * Disabled initialization calls and lifecycle hooks for **Google Mobile Ads (GMA)**, **Pangle**, and **Audience Network**.
   * Removed interstitial ad placement triggers inside player control activities (`MainActivity` playback overlays).
   * Stripped background telemetry and analytics beacons.

3. **Rebuild & Packaging:**
   * Decompiled with `Apktool` and analyzed via `JADX`.
   * Reassembled DEX files, 4-byte aligned via `zipalign`, and signed with `apksigner`.

---

## Tools Used

* **Decompilation & Static Analysis:** JADX-GUI, Apktool, Ghidra
* **DEX / Smali Editing:** Smali / Baksmali
* **Packaging:** `zipalign`, `uber-apk-signer`

---

## Downloads

Pre-built, aligned, and signed APK packages are available in the [Releases](https://github.com/berbersoft02/lplayer-adfree/releases) section:

* **[Download Latest APK](https://github.com/berbersoft02/lplayer-adfree/releases/latest)**

---

## Disclaimer

This repository is provided strictly for educational and security research purposes, demonstrating Android application analysis, Smali patching, and reverse engineering techniques.
