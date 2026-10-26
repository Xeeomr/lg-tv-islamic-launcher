# v0.10.10 — C4 state recovery and clearer maintenance screens

Components: cytv **0.2.13**, Home **1.3.6**, Helper **0.6.17**, Root Preview
**0.1.10**, Android **0.1.4-preview** (version code 5). No-root Updater remains
**0.1.5** because its packaged source has not changed since v0.10.9.

## C4 ownership repair

Helper 0.6.17 fixes the ownership regression reported in PR #2. The helper and
inventory service can use a protected pairing key in a trusted installer-owned
state directory even when directory chmod returns EPERM. A foreign-owned key
whose permissions were expanded at boot is privately staged and atomically
replaced at 0640 while preserving the shared group. Failed staging or replacement
keeps the original file and blocks SSAP if the key cannot be protected.
App-list permission warnings no longer disable foreground or power monitoring.
The key path and contents are retained; a successful replacement changes the
file owner to the runtime doing the repair. Firmware may still expose the key
between boot-time permission changes and helper startup.

Home/Back routing, held-key startup, watchdog and triple-Home emergency release
retain their existing behavior. The full automated suite and real Linux UID/GID
checks cover the repair. C4/C3 hardware validation of this release is pending;
no new cold-boot, standby or physical-TV acceptance is claimed.

## Changes since v0.10.9

Home and Root settings use a more compact layout, with scrolling content and
visible software-update controls. Desktop and console maintenance screens give
clearer installed-component and connection information. Windows text and
controls have improved readability. Android maintenance dialogs distinguish
connection checks from install/reinstall choices and improve localized text and
button readability. The remote-control guide now uses actual Home screens and
shows the routing switch.

## Updating and rollback

Existing No-root installations need the full installer to receive Helper
0.6.17. The Home-only updater does not upgrade the helper and continues to
report a helper upgrade requirement when the installed baseline differs.
Stop the helper with triple Home before manual reconfiguration; the installer
also checks that it is stopped before replacing its files.

The signed Home rollback is the exact Home **1.3.5** IPK from v0.10.9, paired
with Helper 0.6.17. A hash-pinned compatibility record permits only the reviewed
permission module, version metadata and icon changes. Release preparation
checks that every other Helper runtime file, including input executables and
Home-control protocols, matches the published 0.6.16 baseline. Unapproved
Helper transitions or changed rollback bytes still stop publication.

All platform installers, the Android preview, public TV bundles, signed update
feeds and checksums are built and verified by the automatic release pipeline.
Android retains its existing preview signing identity. Root remains subject to
the documented Root Preview limitations and existing hardware evidence.
