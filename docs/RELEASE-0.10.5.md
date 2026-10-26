# v0.10.5 — Clear updates and recovery

Includes cytv **0.2.8**, Home **1.3.3**, Home Helper **0.6.16**,
Root Edition **0.1.6**, and No-root Updater **0.1.5**.

Root Software updates shows the available version and release notes only when
the release is at least as new as the installed version. An older feed no longer
appears as an available update.

**Recovery** opens its own screen with the saved transaction’s rollback version,
or the reason rollback is unavailable. **Refresh status** checks unfinished
operations. The rollback confirmation names the exact version; **Back** returns
to Software updates and restores focus. Confirmed updates cannot be rolled back
through this recovery flow, and unknown installer outcomes remain blocked.
New messages are translated into all ten supported languages.

Before installation, cytv shows installed → bundled versions for the selected
edition and identifies first installations, reinstalls and downgrades.

The user verified the updated Software updates and Recovery interface with the
TV remote on the existing LG C3 / firmware 43.21.71 installation. This was an
interface-only deployment to Root 0.1.3 with preserved settings and updater state;
it does not establish full installation or rollback acceptance for the new
0.1.6 package. Existing startup and hardware limitations remain unchanged.

## Downloads

- macOS Apple Silicon: `cytv-macos-arm64.zip`; Intel: `cytv-macos-x64.zip`.
- Ubuntu / Debian / Linux Mint x64: `cytv-linux-x64.deb`.
- Windows x64: `cytv-windows-x64.exe` (console wizard).
- Console executables and complete Root/No-root manual bundles are included.

The installers and manual bundles contain the new Root application and existing
recovery runtime. The signed Root update feed offers Root 0.1.6 for compatible installed updater
infrastructure, with a verified cached rollback package required. The standalone
IPK matches the manual bundle exactly. This app update does not replace recovery
infrastructure; No-root automatic-update feeds remain unchanged.

`BUILD-INFO.json` records source and build provenance; `SHA256SUMS` covers the
release assets. macOS builds are ad-hoc signed, not Apple-notarized.
