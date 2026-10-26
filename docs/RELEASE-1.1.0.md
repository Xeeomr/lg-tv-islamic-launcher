# v1.1.0 — system updates and automatic Root Python

Stable 1.1.0 adds whole-edition system updates and optional Python delivery for
Root. The maintainer authorized publication with limited physical-TV evidence;
see the [device checks and accepted remaining risks](RELEASE-1.1.0-ACCEPTANCE.md).
Download the final packages from the [1.1.0 release](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/tag/v1.1.0).

| Component | Previous release | Candidate |
| --- | --- | --- |
| cytv installer | 0.2.16 | 0.3.0 |
| Home | 1.3.8 | 1.4.0 |
| Home Helper | 0.6.18 | 0.6.19 |
| Root Edition | 0.1.12 | 0.2.0 |
| Home Updater | 0.1.6 | 0.2.0 |
| Root Updater | 0.1.1 | 0.2.0 |
| Android installer | 0.1.7-preview / code 8 | 0.2.0-preview / code 9 |
| New fixed System Updater supervisor | Not shipped | 1.0.0 / protocol 1 |

## Included changes

- Compile No-root Helper app/service JS for TV Node 0.12.2+ with Babel,
  core-js and safe-buffer. Select a compatible WebSocket implementation on old
  TV runtimes and preserve controller errors when logging fails (#47, #54).
  Input-device, standby and cold-boot acceptance on the reported LG 49UJ750V
  remains outstanding. Node 8.12.0 also passes the runtime regression for #54;
  confirmation on LG OLED55C11LB (C1) / firmware 03.53.45 remains pending.
- Update compatible TV edition components through a signed release set with an
  independent supervisor, preserved profile and explicit rollback. Computer
  setup provisions the supervisor and captures existing recovery baselines;
  uncertain operations, conflicting legacy installers and downgrades are refused.
- Root setup automatically supplies a verified private ARMv7 Python when the TV
  has no suitable Python 3.9+. Working system interpreters skip the download.
  Desktop and Android installers do not contain the additional runtime archive.
  The optional download is about 26.3 MB, normalized SSH transfer about 51.5 MB
  and installed regular files about 119.3 MB. Staging requires additional free
  space. No system Python, system libc or global PATH changes are made.
- Persist and validate interpreter bindings for Root, watchdogs, boot recovery,
  independent updaters and interrupted removal. Verify executable bytes before
  running retained interpreters. Keep runtime slots needed by recovery/rollback.
  `cytv --prepare-python-runtime` prepares a verified offline cache without a TV.
- Identify individual Root requirement failures and record safe numeric SSH
  command exit statuses in diagnostic JSON without credentials or raw output.
- Correct deterministic IPK archive metadata, protected installation staging,
  older-TV Node URL/HTTPS compatibility and certificate trust for updater and
  renewal services. Preserve unresolved installation/recovery evidence.
- Fix Android operation receipt creation on filesystems that reject hard links.
- Accept macOS packaged-payload aliases during supervisor setup without weakening
  inner-file validation. Avoid reopening Root Home after boot readiness over an
  app the user already launched; initial presentation remains native to webOS.
- Maintain subsequent release candidates after verified publication and preserve
  release scope/notification provenance.
- Keep installed versions and understandable update/recovery messages visible
  when a feed is unavailable, without exposing internal commands (#53).
- Resume interrupted supervisor removal without corrupting verified ownership
  of the downstream Root Updater registration (#56).

Related implementation/preparation PRs: #36, #38, #39, #40, #42, #43, #44, #45,
#46, #48, #49, #50, #52, #53, #56 and #57; the Helper runtime correction relates to issues #47 and #54.
Integrated PRs are recorded in release-plan.json. Issue #37 remains open for
UK6540PTD device feedback; issue #24's original unfinished removal is not claimed
resolved by its separate Android receipt fix.

## Device feedback and limits

The issue #37 TV is **LG UK6540PTD, firmware 05.50.70, ARM32**, not LG C3.
The reporter confirmed Python 2.7.12 and no available Python 3. The new managed
runtime has not been tested on that TV. ARM32 QEMU startup and automated tests
do not establish compatibility with its loader, libc, webOS APIs, remote input,
cold boot or rollback.

Root and on-TV system updates still require their other platform prerequisites,
including appropriate root services and TV Node.js. Supplying Python does not
replace those requirements. Unrooted TVs use the computer installer. Existing
Root/updater infrastructure transitions require computer-assisted setup; this
release does not promise that a legacy app-only OTA update installs new runtime
or supervisor infrastructure.

Root 0.2.0 with both updater layers was exercised on an OLED55C3RLA with firmware
43.21.71: Home/navigation, app launch, Home/Back, volume/mute, emergency exit,
manual resume, standby/wake and update/recovery screens. Full removal needed
supervised recovery before the corrected resumption and fresh installation
completed. Restart Home once if an already-running GUI retains an LS2 denial
immediately after supervisor setup.

True cold boot, physical Helper 0.6.19, signed whole-edition upgrade/rollback and
actual Android installation remain unverified. The exact new Helper and previous
Home rollback are hash-pinned; its approval explicitly records the maintainer's
decision to ship with automated evidence and outstanding physical checks.

## Packages and provenance

Use final release assets instead of earlier Actions test installers: those
earlier builds predate later corrections. Android remains labelled preview.
The final release includes BUILD-INFO.json, RELEASE-INVENTORY.json and SHA256SUMS;
publication verifies exact-source desktop/Android packages and signs the update
feeds. The [documentation audit](DOCUMENTATION-AUDIT.md) records guide and
translation coverage separately from hardware evidence.
