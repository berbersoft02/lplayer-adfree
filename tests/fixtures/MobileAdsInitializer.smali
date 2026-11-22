.class public Lcom/lplayer/ads/MobileAdsInitializer;
.super Ljava/lang/Object;
.source "MobileAdsInitializer.java"

.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method

.method public static initialize(Landroid/content/Context;)V
    .registers 2
    .param p0, "context"    # Landroid/content/Context;

    .prologue
    new-instance v0, Lcom/lplayer/ads/AdCallback;
    invoke-direct {v0}, Lcom/lplayer/ads/AdCallback;-><init>()V

    invoke-static {p0, v0}, Lcom/google/android/gms/ads/MobileAds;->initialize(Landroid/content/Context;Lcom/google/android/gms/ads/initialization/OnInitializationCompleteListener;)V
    return-void
.end method
