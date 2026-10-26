# 1.1.0 release decision and device evidence

On 2026-10-25 the maintainer explicitly selected a stable 1.1.0 release after
being told that Helper 0.6.19 and its rollback had not been tested on hardware.
This is acceptance of the remaining release risk, not certification of the
untested paths. Automated tests, exact-source builds, package hashes, signed
feeds and normal protected-branch publication remain required.

## Root device checks

Device: LG OLED55C3RLA, firmware 43.21.71, webOS SDK 11.2.0, ARM64,
system Python 3.12.6 and Node 20.12.2. Installation used macOS ARM64.
The final local installer contained product source `d344d92721ce6f5e8d07719b5c122758eb2c96a9`,
merged without product changes in `4b66951dcea4232a61d2b48a7a79c3dc02ba9056`.
It installed Root 0.2.0, Root Updater 0.2.0 and System Updater 1.0.0/protocol 1.

The operator confirmed these remote-control checks:

- Home app list, arrows, OK, app launch and short Home returning from an app.
- In-app Back, cancelled and confirmed exit, volume and mute.
- Triple-Home emergency exit, retained LG Home routing and manual resumption.
- Standby/wake, early Emby launch remaining open for at least 70 seconds and
  short Home returning afterward. Kernel uptime did not reset: this is not a
  cold-boot test.
- Update and recovery screens show installed versions and understandable
  messages after closing and reopening Home. A freshly bootstrapped LS2 policy
  initially left the already-running GUI with a denied status call; restarting
  the GUI cleared it.

Computer-side checks confirmed fresh supervisor setup and a non-installable
`feed-unavailable` offer while the public stable release was still 1.0.3 without
system release assets. That expected prepublication response does not validate
the forthcoming signed 1.1.0 upgrade or rollback.

Migration from Root 0.1.11 and Root Updater 0.1.0, full removal and reinstallation
were exercised. One removal needed supervised completion of the idempotent
Root provision rollback after a failed RPC. PR #56 repaired verified downstream
registration restoration on removal resumption; the retained private interrupted
state passed offline validation and the live removal then completed. This is
supervised recovery evidence, not an unattended-success claim. Raw logs and TV
credentials remain private.

The TV retained its working system Python; no optional runtime was downloaded.

## Helper transition and remaining limits

`native/helper-rollback-compatibility.json` pins the exact new Helper archive,
previous Helper 0.6.18 and published Home 1.3.8 rollback package. Previous
packages were checked against v1.0.3 checksums. Automated Helper compatibility,
controller and service regressions provide software evidence, including old
Node runtime checks. The maintainer accepts the remaining physical validation
risk for this specific pinned transition. No physical Helper 0.6.19 or Home
1.4.0-to-1.3.8 rollback test was performed.

Outstanding physical checks include true cold boot; signed whole-edition
upgrade/rollback; new Helper input grab, emergency release and standby; actual
Android installation; and managed Python on the UK6540PTD/05.50.70 from #37.
ARM32 QEMU results do not establish compatibility with that TV. Issues #37,
#47 and #54 remain subject to original-device feedback. Historical evidence for
other builds/models does not certify these new artifacts.

Use the release's BUILD-INFO.json and RELEASE-INVENTORY.json for final source and
build provenance. Platform packaging after these checks does not expand the
hardware evidence recorded here.
