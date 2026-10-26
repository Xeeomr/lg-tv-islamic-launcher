# CYTV Android implementation plan

**Goal:** Build a self-contained Android APK using the CYTV No-root and Root installer, and deliver screenshots.

**Spec:** `docs/superpowers/specs/2026-10-24-cytv-android-design.md`

**Architecture:** Kotlin WebView shell and foreground worker, offline UI, Chaquopy Python adapter calling the existing CLI. No second installer implementation.

## Tasks

- [x] Add failing Python tests for Android config validation, explicit fingerprint approval, hidden credential prompts, injected payload and command dispatch. Run with `python3 -m unittest discover -s android/tests`.
- [x] Implement `android/app/src/main/python/android_bridge.py`; add optional `payload_root` to `cytv.cli.main`. Preserve desktop behavior and existing Root recovery confirmations.
- [x] Build the offline responsive UI under `android/app/src/main/assets/ui/`, with Kotlin bridge handling, version/recovery dialogs, visible input errors and preview-only simulations clearly labeled.
- [x] Add the Kotlin Activity/service, private key document import, operation event replay and notifications. Restrict WebView to bundled content and disable backups.
- [x] Add Gradle/Chaquopy build configuration and public-source staging script; verify the embedded TV payload and exclude desktop Qt dependencies and private state.
- [x] Build APK with downloaded tools in temporary directories. Exercise browser UI and, where available, emulator startup/rotation/prompt flows. Save screenshots and run `scripts/test.sh`.
- [x] Document build, installation, device requirements, privacy, recovery and hardware validation limits in `android/README.md`; report exact artifact and checks.

## Verification record

- Android assembleDebug and lintDebug: passed (two expected warnings: ARM64-only ChromeOS ABI coverage and JavaScript enabled for the bundled offline UI).
- Python adapter: 7 tests passed; existing CLI regression suite: 27 tests passed.
- `scripts/test.sh`: passed with the repository virtual environment and localhost permission (461 Root Python + 35 setup + 185 CYTV + 2 preview Python tests, plus JavaScript/native-C suites).
- Browser UI: No-root/Root, IP/port/key validation, trust, hidden secrets, recovery and 320–1024px widths passed.
- Android 15 ARM64: app launches; both edition screens captured; No-root hidden passphrase callback and missing-Key-Server recovery passed; Root real SSH fingerprint confirmation and hidden password callback passed against a loopback fixture rejecting a dummy password. No commands were executed on a physical TV.
- Actual Android screenshots: `android/screenshots/android-*`; browser simulated states are explicitly labeled separately.
- Installable artifact: `dist/android/cytv-android-0.1.0-preview-arm64.apk`, debug signed.

## Review follow-up

Independent read-only review identified preview payload caching by versionCode, outdated WebView handling and form preservation during key import. Fixed all three: manifest-SHA256 cache directories, a native WebView 108+ feature check/update message, and saving form values before key import. The key-import regression was observed failing before the fix and passing afterward. Final assembleDebug/lintDebug and UI checks passed; the final APK was reinstalled with the same versionCode and the native No-root callback/recovery test passed. The new manifest-hash cache directory was confirmed inside the emulator.

## B1 identity and equal editions follow-up

User requested the existing B1 identity across Android, desktop and console installers, then explicitly rejected bright UI fills. Original house/icon colours are retained; working surfaces and buttons use quiet warm charcoal and muted neutrals. Android initially selects neither edition. Recommendation labels and preferential advice were removed from shared CLI, translations, README and all ten user guides. Model/firmware evidence remains scoped. Packaged B1 SVGs are hash-verified, and native Android/Qt screenshots were refreshed. Android preview is 0.1.1 (versionCode 2).
