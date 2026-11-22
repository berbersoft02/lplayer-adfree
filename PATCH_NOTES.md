# Technical Reverse Engineering & Patch Notes

Documentation of bytecode modifications performed on LPlayer 2.0.5.

## 1. Anti-Tamper & PairIP Bypass

### Analysis
PairIP integrity verification is embedded within secondary DEX (`classes2.dex`) under classes matching `*PairIPVerification*` and `*SecurityCheck*`. The application computes signature and DEX checksums at startup and calls `java/lang/System;->exit(I)V` or `android/os/Process;->killProcess(I)V` if an unexpected signature hash is encountered.

### Smali Transformation
- **Rule ID:** `PAIRIP-001`
- **Target:** `verifySignature(Landroid/content/Context;)Z`
- **Strategy:** `stub_return_bool_true`
```smali
.method public static verifySignature(Landroid/content/Context;)Z
    .registers 1

    # [PATCHED: Integrity check forced true]
    const/4 v0, 0x1
    return v0
.end method
```

- **Rule ID:** `PAIRIP-002`
- **Target:** `System.exit(I)V` and `Process.killProcess(I)V`
- **Strategy:** `neutralize_exit_calls`
```smali
    # [PATCHED: neutralized] invoke-static {0}, Ljava/lang/System;->exit(I)V
    # [PATCHED: neutralized] invoke-static {v0}, Landroid/os/Process;->killProcess(I)V
```

Reference patch diff: [`patches/pairip_bypass.patch`](patches/pairip_bypass.patch)

---

## 2. Ad Network Removal

### Analysis
LPlayer initializes three primary ad mediation providers during application startup and main playback activity creation:
1. **Google Mobile Ads (GMA)**: `Lcom/google/android/gms/ads/MobileAds;->initialize`
2. **ByteDance Pangle SDK**: `Lcom/bytedance/sdk/openadsdk/TTAdSdk;->init`
3. **Facebook Audience Network**: `Lcom/facebook/ads/AudienceNetworkAds;->initialize`

### Smali Transformation
- **Rule IDs:** `GMA-001`, `PANGLE-001`, `AUDIENCE-001`, `TELEMETRY-001`
- **Strategy:** `stub_return_void`
```smali
.method public static initialize(Landroid/content/Context;)V
    .locals 0

    # [PATCHED: Ad/tamper routine stubbed]
    return-void
.end method
```

Reference patch diff: [`patches/ad_neutralization.patch`](patches/ad_neutralization.patch)

---

## 3. Automated Reproduction

All transformations are managed declaratively via [`patch_engine/rules.json`](patch_engine/rules.json) and applied using the automated patch engine:

```bash
python -m patch_engine patch <decompiled_apk_dir> --report audit_report.md
```
