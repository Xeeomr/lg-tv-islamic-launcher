# v0.10.9 — Android preview and Windows graphical installer

Includes cytv **0.2.12** and Android **0.1.3-preview**, with Home **1.3.5**, Helper **0.6.16**, Root **0.1.9**, and No-root
Updater **0.1.5**. The signed rollback uses the exact Home 1.3.4 package
from v0.10.8. Helper and Updater versions are unchanged.

Home 1.3.5 includes the merged webOS 5 network-settings repair (PR #16):
the Wi-Fi shortcut tries the first-use network overlay, then network settings,
then the main settings app. This source change requires the Home version bump;
the input menu also returns focus to the top buttons when Up is pressed at its first row (PR #17). New hardware acceptance has not been claimed.

Root 0.1.9 includes the current shared Home UI and these navigation repairs.
The previous Root number could not be reused because the package bytes changed.
Helper 0.6.16 is reused byte-for-byte from the published v0.10.8 bundle; its
SHA-256 is pinned in the source builder. Its pending source icon refresh does not
change the public recovery baseline.

Windows x64 now includes `cytv-windows-x64-desktop.zip`. Extract the whole
archive and open `cytv-desktop/cytv-desktop.exe`, keeping `_internal` beside it.
The graphical wizard includes Python, Qt and the TV packages and opens without
a console. The separate Windows console EXE remains available. Windows publisher
signing is not configured. Native Windows CI checks both the frozen application
and the extracted public ZIP before release assembly.

`cytv-android-arm64.apk` is a self-contained, debug-signed Android preview for
ARM64 phones running Android 7.0+ with Android System WebView/Chrome 108+.
It supports No-root and existing Root SSH access. Enter the TV address first,
check connectivity, then choose the matching environment. No-root and Root are
equal options for different TV setups; ambiguous checks leave the choice manual.
The installer does not root the TV or modify its firmware.

Android supports all ten desktop languages. The header shows the current
language and opens a picker with native language names, a selected checkmark
and saved selection. On first launch it follows the phone language, with English
fallback. UI, credential dialogs and progress are localized; operation logs and
the foreground notification use the language selected when the operation starts.

All installers use the approved house identity with quiet charcoal surfaces and
muted controls. README download buttons use platform symbols and stable latest
asset links for Windows GUI, Android, both macOS architectures and Linux DEB.

The Android preview signer is retained across builds so later preview APKs can
update the same app installation. CI checks compiled package metadata, certificate,
APK hash, embedded payload hashes and actual TV component versions. The release
includes its public build report, `BUILD-INFO.json` and `SHA256SUMS`.

Automated browser and Android emulator checks cover language selection,
persistence, narrow layouts, both edition paths, hidden credential requests,
explicit SSH trust and safe failure recovery against local synthetic fixtures.
No successful physical-phone-to-TV installation is claimed for either edition.
Existing hardware evidence and cold-power limitations keep their original scope.
