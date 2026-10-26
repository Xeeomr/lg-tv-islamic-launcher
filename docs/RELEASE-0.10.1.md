# v0.10.1 — Root installation repair

cytv 0.2.1 fixes the personalized Root rollback package rejected during Root
Updater setup. TV app versions remain Home 1.3.1, Helper 0.6.15 and Root 0.1.3.

## Recover an interrupted installation

Open the updated cytv and choose **Check TV status**. If it reports **Ready to
reinstall Root**, return to the start screen, choose **Set up my TV**, and confirm
reinstallation. cytv preserves the previous operation report before allowing this
retry. If verification cannot establish a safe retry, the operation remains
blocked; save the diagnostic report instead of deleting recovery files.

## First launch on macOS

If macOS says **cytv was not opened** because Apple cannot verify the app, click
**Done**. Open **System Settings → Privacy & Security**, scroll to **Security**,
then click **Open Anyway** for cytv. Authenticate if requested and click **Open**.
Only approve the app downloaded from this project's release. Our current build
is not Apple-notarized; do not disable Gatekeeper.

Allow **Local Network** access. If permission was changed after a connection
failure, quit and reopen cytv, then choose **Check TV status**.
See the [desktop installation guide](DESKTOP_INSTALL.md) for details and other systems.
