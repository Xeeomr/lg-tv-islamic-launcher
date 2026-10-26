# v1.2.0 — Helper recovery and Root firmware settings

This release adds confirmed Helper recovery and Root firmware-blocking settings.
Download final packages from the [1.2.0 release](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/tag/v1.2.0)
after verified publication. [PR #58](https://github.com/Razdva122/clean-your-tv-lg-webos/pull/58)
records the build and publication checks; a merge alone does not prove delivery.

| Component | Published 1.1.0 | Candidate 1.2.0 |
| --- | --- | --- |
| cytv installer | 0.3.0 | 0.3.1 |
| Home | 1.4.0 | 1.4.1 |
| Home Helper | 0.6.19 | 0.6.19 (unchanged) |
| Root Edition | 0.2.0 | 0.3.0 |
| Home and Root Updaters | 0.2.0 | 0.2.1 |
| Android installer | 0.2.0-preview / code 9 | 0.2.1-preview / code 10 |
| Fixed System Updater supervisor | 1.0.0 / protocol 1 | Unchanged |

## Changes and delivery limits

- #60 / #59: when firmware denies or cannot provide Helper status, Home offers
  **Start Helper** with confirmation. Opening the tile never restarts Helper or
  clears an emergency stop. Home settings require a responding controller. The
  separate same-package request-file failure is not claimed fixed.
- #61 / #55 (partial): Root validates and retains migration source data before
  installation. Verified removal interrupted before provisioning can finish
  without a snapshot that was never created, preserving proof for guarded
  archival. Conflicting evidence or later missing snapshots still stop cleanup.
  The OLED Flex recovery-service startup/finalize failure remains unresolved.
  Retained older drivers must not be overwritten to retrofit this fix.
- #62 / #51 (diagnostics only): installer reports retain bounded numeric Luna
  error/status codes, a fixed operation category, allowlisted state and boolean
  result. Raw replies, error text, paths and app IDs are excluded. The original
  UN70006LA installation refusal remains unresolved; no automatic retry is added.
- #63: Root settings can read and change Homebrew Channel's LG firmware-blocking
  preference. Writes change only `blockUpdates` and are read back. The saved
  preference does not prove effective network blocking. A real TV restart is
  required; standby may not apply it. Firmware security updates are also blocked.
  Homebrew retains the preference after CYTV removal or rollback. See
  [use and limitations](LG-FIRMWARE-UPDATES.md).

The eARC, Bluetooth and microphone changes in open PR #27 are outside this
candidate. No issue is automatically closed by these partial improvements.

## Installation, updates and rollback

Rebuild desktop and Android embedded payloads, Home/Root bundles and both updater
packages. Root's private recovery-service contract is unchanged; compatible app
updates can deliver the firmware settings UI. The #55 driver/host cleanup changes
require the new matching installer/bundle; an app-only update does not replace
retained recovery code. Preserve unresolved operations and use the documented
[recovery flow](MANUAL_INSTALL.md), without blind retries or manual deletion.

Helper source/version remains unchanged. Verify the rebuilt archive against its
existing exact compatibility pin and compare it with published 1.1.0 bytes.
Keep the published 1.1.0 packages as rollback evidence; package/feed checks must
also verify the Home 1.4.0 rollback baseline. This does not establish physical
whole-edition rollback acceptance.

## Acceptance and provenance

The maintainer reported that checks were normal and directed the release. The
[1.2.0 acceptance record](RELEASE-1.2.0-ACCEPTANCE.md) describes this confirmation
and its limits: OLED55C3RLA / 43.21.71 was confirmed, but the exact tested
revision was not restated.
Historical [1.1.0 evidence](RELEASE-1.1.0-ACCEPTANCE.md) applies to its own build only.
Required candidate checks include Home/Back/navigation/volume, triple-Home and
manual resume, standby separately from restart/cold boot, supported update and
rollback, and the firmware-control matrix in the feature guide.

Original-device feedback is outstanding on OLED48C24LA / 43.21.74 (#59),
OLED Flex 42LX3Q9LA / webOS 11.2.0 (#55) and UN70006LA / 04.64.00 (#51).
Automated checks and successful installation do not certify these devices.
Source commits, build runs and acceptance are recorded in PR #58. Publication
must verify BUILD-INFO.json, RELEASE-INVENTORY.json, SHA256SUMS and signed feeds
before shipping notices or delivered issue statuses are assigned.

The [documentation pass](DOCUMENTATION-AUDIT-1.2.0.md) records candidate guidance
and the publication boundary.
