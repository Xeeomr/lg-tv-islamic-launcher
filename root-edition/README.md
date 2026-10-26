# Root Edition

**Native Home and Back routing, with an on-TV emergency exit.** Root Edition
uses the same launcher interface as No-root Edition, but registers a separate
application as the system Home. No router script, USB drive or always-on computer
is needed after setup. A computer is needed for installation and recovery tools.

[v1.2.0 stable](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/tag/v1.2.0) includes **Root Edition 0.3.0**, **Root Updater 0.2.1** and **System Updater supervisor 1.0.0**. Latest-download links follow the published release.

Root **0.2.0**, Root Updater **0.2.0** and System Updater supervisor **1.0.0** were checked on **LG OLED55C3RLA / firmware 43.21.71 / webOS 11.2.0**, using `d344d92` (product contents identical to `4b66951`). Arrows, OK, app launch, Home, Back/Cancel/confirmed exit, volume/mute, triple-Home emergency exit and explicit resume passed. Standby/wake with Emby left open for 70 seconds and the installed-version menus passed; an unavailable update feed showed a friendly message. True cold boot, Helper **0.6.19** on a TV, UK6540PTD, and a complete signed system upgrade or rollback remain untested. Stable publication accepts this limited evidence; it does not validate every model or path.

See [current acceptance](../docs/RELEASE-1.2.0-ACCEPTANCE.md). Earlier [0.1.1](ROOT-0.1.1.md) and [0.1.0](ROOT-STABLE-0.1.0.md) records retain their original artifact scope. Keep working installers and recovery backups.

[Install and activate](ROLLOUT.md) · [Compare editions](../docs/EDITIONS.md) ·
[Acceptance](RELEASE-ACCEPTANCE.md) · [Recovery design](RECOVERY.md)

**Since 1.2.0:** Home settings → LG firmware updates controls Homebrew
Channel's existing firmware-blocking preference. Changes need a real TV restart;
the saved switch is not proof of active blocking. This also blocks firmware
security updates, and Homebrew retains the preference after CYTV removal.
See [operation, limitations and TV acceptance scope](../docs/LG-FIRMWARE-UPDATES.md).

## What works on the tested setup

- Short **Home** selects our launcher through system routing, without the old
  interception helper running.
- Confirmed **Back** exit returns to our launcher without an observed LG flash.
  In-app navigation and exit confirmation remain under the application's control.
- Turning **Change Home** on enables permanent intent after automatic input and recovery checks.
- A confirmed normal shutdown retains our Home profile so bootManager selects
  our launcher as its first app on the next startup. Recovery then renews the
  routing transaction after normal-boot and fresh input/guardian checks pass.
- **Three short Home presses within two seconds** request emergency restoration
  independently of the web interface. Release Home between presses; do not hold it.
- Turning **Change Home** off in Home settings restores the original routing.
  **Open LG Home** only visits LG Home once and preserves the routing selection.
- Two independent health checks and recovery state protect the system route.
  Failed startup or a later health failure automatically restores LG Home.

The original launcher, helper and their data are separate. Root exit disables
Root autostart; it does not remove root, uninstall apps or resume the old helper.
To return to No-root, restore first and then explicitly resume Home Helper from
the ordinary launcher. Never run both modes' input handling together.

## Requirements and limits

An already rooted TV, working root SSH access with a verified host key, Python 3.9+
and Node.js 8+ on the TV, Homebrew services and the supported ARM32 Magic Remote input interface
are required. Installation checks fail closed for unexpected state. A doctor
report alone does not establish compatibility.

The computer/Android installer can provision a private, verified ARMv7 Python
when system Python is missing or incompatible. Working system installations do
not download this component. See [automatic Python runtime](../docs/OPTIONAL-PYTHON.md)
for delivery, retained recovery dependencies and unverified older-TV limitations.

The installer does not root your TV, change Developer Mode or flash firmware.
See the [upstream rooting overview](https://www.webosbrew.org/rooting/) separately.
Do not install Developer Mode over an existing root setup for this guide.

The public bundle contains no personal app list. Installation can copy validated
profile data from an existing Home installation without modifying it. It does not
migrate arbitrary browser storage. Root excludes the ordinary Home updater and
Developer Mode renewal UI. Its own **Settings → Software updates** uses an
independent System Updater supervisor after explicit computer bootstrap, with
signed whole-edition release sets, saved profiles and bounded rollback. Startup
health confirmation is automatic. Rollback remains available after confirmation,
without a time limit, until the next update replaces the saved transaction. It
restores the previous package and pre-update settings; the rollback dialog warns
that later settings changes will be lost. After verified startup, previously
enabled Home control resumes automatically through its existing guarded activation
path. Explicit or emergency off during the update wins; disabled preferences,
failsafe and uncertain activation stay off. The runtime and independent updater
must be migrated together from the computer for this behavior. See
[Root updates and one-time setup](UPDATES.md) and the
[isolated update/rollback validation](../docs/development/ROOT-UPDATES-TV-VALIDATION.md). The RC can update compatible Root recovery infrastructure as part of the signed
set; first supervisor/runtime bootstrap and legacy migrations remain computer-assisted.

Early boot black screens, faster boot artwork, system-library patches and
removing system advertisements are **not** delivered by this edition. Long Home
is not its emergency gesture and can invoke LG behavior such as magnification.

For exact evidence and outstanding tests, read [release acceptance](RELEASE-ACCEPTANCE.md).
Historical research is retained in [STATUS.md](STATUS.md); older RC limitations
are not the current usage instructions.
