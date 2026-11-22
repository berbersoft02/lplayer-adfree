.class public Lcom/lplayer/ads/AudienceNetworkInitializer;
.super Ljava/lang/Object;
.source "AudienceNetworkInitializer.java"

.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method

.method public static initialize(Landroid/content/Context;)V
    .registers 1
    .param p0, "context"    # Landroid/content/Context;

    .prologue
    invoke-static {p0}, Lcom/facebook/ads/AudienceNetworkAds;->initialize(Landroid/content/Context;)V
    return-void
.end method
