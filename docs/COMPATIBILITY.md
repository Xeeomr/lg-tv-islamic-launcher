# Compatibility and known limits

TV runtime requirements are separate from the computer's build tools. No-root
requires TV Node.js 0.12.2+ for the compiled Helper; cytv and the source
installer reject older runtimes before installing packages. Root requires TV
Python 3.9+ and Node.js 8+. Root install/setup checks these requirements; recovery
commands do not add a new Node version gate. Passing these checks does not
establish hardware compatibility. Outbound HTTPS uses the
[bundled Mozilla CA store](TLS-TRUST.md).

Helper app/service JavaScript is compiled separately with Babel for Node 0.12,
with local core-js and safe-buffer polyfills loaded before application imports.
Nodes below 10 select the vendored ws 6.2.4 compatibility path; newer runtimes
use ws 8.21.0. The Node 0.12.2 regression exercises controller startup and a local
WebSocket exchange. Input-device access, firmware SSAP behavior, standby and cold
boot still require hardware acceptance on the LG 49UJ750V from issue #47.

The [v1.2.0 stable release](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/tag/v1.2.0) contains cytv 0.3.1, Home 1.4.1, Helper 0.6.19,
Root 0.3.0, both edition Updaters 0.2.1 and Android 0.2.1-preview / code 10.
The latest-download links follow the stable release. Publication does not establish hardware acceptance for every component or model.
Root setup can provision a pinned private ARMv7 Python on eligible TVs without a
suitable interpreter. Working system Python skips the download; compatible
loader/libc, root/Homebrew services, Node.js 8+ and input support remain required.
The issue #37 UK6540PTD / 05.50.70 remains unvalidated for this runtime.
See [optional Python](OPTIONAL-PYTHON.md) and [release scope](RELEASE-1.2.0.md).
Older version rows below are historical hardware reports, not the current package
list. Root has separate [acceptance and lifecycle evidence](../root-edition/RELEASE-ACCEPTANCE.md).

## 1.2.0 acceptance

See the [maintainer confirmation and evidence limits](RELEASE-1.2.0-ACCEPTANCE.md).
Original-device issues remain open for their requested results.

## Historical 1.1.0 hardware evidence

Root **0.2.0**, Root Updater **0.2.0** and System Updater supervisor **1.0.0** were checked on **LG OLED55C3RLA / firmware 43.21.71 / webOS 11.2.0**, using `d344d92` (product contents identical to `4b66951`). Arrows, OK, app launch, Home, Back/Cancel/confirmed exit, volume/mute, triple-Home emergency exit and explicit resume passed. Standby/wake with Emby left open for 70 seconds and the installed-version menus passed; an unavailable update feed showed a friendly message. True cold boot, Helper **0.6.19** on a TV, UK6540PTD, and a complete signed system upgrade or rollback remain untested. Stable publication accepts this limited evidence; it does not validate every model or path.

The remaining version rows below are historical reports.

| Configuration | Status |
| --- | --- |
| LG OLED55C3RLA, firmware 43.21.71 | Hardware used for development and tests |
| Launcher 1.0.13 + helper 0.6.13 | Recovery UI, app icons and hover labels tested on the same TV; underlying 0.6.12 input/watchdog behavior unchanged |
| LG OLED55C46LA (C4), firmware 33.31.68, webOS 24 (SDK 10.3.1) | Community report with Helper 0.6.13: launcher and short Home work. Long Back briefly shows LG Home then redirects to our launcher; holding OK on Resume Home can block interception. After remote power-off/on with Quick Start+ off, one run showed LG Home at boot +31.6 s and our launcher at +33.1 s. EIM registration is unconfirmed because Developer Mode shell calls return no reply. Fixes below await C4 hardware verification |
| Other LG models / firmware / remotes | Unverified |
| macOS build / CLI | Used locally |
| Linux x64 | Graphical `cytv-linux-x64.deb` for Ubuntu 22.04+, Debian 12+, Mint 21+; standalone `cytv-linux-x64` is the CLI. Real-TV/OS acceptance remains separate; Linux ARM desktop packages are not included |
| Windows x64 | Native graphical `cytv-windows-x64-desktop.zip` and separate console wizard. The graphical ZIP requires its `_internal` folder; no Windows publisher signature. Real-TV/OS acceptance remains separate. Source Bash scripts require a compatible environment |
| Android ARM64 preview | Debug-signed `cytv-android-arm64.apk`; emulator/offline checks do not establish physical-TV acceptance. See [Android requirements](../android/README.md) |
| C5 / webOS 26 | Helper startup remains under investigation; no compatibility claim |

The relay requires compatible `LGE M-RCU - Builtin [0]` and `[1]` devices and checks
capabilities before interception. Unsupported or busy devices cause it to exit.
Do not remove these checks to force compatibility.

- Developer Mode expiry may remove sideloaded apps.
- On some firmware (seen on webOS 24) `luna-send-pub` from the Developer Mode shell
  returns no response even for otherwise working services. An empty reply does not
  establish that EIM rejected registration. Setup distinguishes no reply, an explicit
  rejection, a command error and a confirmed success; the guarded fallback remains available.
- Back navigation inside apps remains theirs; exiting may briefly show LG Home.
- Cold startup is not instant and can begin with a black screen. No fixed startup
  time or improvement across firmware is promised.
- Three short Home presses within two seconds stop interception until a manual helper launch; it does not erase data.
- Network and foreground monitoring depends on local SSAP pairing and connectivity.
- Wheel-to-tile navigation is not implemented; wheel events are passed through.
- Initial inventory is prepared during setup. **+ / Add app** requests a fresh
  inventory through the edition service; unavailable discovery falls back to saved
  data. Source builds can also re-sync on the computer. See [app management](APP-MANAGEMENT.md).
- Hiding a tile does not uninstall the app or disable system ads.

This is an alternative launcher, not an LG-supported system Home replacement.

Triple-Home recovery in the updated No-root Helper still needs verification on a physical TV; the reports above describe earlier releases.

## C4 follow-up fixes (hardware verification pending)

- Helper 0.6.15 could disable SSAP on C4 because the installer owns the state
  directory and Developer Mode owns the uploaded files: the helper cannot chmod
  either. Helper 0.6.17 keeps the existing shared paths, attempts 0770 on
  state directories and accepts a non-world-writable 0775 directory owned by the
  packaged prisoner:jailer identity when the runtime belongs to that group.
  A pairing key already at 0640 remains usable. If chmod of a foreign-owned key
  fails, the runtime stages the same key privately and atomically replaces it at
  0640, preserving the shared group for the separate app-inventory service.
  This changes the key's owner to the process performing the repair. Failed
  staging/replacement keeps the original key and SSAP remains disabled if it
  cannot be protected. App-list permission warnings no longer disable SSAP.
  Ordinary relay input, stop flags and boot state paths remain independent.
  Modeled multi-UID tests run on macOS/Linux; real multi-UID tests require Linux
  root and run in CI. C4/C3 hardware validation of this fix is still pending.
  Firmware can still expose the key between boot-time permission changes and
  runtime startup; the boot-time writer has not been identified.
- Resume Home waits up to five seconds for source/destination keys to be released,
  without grabbing the remote, while continuing controller heartbeat/stop handling.
  A timeout or device error retains the persistent stop behavior.
- Back events (code 412) still pass through. A hold of at least 700 ms marks the
  next LG Home transition as intentional; the marker lasts 2.5 seconds after release
  and is consumed once. Holds older than ten seconds are treated as stale.
  Short Home clears the marker and still opens our launcher. These thresholds and
  event ordering need confirmation on C4 and regression testing on C3.
- The C4 report measured a full remote power cycle with Quick Start+ disabled,
  not standby/resume. It does not establish that EIM caused the startup delay.

No-root installer architecture detection reads the ELF header of the TV shell.
A verified little-endian ARM32 userspace is accepted on an ARM32 or aarch64
kernel. Unknown or incompatible runtimes stop before package installation.
The diagnostic report includes allowlisted kernel architecture, userland ABI and
ARM32 verification results, without raw command output. Passing this check does
not certify remote-control, startup or firmware compatibility.
