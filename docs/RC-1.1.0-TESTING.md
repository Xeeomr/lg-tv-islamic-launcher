# Historical 1.1.0 release-candidate testing guide

**Superseded by [v1.1.0 stable](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/tag/v1.1.0).** Use the [current installation guide](INSTALL.md), [update guide](UPDATES.md) and [release notes](RELEASE-1.1.0.md). The instructions and Actions run below are a historical candidate record, not the final release download. Later C3 evidence and remaining limits are recorded in [compatibility](COMPATIBILITY.md#current-110-hardware-evidence).

This is an unpublished candidate for device feedback, not the stable release.
Keep the working installer and recovery data. Do not uninstall first or delete
recovery journals to make a blocked setup proceed. Record the exact artifact,
TV model, current firmware/webOS version and installed component versions.

## Get the test installer

[Build 40178512948](https://github.com/Razdva122/clean-your-tv-lg-webos/actions/runs/40178512948)
passed Windows, Linux, both macOS architectures and Android builds at source
`acf1acccb0ec0802c993f94a39080859dcda9591`. Later documentation changes do not
change these installer bytes. GitHub may require sign-in to download Actions
artifacts; they are retained temporarily and are not `releases/latest` assets.
Final release builds must be repeated at the frozen candidate commit.

On macOS, download `cytv-macos-arm64-desktop` for Apple Silicon or
`cytv-macos-x64-desktop` for Intel. Extract the Actions artifact and its enclosed
ZIP, then open `cytv.app`. If macOS blocks a trusted download, use its normal
Privacy & Security → Open Anyway flow; do not disable Gatekeeper. Leave the
working app available while testing the candidate from its extracted directory.

The separate `cytv-macos-arm64` / `cytv-macos-x64` artifact contains the console
executable `cytv`. From its directory:

```sh
chmod +x cytv
./cytv --version
./cytv --check-payload
```

Expect installer **0.3.0** and a successful embedded-payload check without a TV
connection. Bundled versions are Root/Root Updater **0.2.0**, or Home **1.4.0**,
Helper **0.6.19** and Home Updater **0.2.0**. Android is **0.2.0-preview / code 9**.

## First checkpoint: inspect the existing TV

Keep the TV on and on the same trusted network. In the desktop app select the
saved Root connection and run Status, then diagnostics. The console equivalents
below use the saved connection; add `--host TV_ADDRESS --edition root` if needed:

```sh
./cytv --language en status
./cytv --language en doctor --report
```

Review failed requirements and pending transactions before installation. SSH
success does not prove Root prerequisites are satisfied. A missing Node runtime,
denied webOS service, changed SSH key or uncertain recovery state needs resolution.
Retain the diagnostic JSON and review it before sharing.

Existing Root installs with a retained Root Updater may deliberately refuse a
generic reinstall. Do not bypass that check. Inspect the legacy updater's
transaction and recovery status first; an active/uncertain update must be resolved
using its matching recovery flow. A one-time infrastructure transition must be
reviewed against the actual installed state. `--yes` is not approval to replace
Root, and an app-only IPK/legacy OTA does not provision the new runtime or supervisor.

## Second checkpoint: install and check everyday controls

Once the existing installation is clear for the supported setup/reinstallation
flow, use Install interactively and review the displayed version changes and
reinstallation consequences. Reinstallation can reset Root preferences. The
installer should verify recovery, activate Home and open it without a Keep step.

Check these on the remote, recording pass/fail and any LG Home flash:

1. App tiles, saved inventory/icons, arrows, held arrows, OK and app launch.
2. Short Home; in-app Back, Cancel and confirmed exit; volume and mute.
3. Add/hide/reorder an app; return to settings and confirm layout/focus persists.
4. Change Home off/on and Open LG Home once; verify their distinct effects.
5. Three short Home presses within two seconds, releasing between presses:
   LG Home returns and control stays off. Resume explicitly through Change Home.
6. Standby/wake. Test a normal restart next; test cold power only after basic
   controls and recovery pass and while no installation/update is running.

During a supervised startup check, open an ordinary app as soon as Home is
usable and leave it open through the first minute. Boot protection must finish
without reopening Home over that app. Then verify short Home still returns
normally. Record early-start focus separately from later successful app launches.

Record observations per path. One successful launch does not certify cold boot,
all models or every rollback path.

## Third checkpoint: supervisor and recovery

The new Root launcher must advertise `systemUpdateProtocol = 1` before setup.
With its edition-specific Updater installed and its recovery state verified,
choose **Enable updates for all TV components (root required)**, or run:

```sh
./cytv --language en --edition root enable-system-updates
```

This is a separate action from Install. It captures the actual installed baseline
and provisions the fixed supervisor without reinstalling Home. Use
[the update guide](UPDATES.md) for requirements, rooted No-root setup and recovery.
Check the Software updates and Recovery screens, readable notes and remote focus.
Do not expect an unpublished 1.1.0 offer from the stable feed. A complete signed
upgrade/rollback test requires a separately prepared compatible test release set;
do not point the candidate at arbitrary feeds or perform a downgrade to fake one.
Power interruption tests need their own recovery preparation, not the first run.

## What a modern C3 can and cannot establish

A TV with suitable Python 3.9+ should keep that interpreter and skip the optional
download. This checks the fast path. It cannot establish ARMv7 runtime compatibility
on UK6540PTD. Do not rename/delete the TV's system Python to simulate an old TV.
Use a separate verified offline cache to test host acquisition without a TV:

```sh
./cytv --data-dir /path/to/new-private-cache --prepare-python-runtime
```

This downloads about 26.3 MB on the Mac. Provisioning on an eligible old TV would
transfer about 51.5 MB, install about 119.3 MB and require 320 MiB free staging
space. No additional runtime archive is embedded in the normal installer.
See [optional Python and ABI limits](OPTIONAL-PYTHON.md).

## Feedback record

Record the build run/source commit, installer and installed versions, model,
current firmware/webOS, tested steps, failures, untested paths and recovery result.
Attach the generated diagnostic JSON after reviewing it. Do not post SSH keys,
pairing keys, private profile directories or raw device backups. Keep exact
Helper archive/rollback evidence for its separate release approval.

## Node 0.12 Helper feedback — issue #47

The existing test build linked above predates the Helper compatibility fix.
Use rebuilt candidate installers or the newly compiled Helper 0.6.19 package,
not another installation of the older test artifact with the same candidate
version. On LG 49UJ750V / webOS 3.5 / firmware 06.10.65, verify explicit
Start Helper, controller startup and relay READY, short Home, triple-Home
emergency release, unrelated remote keys, standby/wake and a separate cold boot.
Check foreground/app-exit behavior and status/listApps. Retain redacted bootstrap
and controller logs if startup fails; device existence alone does not establish
open/grab permission. Record actual artifact SHA-256 and outcomes. Local Node
0.12.2 and WSS regressions do not establish physical-TV acceptance.
