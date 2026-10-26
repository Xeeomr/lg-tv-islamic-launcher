# v0.10.0 — Desktop setup without terminal commands

cytv 0.2.0 includes Home 1.3.1, Home Helper 0.6.15 and Root 0.1.3.
The separate No-root Home Updater remains 0.1.3.

## Download and open

- **macOS Apple Silicon:** extract `cytv-macos-arm64.zip`, move `cytv.app` to Applications and open it.
- **macOS Intel:** use `cytv-macos-x64.zip` in the same way.
- **Ubuntu / Debian / Linux Mint x64:** open `cytv-linux-x64.deb` in the graphical package installer, then open **Clean Your TV** from the applications menu.
- **Windows x64:** open `cytv-windows-x64.exe`; the existing console wizard remains available.

Mac/Linux desktop packages open a window with TV discovery, edition selection,
masked password entry and buttons. No terminal commands or Python installation
are needed. The separate console executables are still included for scripting
and maintenance. See the [desktop guide](DESKTOP_INSTALL.md) for supported systems
and first-launch steps.

macOS builds are ad-hoc signed, not Apple-notarized. The first launch may require
**System Settings → Privacy & Security → Open Anyway**. Do not disable Gatekeeper.

## Included changes from main

- Preserve saved Home apps when a TV inventory refresh returns only some apps.
- Fix Helper state permissions, startup recovery and Back handling for the C4-related cases.
- Install and verify Root Updater and its rollback baseline alongside a fresh Root installation.
- Keep recovery and existing-updater checks before activating or reinstalling Root.

Root turns on Home control and opens Clean Your TV Home immediately. There is no
trial, countdown or Keep confirmation. No-root still requires LG Developer Mode;
Root requires existing root and SSH access. cytv does not root the TV.

## Diagnostics and recovery

Desktop failures offer **Save diagnostic report…** and **Open an issue**. Reports
exclude credentials, SSH key paths and raw TV logs. The installer waits for active
TV operations to finish before allowing exit. SSH identity changes remain blocked.
Use **Return to LG Home**, the maintenance action in cytv, or the documented
emergency Home gesture to restore LG Home.

## Manual bundles and update feeds

Both complete manual-install bundles are rebuilt from this release's source.
See [manual installation](MANUAL_INSTALL.md). Previous signed update feeds are
preserved byte-for-byte for compatibility. This release does not publish unsigned
updates or offer recovery-infrastructure migrations through those feeds.

`SHA256SUMS` covers the downloadable files. Hardware compatibility remains scoped
to the evidence in [compatibility notes](COMPATIBILITY.md); desktop build tests do
not certify every TV model or desktop distribution.
