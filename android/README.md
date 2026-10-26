# CYTV for Android — 0.2.1-preview candidate (versionCode 10)

**[v1.2.0 stable](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/tag/v1.2.0)** includes cytv **0.3.1**, Home **1.4.1**, Helper **0.6.19**, Root **0.3.0** and both edition Updaters **0.2.1**, and Android **0.2.1-preview / code 10**. Android remains a preview within the stable distribution. Latest-download links follow the published release; see [release notes](../docs/RELEASE-1.2.0.md) and [scoped hardware acceptance](../docs/RELEASE-1.1.0-ACCEPTANCE.md).

No-root and Root are equal options for different TV environments: Developer Mode or existing root SSH. Neither edition is preferred generally. After the connection check, CYTV highlights the edition matching an unambiguous detected SSH endpoint; root privileges still require verification after sign-in.

The interface uses the approved B1 house mark in its original colours, with quiet warm charcoal surfaces and muted controls. Orange is confined to the identity rather than large button/background fills.

A self-contained Android installer for the existing No-root and Root editions of Clean Your TV. The interface supports the same ten languages as desktop: English, German, Spanish, Brazilian Portuguese, French, Italian, Korean, Hindi, Polish and Russian, with the Android system font, a bundled Noto Sans fallback, readable text sizes, offline UI and TV packages. The optional TV Python runtime archive is a separate
verified on-demand download, rather than part of the APK. On first launch it follows the phone language (English for unsupported languages). The top-right control shows the current language; tap it to open a list with native language names and a checkmark. Your choice is saved on this phone. No PC, Termux, Python installation on the phone, or cloud service is required to run the APK.

## Install and connect

1. Copy the preview APK to a **64-bit ARM phone running Android 7.0 or later with Android System WebView/Chrome 108+**. Allow the browser/file manager to install this APK when Android requests it.
2. Keep the phone and LG webOS TV on the same local network. Turn the TV on; disconnect VPNs or guest-network isolation if the connection fails.
3. Enter the TV IPv4 address and check the connection first. Then choose **No-root** for Developer Mode, or **Root** for a TV with existing root SSH access. Exactly one responding access mode is highlighted; with both or neither, choose manually. Default SSH ports are 9922 and 22 respectively; Root ports are editable.
4. No-root: enable **Dev Mode Status** and **Key Server** in the TV's Developer Mode app. Enter its passphrase when CYTV asks. Root: use the existing SSH password or select a private key with Android's file picker. Encrypted keys prompt for their passphrase.
5. Review the SSH fingerprint before trusting the TV. Review the actual installed/package versions before confirming installation. Accept the remote-control pairing prompt on the TV if shown.
6. Keep the TV on. The foreground service continues while the Activity is in the background; keep Android's CYTV notification available. Do not force-stop the app or change networks during installation.
7. Check Home, arrows/OK, Back, volume and standby/wake on the TV. Root requires existing compatible root, Python 3.9+, Node.js 8+, Homebrew services
   and supported ARM32 remote input on the TV. Eligible missing Python can be supplied
   as a pinned private ARMv7 runtime downloaded on the phone and transferred via SSH;
   a compatible TV loader/libc is still required. Working system Python skips this download.
   See [runtime limits](../docs/OPTIONAL-PYTHON.md). CYTV does not root or flash the TV.

This is a **debug-signed preview**, not a public production release. End-to-end installation from a physical phone to a physical TV still needs validation for **both editions**. Older 32-bit phones and x86 devices are not included in this APK. The initial UI includes install, status and restore; it does not expose uninstall or automatic discovery. The full TV app inventory is imported automatically. Compatible whole-edition TV updates require separate computer-assisted System
Updater bootstrap with root/Homebrew services. Unrooted TVs use the installer.
The APK does not expose that bootstrap action; see [updates](../root-edition/UPDATES.md).

## Recovery and private data

Use **Status and recovery** from the start screen. The selected action stays visible while you choose the TV connection method; status and restore show their own progress without installation steps. The Android notification describes an ongoing TV operation. After an interrupted operation, check status before reinstalling. CYTV retains the existing durable operation receipts and never automatically repeats installation after process death. Activity recreation replays the current operation and pending question. Pending questions time out after ten minutes; the foreground wake lock is bounded to 25 minutes. OS process/service termination can still interrupt networking; retained receipts remain authoritative. An unfinished No-root removal is resumed
only through its existing verified flow and a separate confirmation; unknown removal
outcomes stay blocked. The preview has no uninstall action, so use desktop/CLI
with the retained connection and evidence when removal is required. Status and
restore do not download a new Python. Referenced runtime slots remain for recovery.

Three short Home presses within two seconds request the existing TV emergency exit. Older No-root Helper versions through 0.6.13 instead use holding Home for two seconds. Root cold-power behavior and model compatibility retain the limitations documented by the TV project.

Profiles, imported keys and pairing data live in the app-private directory. Android backup is disabled. Passwords are requested on demand and are not written to the UI log or preferences. Imported keys persist for later use; uninstalling Android CYTV removes them and the local recovery receipts. Raw logs remain local and can contain TV addresses; no automatic sharing/export is implemented. The Android package needs Internet/network access for local TV sockets, foreground-service/notification permissions and a bounded wake lock. Cleartext is enabled for the TV's Developer Mode Key Server; the WebView itself blocks all network navigation and serves only bundled files.

## Build

Run builds from the maintained project root. Requires JDK 17, Python 3.12, Android SDK platform 35/build-tools 35.0.0/platform-tools and accepted SDK licenses. Gradle 8.13 is pinned by the wrapper; Android Gradle Plugin 8.9.2 and Chaquopy 17.1.0 are pinned in the build.

From the repository root, prepare a public TV payload using the existing build flow (or use an already built, hash-verified `build/cytv/payload`):

```sh
python3.12 -m venv android/.build-venv
android/.build-venv/bin/pip install -r cytv/requirements.txt ziglang==0.14.1
android/.build-venv/bin/python scripts/build-cytv.py --payload-only
export CYTV_BUILD_PYTHON="$PWD/android/.build-venv/bin/python"
export ANDROID_HOME=/path/to/android-sdk
export JAVA_HOME=/path/to/jdk-17
cd android
./gradlew :app:assembleDebug :app:lintDebug
```

Output: `android/app/build/outputs/apk/debug/app-debug.apk` relative to the repository root. No release signing material is stored in the repository. The first build downloads dependencies; runtime installation uses the embedded payload. Runtime extraction is cached by the bundled manifest SHA-256, so reinstalling a preview with the same versionCode cannot reuse a different older payload. Staging validates every payload hash and copies only public source modules, excluding Qt/desktop entry points, caches and local profiles. It does not automatically rebuild TV payloads during Gradle execution.

Python dependencies are resolved normally against PyPI and the official Chaquopy wheel index: Paramiko 3.5.1, websockets 15.0.1, cryptography 42.0.8, bcrypt 3.2.2 and PyNaCl 1.5.0. Python 3.12/arm64 is used because its available bcrypt wheel satisfies Paramiko's minimum version; dependency constraints are not bypassed. These versions are the available Android package combination, not a claim that all packages are the latest upstream versions.

## Checks and screenshots

```sh
# Repository Python dependencies must be installed in the chosen interpreter.
python3 -m unittest discover -s android/tests
bash scripts/test.sh
# Requires Playwright and a local Chrome; CYTV_CHROME can override its executable.
node android/tests/ui.cjs
node android/tests/localization.cjs
node android/tests/maintenance.cjs
node android/tests/screenshots.cjs
```

The localization suite checks all ten complete catalogs, system-language resolution, the current-language picker, saved selection, preserving connection fields, localized native requests and progress, and returning from recovery to a fresh installation. Operation logs and the foreground notification use the language selected when the operation starts; changing the interface language does not rewrite earlier logs.

The browser suite covers both editions, IP/port/key validation, explicit trust, secret isolation, error recovery and widths 320/375/412/768/1024. Files `screenshots/01-*` through `05-*` show the same offline UI in browser demonstration mode, clearly labeled; progress and completion there are simulated.

The `screenshots/android-language-*` files and `android-languages-overview.png` show the actual APK language picker and Russian, German, Korean and Hindi screens. Run `node android/tests/languages-emulator.cjs` against the same forwarded debug WebView to check all ten languages and recreate them.

Files `screenshots/android-*` are screenshots of the actual debug APK on an Android 15 ARM64 emulator. Native smoke checks reached the real Python No-root code/passphrase request, then tested the recovery result for an unavailable synthetic Key Server. The Root negative SSH fixture checked the real fingerprint confirmation and hidden password callback, then rejected an intentionally invalid synthetic password. It never executes TV commands. These checks do not establish successful hardware installation.

For native smoke tests, forward the APK's debug WebView socket (`adb shell cat /proc/net/unix` identifies `webview_devtools_remote_PID`) with `adb forward tcp:9228 localabstract:webview_devtools_remote_PID`. Run `node android/tests/emulator.cjs` with `CYTV_ADB` set to adb's path. For the Root negative fixture, run `python android/tests/root-handshake.py` first, then set `CYTV_TEST_ROOT=1` for the Node command. To avoid an older fixture’s remembered host key, set a fresh `CYTV_TEST_SSH_PORT` in both commands. Start the app on its Russian welcome screen with no operation running. WebView debugging is enabled only in debug builds; it is disabled in release builds.
