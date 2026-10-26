# v0.10.3 — Localized setup, recovery and Termux build fixes

Includes cytv **0.2.6**, Home **1.3.2**, Home Helper **0.6.16**,
Root Edition **0.1.4**, and No-root Updater **0.1.4**.

## Downloads

- macOS Apple Silicon: `cytv-macos-arm64.zip`; Intel: `cytv-macos-x64.zip`.
  Extract `cytv.app`, move it to Applications and open it.
- Ubuntu / Debian / Linux Mint x64: `cytv-linux-x64.deb`.
- Windows x64: `cytv-windows-x64.exe` (console wizard).
- Separate console executables and complete manual-install bundles are included.

The installer and TV interfaces now include ten languages with automatic system
language selection and a saved manual choice. See the
[desktop guide](DESKTOP_INSTALL.md) and [manual installation](MANUAL_INSTALL.md).
Mac builds are ad-hoc signed, not Apple-notarized; use the documented
Privacy & Security → Open Anyway process if required. Do not disable Gatekeeper.

## New desktop installer

macOS and Linux now use a redesigned desktop wizard with a visible four-step
setup rail, side-by-side Root/No-root choices, keyboard focus indicators and
collapsible maintenance actions. The layout adapts to smaller desktop windows;
password masking, safe cancellation and conservative destructive defaults remain.

## Setup, removal and recovery

- Complete translations for interrupted setup, Root reinstallation, full removal
  and recovery across all supported languages.
- Reconcile interrupted Root setup and verify the updater connection before
  activating or reinstalling Root. Unknown package outcomes remain blocked.
- Full project removal cleans Root Updater, its service, startup hooks and owned
  retained app permissions. Inactive recovery records remain for diagnostics.
- Include the Home startup and bounded standby recovery fixes discussed in #10.

For interrupted setup, use **Check TV status** before retrying. Keep recovery
files; save a diagnostic report if the installer cannot establish a safe retry.

## Source installation and Termux

- Correct Helper package permissions using its actual `appinfo.json` version,
  even when older IPKs remain in `dist/`.
- Honor Zig 0.14.1 supplied through `ZIG` or `PATH`, without trying to install the
  Android-incompatible `ziglang` Python distribution. Termux without a compiler
  stops with instructions before pairing. See [Termux setup](INSTALL.md#termux--android).

## Validation and compatibility

CI tests pass on Linux and macOS; the cytv binaries are built and tested natively
for Windows x64, Linux x64, macOS Apple Silicon and macOS Intel. Embedded public
payloads are verified during builds. `BUILD-INFO.json` records source revisions
and build provenance, and `SHA256SUMS` covers the downloadable assets.

All installer binaries are freshly built with the new desktop interface and
verified public payloads. Manual bundles contain the current TV packages; the
source archive includes the Termux and package-permission fixes.

This does not certify every TV model. QNED80T feedback for #10 remains pending;
C5/webOS 26 Helper startup in #12 still needs diagnostic logs. End-to-end Termux
hardware behavior remains unverified. Root compatibility retains the scoped C3
evidence and limitations in [compatibility notes](COMPATIBILITY.md).

Previous signed update feeds are preserved byte-for-byte. This release does not
offer recovery-infrastructure migrations through those feeds or replace them
with unsigned updates. Use the computer installer/manual workflow for these
component versions.
