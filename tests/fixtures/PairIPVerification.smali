.class public Lcom/lplayer/security/PairIPVerification;
.super Ljava/lang/Object;
.source "PairIPVerification.java"

.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method

.method public static verifySignature(Landroid/content/Context;)Z
    .registers 3
    .param p0, "context"    # Landroid/content/Context;

    .prologue
    invoke-static {p0}, Lcom/lplayer/security/IntegrityCheck;->getSignature(Landroid/content/Context;)Ljava/lang/String;
    move-result-object v0

    const-string v1, "EXPECTED_SIGNATURE_HASH_PAIRIP"
    invoke-virtual {v0, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2

    if-nez v2, :cond_0

    const/4 v0, 0x1
    invoke-static {v0}, Ljava/lang/System;->exit(I)V

    const/4 v0, 0x0
    return v0

    :cond_0
    const/4 v0, 0x1
    return v0
.end method
