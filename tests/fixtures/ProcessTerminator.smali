.class public Lcom/lplayer/security/ProcessTerminator;
.super Ljava/lang/Object;
.source "ProcessTerminator.java"

.method public static terminateOnTamper()V
    .registers 1

    invoke-static {}, Landroid/os/Process;->myPid()I
    move-result v0

    invoke-static {v0}, Landroid/os/Process;->killProcess(I)V
    return-void
.end method
