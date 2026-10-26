# v0.10.4 — Our Home from startup

Includes cytv **0.2.7**, Home **1.3.3**, Home Helper **0.6.16**,
Root Edition **0.1.5**, and No-root Updater **0.1.5**.

Root now preserves the confirmed Home profile during normal shutdown. webOS
can open Clean Your TV as its first application, instead of opening LG Home
and switching later. Startup still renews the guarded routing transaction;
explicit exit, emergency recovery and health failures retain stock restoration.
The input observer also accepts the intentionally retained shutdown profile.

Two firmware-managed restarts with reason `remoteKey` on the existing
OLED55C3RLA / firmware 43.21.71 installation selected our Home as the first app.
The user also confirmed normal operation. Direct AC power-loss behavior and
other TV models remain unverified. A direct `systemctl reboot` can still be
classified as an input fault and disable Home control; use webOS power controls.

Settings explain that **Open LG Home** visits LG Home once while preserving the
saved Home choice. Software installation and recovery now show an explicit
confirmation dialog, with translations across the supported languages.
The shared installation, edition, maintenance and recovery guides are updated.

## Downloads

- macOS Apple Silicon: `cytv-macos-arm64.zip`; Intel: `cytv-macos-x64.zip`.
- Ubuntu / Debian / Linux Mint x64: `cytv-linux-x64.deb`.
- Windows x64: `cytv-windows-x64.exe` (console wizard).
- Console executables and complete Root/No-root manual bundles are included.

Installer payloads contain the new recovery runtime. Existing Root installations
need the computer installer/manual reinstall workflow to receive that runtime;
an application-only signed update does not migrate recovery infrastructure.
Previous signed update feeds are preserved unchanged. This release does not
replace them with unsigned updates.

`BUILD-INFO.json` records build provenance; `SHA256SUMS` covers release assets.
macOS builds are ad-hoc signed, not Apple-notarized. Hardware evidence is scoped
to the tested installation; C5/webOS 26 Helper startup remains under investigation.
