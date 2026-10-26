# Root Stable 0.1.0

Separate stable distribution for **LG OLED55C3RLA, firmware 43.21.71, Magic Remote**.
Other models and firmware are unvalidated. No-root v0.8.1 remains a separate release.
This designation does not claim that every lifecycle scenario has passed.

## Install and recover

Download the complete Root bundle, extract it, and follow [installation and activation](ROLLOUT.md).
Use `root-edition/doctor.py` for read-only diagnosis and the bundled `setup.py`
for installation, status, restoration and removal.
Do not install the IPK alone: the recovery service, permissions and startup registration
are required. Existing root and verified SSH access are prerequisites; this installer
does not obtain root. Keep the existing launcher and private recovery backups.

The protected trial must be confirmed with **Settings → Keep Root mode**. Exit with
**Settings → Exit Root mode**, or **three short Home presses within two seconds**.
Release the button between presses. The emergency observer runs independently of the
interface. Long Home is not the Root emergency gesture and can trigger LG zoom.
Root exit restores LG routing and disables Root autostart; it does not remove root
or automatically start the No-root helper.

## Verified on the fixed bundle

- System Home and confirmed Back exit to the launcher without observed LG flash,
  including Kinopoisk and VK Video; ordinary Back navigation and Cancel preserved.
- Persistent mode and automatic launch after software reboot.
- Quick standby/resume, arrows, OK, held arrows, volume, pointer and wheel.
- Settings exit, emergency exit and instrumented exit while the renderer was stopped.
- Genuine Homebrew failsafe recovery with normal init.d skipped.
- Clean uninstall/reinstall with original launcher files and five-app profile preserved.
- Independent restoration after a stalled emergency observer, measured at 2.414 seconds.

See the [acceptance record](../docs/development/ROOT-STABLE-ACCEPTANCE.md).

## Known limitations

- Cold-power startup of this exact final bundle has **not** been tested; it was deferred.
  Software reboot and quick standby do not substitute for that test.
- One initial frozen-interface test required a second triple-Home attempt. The cause
  was not established. Later captured gestures and an instrumented frozen-interface
  repeat passed on the first attempt. Do not describe the earlier observation as fixed.
- Early boot black screens are not solved. There is no unattended Root updater.
- Compatibility outside the stated model/firmware is not established.

## Artifact identity and naming

This distribution retains the exact tested runtime and package. The installed name
**Home Root Preview**, ID `com.cleanyourtv.root.preview`, and package version `0.0.1`
are retained for compatibility. The distribution version is **Root Stable 0.1.0**;
these internal names do not mean that a different binary should be installed.

| Artifact | SHA-256 |
| --- | --- |
| `bundle.json` | `cb2495c1e218f1916d89b5fdb11e78f28123068b66ef30481d3b4766010225a2` |
| `com.cleanyourtv.root.preview_0.0.1_all.ipk` | `1036abb125fa74fc20f8f5d18ca694ca4094a0257a6072fc56c22a85061fe261` |

Generic build metadata retains `hardware_validated: false` and
`public_release_ready: false`: the builder does not certify arbitrary builds or
hardware. The model-scoped evidence above applies only to these artifact identities.
All trial timers, health checks, restoration guards and explicit activation remain
unchanged. No TV settings or installed files are changed by publishing this release.
