![Clean Your TV — for LG webOS](assets/brand/readme-logo.png#gh-light-mode-only)
![Clean Your TV — for LG webOS](assets/brand/readme-logo-dark.png#gh-dark-mode-only)

# Clean Your TV — LG webOS

**A clean home screen for LG webOS, with No-root and Root editions.**

Keep your favorite apps in a personal dock and app grid, without sponsored rows
in this launcher. Both editions run on the TV; your computer can be switched off
after setup. One cytv wizard installs either edition.

No-root and Root are equal options for different TV setups. Choose No-root for LG Developer Mode or Root for existing root SSH access. Compatibility and test coverage remain specific to each edition.

- **No-root:** uses LG Developer Mode and an on-TV Home Helper. Keep the session
  active and local networking available for Helper monitoring.
- **Root:** uses existing root access, system Home routing and independent recovery.
  The installer does not obtain root or flash firmware.
- **Home opens your launcher** while Home control is enabled.
- **A way back to LG Home:** press Home three times within two seconds. Older
  No-root Helper versions through 0.6.13 instead use holding Home for two seconds.

Based on [webos-vibehack](https://github.com/OmkarK97/webos-vibehack), with Home-button
handling moved from an external watcher to an on-TV native helper.

[Live preview](https://razdva122.github.io/clean-your-tv-lg-webos/) · [Install](docs/INSTALL.md) · [Recovery](docs/RECOVERY.md) ·
[Compatibility](docs/COMPATIBILITY.md) · [Build](docs/BUILD.md) · [Update & remove](docs/MAINTENANCE.md)

[Manual installation of both editions without cytv](docs/MANUAL_INSTALL.md) — requirements, commands, recovery and reinstallation limits.

## Languages

Installation, use and recovery: [English](docs/i18n/en.md) · [Deutsch](docs/i18n/de.md) · [Español](docs/i18n/es.md) · [Português (Brasil)](docs/i18n/pt-BR.md) · [Français](docs/i18n/fr.md) · [Italiano](docs/i18n/it.md) · [한국어](docs/i18n/ko.md) · [हिन्दी](docs/i18n/hi.md) · [Polski](docs/i18n/pl.md) · [Русский](docs/i18n/ru.md).

The v1.0.1 release selects the system language automatically and saves
an explicit choice in the installer or **Settings → Language** on the TV.
See [language availability and guides](docs/LANGUAGES.md); older release downloads
may predate these features.

## Install with cytv

Choose your platform. Download buttons use GitHub’s `releases/latest/download`
URLs, so they follow the latest published release without a version in the link.

[![Download Windows x64 graphical installer — GUI ZIP](assets/brand/downloads/windows.svg)](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/latest/download/cytv-windows-x64-desktop.zip)
[![Download macOS Apple Silicon graphical installer — ZIP](assets/brand/downloads/macos-arm64.svg)](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/latest/download/cytv-macos-arm64.zip)
[![Download macOS Intel graphical installer — ZIP](assets/brand/downloads/macos-x64.svg)](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/latest/download/cytv-macos-x64.zip)
[![Download Linux x64 graphical installer — DEB](assets/brand/downloads/linux.svg)](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/latest/download/cytv-linux-x64.deb)
[![Download Android ARM64 preview installer — APK](assets/brand/downloads/android.svg)](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/latest/download/cytv-android-arm64.apk)

The buttons above download **[v1.2.0 stable](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/tag/v1.2.0)**. It adds confirmed Helper recovery, Root firmware settings and installer recovery/diagnostic improvements. Hardware evidence remains specific to the tested configuration; see [release notes](docs/RELEASE-1.2.0.md) and [compatibility](docs/COMPATIBILITY.md).

Windows downloads the graphical ZIP: use **Extract All**, then open
`cytv-desktop/cytv-desktop.exe` with its `_internal` folder beside it. Windows
publisher signing is not configured. Android is an ARM64,
debug-signed APK; see [Android preview and requirements](android/README.md).
These downloads do not establish physical-TV compatibility.

One wizard installs either edition. Root activates and opens Home immediately,
without a trial or Keep confirmation.
[All latest release files](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/latest) ·
[Desktop setup](docs/DESKTOP_INSTALL.md) · [CLI guide](docs/CLI.md) · [Release notes](docs/RELEASE-1.2.0.md)

## Choose your edition

| Edition | Status | Start here |
| --- | --- | --- |
| **No-root** | Launcher and helper run on the TV | [Installation](docs/INSTALL.md) |
| **Root Edition** | Root 0.3.0 with persistent activation and Settings updates; version-specific hardware evidence | [Overview and evidence](root-edition/README.md) |

Both use the same Home interface. Root Stable provides native system routing
for Home and confirmed Back exits without an observed LG flash on the tested C3.
It installs separately. True cold boot remains untested for this release; the current C3 check passed triple-Home emergency exit and explicit resume. [Compare requirements, controls and limits](docs/EDITIONS.md).
The features and remote-control guide below describe **No-root Edition**.

![Clean Your TV menu with a five-app dock and Inputs, Wi-Fi and Settings shortcuts](docs/launcher-menu.png)

*Launcher 1.0.11, rendered locally with an example five-app configuration.
Your apps and their order are configured during setup; they are not bundled.*

## What you need

Use a computer or a compatible Android phone for initial installation and maintenance. cytv includes the
runtime and TV packages. **+ / Add app** can refresh the app inventory on the TV.
No-root requires an active Developer Mode session and local networking for Helper
monitoring. Root requires existing root SSH access and recovery services; do not
enable Developer Mode over root. Root needs a suitable TV Python 3.9+ and Node.js
8+ in addition to webOS services. The 1.1.0 installer can supply a verified private
ARMv7 Python on demand when the existing Python is unsuitable. Working system
Python skips that download; ordinary installers do not embed the runtime archive.
See [installation requirements](docs/INSTALL.md) and [optional Python](docs/OPTIONAL-PYTHON.md).

Compatibility varies by model, remote and firmware; see [compatibility and known limits](docs/COMPATIBILITY.md)
before installing. Not affiliated with LG.

## What it does

| Feature | Behavior |
| --- | --- |
| Personal home screen | Local app grid, configurable dock, hidden tiles and tile ordering; no sponsored rows in this launcher |
| Short Home | Native on-TV interception returns to the launcher without passing through LG Home on the tested setup |
| Three short Home presses within two seconds | Stops interception and returns to LG Home |
| Resume interception | Manually open **Home Helper** from LG Apps |
| Wi-Fi shortcut | Opens LG's network setup overlay |
| Automatic startup | Returns after standby and cold boot using input restoration plus a guarded fallback helper; no external device runs the startup logic |
| Exit with Back | Returns after watched apps exit, preserving in-app navigation and exit confirmation; LG Home can briefly flash |
| Quick standby/resume | Avoids relaunching a launcher already restored by webOS, preserving arrows and OK after a fast power cycle |
| Remote controls | Arrows, held arrows, OK, volume and pointer remain usable; wheel events are forwarded |
| Failure recovery | Watchdog cleanup releases interception if the handler stalls; triple Home provides a manual escape |
| Local interface | App tiles, font and splash assets are stored locally; the menu does not wait for an Internet download |

This does not remove system advertisements, uninstall apps, or replace the operating
system's Home destination. It provides an alternative screen. Cold boot still has
an initial black interval; early display timing is under investigation.

## How it works

**Home** is the app launcher. **Home Helper** handles the Home button and watches
for exits from configured apps. Both run on the TV. The helper leaves ordinary
in-app Back navigation, exit confirmations and the other remote controls intact.

![Remote controls: short Home opens our launcher; three short Home presses within two seconds stop the helper; hold Back exits to LG Home; resume via the Home Helper app](docs/remote-controls.png)

*Illustrated controls and example screens; button layout varies by remote.*

**Hold Back exits the app; three short Home presses stop the helper.** When the helper is active,
it returns to our launcher after a watched app exits through LG Home. That path
can briefly show LG Home; it is not the same direct path as short Home.

### Remote control guide

| Button | What it does |
| --- | --- |
| **Arrows / hold an arrow** | Move through tiles and menus; normal navigation inside apps. |
| **OK / pointer click** | Open the selected app or activate a control. |
| **Short Home** | Return directly to our launcher while Home Helper is active. With the helper stopped, LG handles Home normally. |
| **Three short Home presses within two seconds** | Emergency exit: stop the helper and open LG Home. Preferences are kept; this is **not a factory reset**. |
| **Short Back** | Go back inside the current app. Its exit dialog and Cancel action still work normally. On a confirmed exit from a watched app, the helper returns to our launcher. |
| **Hold Back** | Use webOS's exit-to-Home action and stay in LG Home. It **does not stop the helper**; a subsequent short Home opens our launcher. The new hold detection awaits C3/C4 hardware verification. |
| **Volume + / −, mute** | Normal TV/audio controls. |
| **Move the Magic Remote / wheel** | Pointer and wheel events pass through. Wheel-to-tile selection is not implemented in our launcher. |
| **Power** | Normal TV standby/wake. With startup configured and the helper not stopped, our launcher returns automatically; cold boot still takes time. |
| **Hold 1, if assigned** | Open Home using LG Quick Access. This shortcut must be assigned during setup; it does not resume a stopped helper by itself. |

### Resume after an emergency exit

Open **Home Helper** from LG's app list to restart the stopped helper.
Opening Home alone does **not** clear the emergency stop. A single-instance lock
prevents duplicate controllers. Regular Home routing is controlled by the
**Change Home** switch in Home settings; there is no recovery button in the top menu.
Older packages may call the helper **Native Home Prototype**.

The long-Back action is documented by [LG's remote guide](https://webostv.developer.lge.com/develop/guides/magic-remote);
app-specific exit behavior can vary. See [Recovery](docs/RECOVERY.md) for troubleshooting.

## Get started

Start with the [shared installation guide](docs/INSTALL.md) for No-root or Root.
cytv includes TV discovery, saved profiles, diagnostics, recovery and the required
packages. macOS uses `cytv.app`; Linux uses the graphical `cytv-linux-x64.deb`
package. Windows uses `cytv-windows-x64-desktop.zip`: extract
all files and open `cytv-desktop/cytv-desktop.exe` with `_internal` beside it.
The separate `cytv-windows-x64.exe` download is the console wizard. See [desktop setup](docs/DESKTOP_INSTALL.md).
The [Android preview](android/README.md) includes all ten desktop languages. Its top-right control shows the current language and opens a saved language picker.
Real-TV acceptance remains model- and build-specific.

### No-root source installation

On the TV, enable **Developer Mode** and **Key Server**. On a Mac or Linux computer
with **Node.js 20+ (including npm), Python 3.9+ and Git**, run:

```sh
git clone https://github.com/Razdva122/clean-your-tv-lg-webos.git
cd clean-your-tv-lg-webos
./install.sh 192.168.1.50
```

Replace the address with your TV's IP. The script prepares local tools, pairs with
the TV, reads your apps, builds and installs both packages, configures Home Helper
and requests its launch. Enter the Developer Mode passphrase when prompted and
accept the remote-control pairing request on the TV. No manual helper build or
configuration is needed. No root or `sudo` is used.

Once installed, check short Home, press Home three times within two seconds to test recovery, and
check standby/wake and cold boot. **Hardware compatibility still needs to be
verified on your TV.** See the [installation guide](docs/INSTALL.md) for prerequisites,
manual installation and recovery. This Bash source workflow has not been validated
on Windows/WSL; the native Windows cytv console is a separate download.

## Browser preview

[Try the live launcher preview](https://razdva122.github.io/clean-your-tv-lg-webos/).
Switch between **No-root Edition** and **Root Edition** in the top bar. Both use
demo apps and simulated TV functions; Root mode activation and exit
only change the browser simulation. [Open Root Edition directly](https://razdva122.github.io/clean-your-tv-lg-webos/#root).
GitHub Pages automatically deploys
the latest `main` after tests pass.

### Run locally

Preview the actual launcher without a TV or extra dependencies (Python 3.9+):

```sh
python3 scripts/preview.py --open
```

Open http://127.0.0.1:8765/ if the browser does not open automatically. The
1920×1080 TV canvas scales to fit the window. Use the mouse, arrow keys and
Enter; hold Enter to rearrange a tile, and use Esc to go back in panels.
The preview uses ten demo apps with scalable SVG brand logos and simulated webOS
services. It never connects to a TV or performs real launches, renewals or updates.

Save changes in `launcher/` or `preview/` and the page reloads automatically
within about a second. The server reads sources on each request and disables
caching. Tile order is saved in the
browser's local storage. Stop with Ctrl+C; use `--port 8766` if the port is busy.
Only launcher assets and preview files are served, on the loopback interface.
The preview adapter is injected by the server and is not included in TV packages.
Logo sources are recorded in `preview/icons/SOURCES.txt`.

## Developer Mode auto-renewal — Beta

No-root Home includes **Home settings → Developer Mode auto-renewal (Beta) →
Turn on auto-renewal**. It is off by default and aims to renew the session on the
TV. **Real renewal on unrooted TVs remains unverified: monitor the official timer.**
See [setup, status and feedback](docs/DEVELOPER-MODE-BETA.md).

## Current components and hardware evidence

The **v1.2.0 stable** distribution contains cytv **0.3.1**, Home **1.4.1**, Helper **0.6.19**, Root **0.3.0**, both edition Updaters **0.2.1**, Android **0.2.1-preview / code 10**, and System Updater **1.0.0 / protocol 1**. Component versions are recorded in `release-versions.json`; see [release notes](docs/RELEASE-1.2.0.md).

Root **0.2.0**, Root Updater **0.2.0** and System Updater supervisor **1.0.0** were checked on **LG OLED55C3RLA / firmware 43.21.71 / webOS 11.2.0**, using `d344d92` (product contents identical to `4b66951`). Arrows, OK, app launch, Home, Back/Cancel/confirmed exit, volume/mute, triple-Home emergency exit and explicit resume passed. Standby/wake with Emby left open for 70 seconds and the installed-version menus passed; an unavailable update feed showed a friendly message. True cold boot, Helper **0.6.19** on a TV, UK6540PTD, and a complete signed system upgrade or rollback remain untested. Stable publication accepts this limited evidence; it does not validate every model or path.

The [1.2.0 acceptance record](docs/RELEASE-1.2.0-ACCEPTANCE.md) records the maintainer's confirmation on OLED55C3RLA / 43.21.71 and its limits. Earlier hardware reports retain their original artifact scope. C5/webOS 26 Helper startup remains under investigation. See [compatibility](docs/COMPATIBILITY.md), [Root acceptance](root-edition/RELEASE-ACCEPTANCE.md) and [installation checks](docs/INSTALL.md#5-verify-before-daily-use).

## Project layout

```text
launcher/          Web launcher and local splash image
native/app/        Home controller, policies and native entry point
native/prototype/  Remote relay/filter source and tests
native/service/    Guarded startup service
scripts/           Build and setup tools
docs/              Installation, edition comparison, recovery and limitations
root-edition/      Root package, installer, recovery runtime, updater and validation
cytv/              Shared desktop/console installer and saved TV connections
```

## Credits

Built on the work of [OmkarK97/webos-vibehack](https://github.com/OmkarK97/webos-vibehack)
and [Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv).
MIT-licensed project code; Outfit uses SIL OFL and the bundled ws library uses MIT.
See [LICENSE](LICENSE) and [third-party notices](THIRD_PARTY_NOTICES.md).

No firmware images, extracted proprietary binaries, TV credentials or personal
app inventories are included. Please redact logs before opening an issue.

## Software updates

The 1.1.0 release introduces **Update all** in **Settings → Software updates**
for rooted TVs with Homebrew Channel and a separately provisioned System Updater.
Its signed release set updates Home/Helper/Home Updater for No-root edition on a
rooted TV, or Root Home/runtime/Root Updater for Root edition. Initial installation
and supervisor setup require the computer installer; installing a launcher IPK or
using legacy Home-only OTA does not install that infrastructure. Unrooted TVs
continue updating from their computer. Updates preserve the profile and retain a
verified previous component set for recovery; explicit emergency stops stay off.
See [setup and recovery](docs/UPDATES.md). Complete signed system upgrade and rollback acceptance remains pending.
