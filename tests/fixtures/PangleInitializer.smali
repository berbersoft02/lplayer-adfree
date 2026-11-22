.class public Lcom/lplayer/ads/PangleInitializer;
.super Ljava/lang/Object;
.source "PangleInitializer.java"

.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method

.method public static init(Landroid/content/Context;)V
    .registers 2
    .param p0, "context"    # Landroid/content/Context;

    .prologue
    new-instance v0, Lcom/bytedance/sdk/openadsdk/TTAdConfig$Builder;
    invoke-direct {v0}, Lcom/bytedance/sdk/openadsdk/TTAdConfig$Builder;-><init>()V

    invoke-static {p0, v0}, Lcom/bytedance/sdk/openadsdk/TTAdSdk;->init(Landroid/content/Context;Lcom/bytedance/sdk/openadsdk/TTAdConfig;)V
    return-void
.end method
