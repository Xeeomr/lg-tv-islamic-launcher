# Clean Your TV — user guide

No-root and Root are equal options for different TV setups. Choose No-root for LG Developer Mode or Root for existing root SSH access. Compatibility and test coverage remain specific to each edition.

## Before installation

This guide covers **[v1.2.0 stable](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/tag/v1.2.0)**. Latest-download links follow the published stable release. See the [installation guide](../INSTALL.md) and [release notes](../RELEASE-1.2.0.md).

The release contains cytv **0.3.1**, Home **1.4.1**, Home Helper **0.6.19**, Root Edition **0.3.0**, Home Updater and Root Updater **0.2.1**, Android **0.2.1-preview** (version code **10**) and System Updater supervisor **1.0.0** (protocol **1**). These are the v1.2.0 release components.

Keep the TV on and the computer on the same trusted local network. No always-on computer is needed afterward. Compatibility depends on model, firmware and remote; Root has outstanding hardware checks.

- **No-root:** enable LG Developer Mode and Key Server. Enter the passphrase displayed on the TV and accept the separate TV pairing request. Developer Mode must remain active; expiry can remove sideloaded apps. Monitor its official timer even with Beta renewal enabled. Helper monitoring needs local networking.

The updated No-root Helper requires TV Node.js 0.12.2 or newer. The installer checks the TV runtime before installation. Older published packages do not gain this compatibility automatically; input-device access and standby/cold boot still need testing on each model.

- **Root:** existing root SSH access is required. The installer does not root the TV. Do not enable Developer Mode on an existing rooted setup. Keep root access and recovery services available.

## Optional Python for Root in v1.1.0

Root needs a working Python **3.9+** on the TV. The installer checks the required modules (including `json` and `fcntl`), locking, filesystem and subprocess operations; the version number alone is insufficient. A suitable existing interpreter avoids the extra download. Otherwise setup downloads verified **CPython 3.13.17 for ARMv7 soft-float** on the computer or Android device, then transfers it over trusted SSH; the TV does not need Internet access. This optional archive is not bundled in ordinary installers: about **26.3 MB** downloaded, **51.5 MB** for normalized SSH transfer and **119.3 MB** installed, with **320 MiB** free required for initial staging. The private runtime does not replace system Python, libc or global PATH.

The runtime still needs a compatible loader and libraries. Root SSH, Node.js **8+**, `luna-send` and the webOS application/service directories remain required; No-root Helper needs Node.js **0.12.2+**. LG UK6540PTD / firmware 05.50.70 / ARM32 (issue #37, Python 2.7.12 with no Python 3) has **not** passed hardware acceptance with this runtime. QEMU tests do not establish TV, cold-boot, remote-input or rollback compatibility. Historical hardware results apply only to their recorded model, firmware and artifacts.

To prepare a verified cache on an Internet-connected computer **without contacting a TV**:

```sh
./cytv --language en --prepare-python-runtime
```

Use the same private data directory for setup; when moving a cache, prepare a fresh dedicated directory with `--data-dir /path/to/private-data` and use that option for both commands. Do not copy normal SSH keys or profiles into a shared cache. Status, diagnostics, restore and removal do not download Python automatically. Retain runtime slots referenced by installed updaters or recovery. See [Python details](../OPTIONAL-PYTHON.md).

## Install and select a language

- **Windows x64:** Download `cytv-windows-x64-desktop.zip`, choose **Extract All** in File Explorer, then open `cytv-desktop/cytv-desktop.exe`. Keep the `_internal` folder beside it. Windows publisher signing is not configured. The separate console is `cytv-windows-x64.exe`; rename it to `cytv.exe` and use `.\cytv.exe` in PowerShell for the commands below.
- **macOS 13+:** extract `cytv-macos-arm64.zip` (Apple Silicon) or `cytv-macos-x64.zip` (Intel), move `cytv.app` into Applications and open it. Allow Local Network access. If blocked, use Privacy & Security → Open Anyway only for a trusted project download; do not disable Gatekeeper. Older-system acceptance is not established.
- **Linux x64:** on Ubuntu 22.04+, Debian 12+ or Mint 21+, open `cytv-linux-x64.deb` in the graphical package installer, install, then open Clean Your TV from the applications menu. Desktop libraries may require Internet access. Linux ARM is not included. The standalone `cytv-linux-x64` executable is the CLI; use the `.deb` for the graphical app.

[Android installer](../../android/README.md): all ten interface languages are available. The top-right control shows the current language; tap it to choose another. Your selection is saved on the phone.

Android status and recovery keep the selected action visible during connection and show its own progress. Text uses the phone’s system font with larger labels and help text.

The desktop wizard selects your system language automatically; its language selector saves an explicit choice. On the TV, open **Settings → Language** and select a language, or the system/automatic option to follow the TV language. Installer and TV preferences are separate. The supported codes are listed in the [language index](../LANGUAGES.md).

For a separately downloaded CLI on macOS/Linux, open a terminal in its extracted directory:

```sh
chmod +x cytv
./cytv --language en install
```

Choose the TV (or enter its IP), choose the edition and review the summary. Approve first-use SSH trust only for your own TV on a trusted network; a changed saved key blocks access. Root credentials are distinct from the Developer Mode passphrase. Root installs recovery and activates Home immediately, without a trial or Keep step. Check arrows, OK, Home, Back/Cancel, volume, standby/wake and cold boot on your own TV.

If Root removal is interrupted, choose Remove again in the app. It checks the retained TV journal and package state before continuing; completed removal is not submitted again. If the previous operation is still running, wait a minute. If its outcome cannot be verified, restart the TV and check again; retain the diagnostic report for support.

## Everyday use and recovery

Arrows select tiles; OK opens them; hold OK to reorder. Short Back retains the app's navigation and exit confirmation. Short Home opens Clean Your TV while Home control is active. In new builds, hold Back for 1.2 seconds to open LG Home once. The Home-control switch and your settings remain unchanged.

**New builds: press Home three times within two seconds**, releasing between presses, to return to LG Home and stop Home control. This preserves preferences. Older No-root Helper versions through 0.6.13 instead use holding Home for about two seconds; holding Home is not the Root emergency gesture.

No-root: open **Home Helper** from LG Apps to resume; opening Home alone does not clear the stop. Root: turn **Change Home** on in Home settings to resume. **Open LG Home** opens LG Home once without changing routing. To restore LG Home as the persistent destination, turn **Change Home** off or run `cytv restore`. Do not run both controllers together. If a failure repeats, leave LG Home active.

```sh
./cytv --language en status
./cytv --language en doctor --report
./cytv --language en restore
./cytv --language en uninstall
```

After interruption, run `status` before retrying; retain journals and recovery files. `restore` returns LG Home without removing apps. `uninstall` restores before removal. Root recovery state is deliberately retained; never delete it to force reinstallation. Review diagnostic reports before sharing; do not publish keys or profile folders.

## Updates and removal

Keep known-working packages and private settings backups. For computer-assisted No-root package replacement, stop Helper first and update without uninstalling, which may erase settings. Removing the desktop app does not remove TV apps. Do not replace a live Root runtime with a standalone IPK; use cytv's explicit recovery/reinstallation flow.

In v1.1.0, **Update all** in Home Settings → Software updates uses a signed release set: Home, Helper and Home Updater for No-root on a rooted TV; Root Home, Root Updater and the routing/recovery runtime for Root. This requires root, Homebrew Channel, working webOS installer services, Python 3.9+ and Node.js 8+. An unrooted TV still uses the computer installer.

For a fresh setup, use the complete stable installer to install the matching transition Home and edition-specific recovery Updater. **An existing Root installation with a retained Root Updater may deliberately block generic reinstallation.** First inspect `status`, Recovery and the existing transaction through the matching legacy recovery flow; follow the [existing-TV checkpoint](../UPDATES.md#one-time-computer-preparation). Do not delete journals or bypass this check. A legacy Home-only OTA does not install the new infrastructure.

Only after the installed components and recovery state are ready, enable **updates for all TV components** in the desktop installer. For a saved root SSH connection and the Root edition:

```sh
./cytv --language en enable-system-updates --edition root --host TV_ADDRESS
```

This separate action provisions the fixed supervisor and captures the installed component set as a rollback baseline. It requires installed Home metadata with `systemUpdateProtocol = 1`; it does not reinstall Home or change routing. Ordinary No-root edition on a rooted TV needs root SSH and the matching computer-installed components; follow the [bootstrap procedure](../UPDATES.md#one-time-computer-preparation). A legacy Home-only OTA update does **not** provision the new supervisor, Python or updater infrastructure. Once the supervisor is installed, conflicting legacy installers are disabled; do not replace packages around it.

Root 0.2.0, Root Updater 0.2.0 and supervisor 1.0.0 passed controls, triple-Home emergency exit/resume, standby/wake with Emby open for 70 seconds, installed-version menus and friendly feed-unavailable handling on OLED55C3RLA / firmware 43.21.71 / webOS 11.2.0 (`d344d92`, product contents identical to `4b66951`). True cold boot, Helper 0.6.19 on a TV, UK6540PTD and a complete signed system upgrade/rollback remain untested. Stable publication accepts this limited evidence; other models are not validated.

Technical details in English: [desktop setup](../DESKTOP_INSTALL.md), [CLI](../CLI.md), [Installation of both editions](../INSTALL.md), [manual installation](../MANUAL_INSTALL.md), [recovery](../RECOVERY.md), [edition comparison](../EDITIONS.md).

After connecting, cytv reads the installed TV versions and shows current → bundled version for Home and Home Helper (No-root), or Root and Root Updater. Review and confirm before installation. First installs, reinstalls and downgrades are labeled separately; `--yes` skips confirmation but still prints the versions.

Software updates shows release details only for the installed version or newer. Open Recovery to see the saved rollback version or why rollback is unavailable; Back returns to updates.

No-root checks the TV shell ABI, so a 64-bit kernel with verified ARM32 userspace is accepted. If verification fails, attach the generated diagnostic JSON; do not share keys or passphrases.

Home updates require confirmation before installation; startup verification is automatic afterward. Background status refresh keeps the selected remote-control button in place.

Startup health is checked automatically in both editions; no manual health-confirmation step is required. Legacy Home-only rollback restores the previous Home package and its saved profile; System Updater rollback restores the complete previous release set. Recovery remains available after confirmation, without a time limit, until the next update. Later settings changes may be lost; rollback asks for confirmation. On-TV No-root updates and rollback still need root and Homebrew Channel. After an interruption, run `status` and inspect Recovery before continuing. An uncertain installer outcome blocks reinstallation and rollback: retain logs, journals and runtime slots, and never delete state to force a retry. Resume an interrupted cytv operation only through its checked recovery flow.

The update screen now separates versions, status and readable release notes. Up/Down reads the notes; Left/Right selects the fixed actions below. After automatic startup checks, Root restores previously enabled Home control; No-root preserves the separate Helper state. Disabled preferences and explicit or emergency off remain off.

Opening Home settings checks for updates in the background. An orange dot on Software updates means a newer version is available, including releases that require computer setup. Settings stay usable during the check.

No-root: open Home settings → Developer Mode for auto-renewal, session checks and diagnostics. The main screen keeps a brief status and any renewal errors visible. Back returns to Home settings. Both editions place Language, Software updates and TV settings in the same row; an arrow opens each item.

Opening Home Helper shows its purpose and current state. Starting a stopped Helper requires confirmation. Home Updater and Root Updater explain recovery; regular updates are in Home settings. Restore is shown only when a saved version is available and asks for confirmation before replacing Home and its settings.

If Root shows `Denied methods call status` immediately after supervisor bootstrap, close and reopen Home Root once, then check updates again. If it persists, retain diagnostics and recovery state.

1.2.0 (#51): after a TV package rejection, the diagnostic JSON retains only the operation category, bounded numeric error/status codes, an allowlisted package state and a boolean result. It excludes raw TV error text, paths and app IDs. Review the report before sharing; installation is not automatically retried, and the UN70006LA installation failure is not yet confirmed fixed.

1.2.0 (#59): if Helper status cannot be checked, **Start Helper** remains available with confirmation. Opening the tile does not restart Helper or clear an emergency stop. Home button settings require a responding controller.

1.2.0 (#55): Root validates migration data before installing. Interrupted cleanup before provisioning can remove the package without a nonexistent LS2 snapshot, retaining a verified receipt for the normal cytv archive/reinstall flow. Later missing snapshots or conflicting evidence still stop cleanup. These changes require the new driver; the OLED Flex recovery-service startup failure remains unresolved.

## LG firmware blocking in 1.2.0

Root only: Home settings → LG firmware updates changes the existing Homebrew Channel preference. This includes firmware security updates; Clean Your TV updates remain separate. A real TV restart is needed in both directions; standby is not enough. The switch shows the saved preference, not verified active blocking. Some TVs check before blocking starts, so prompts may remain and router blocking may be needed. Homebrew keeps the preference after CYTV removal or rollback. If unavailable or unconfirmed, check Homebrew and refresh status. See the acceptance record for the scope of TV checks.

[LG firmware blocking](../LG-FIRMWARE-UPDATES.md) · [1.2.0](../RELEASE-1.2.0-ACCEPTANCE.md)
