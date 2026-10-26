# v1.0.2 — Unpublished candidate, superseded by v1.0.3

Never published. Signing rejected changed Root shared UI under version 0.1.11.
Use [v1.0.3](RELEASE-1.0.3.md), which correctly increments Root to 0.1.12.
The operator confirmed successful RC checks and authorized release on 2026-10-25.

## Components

- cytv 0.2.16
- Home 1.3.8
- Home Helper 0.6.18, built from source (the immutable 0.6.17 baseline is retained)
- Android 0.1.7-preview, versionCode 8
- Root 0.1.11 and independent No-root Updater 0.1.6, unchanged

## Changes

- #25/#26: preserve tile visibility and selection when returning Home, fix focused
  tile layering, open AirPlay with a bounded fallback, and refresh app inventory
  without interrupting navigation or editing.
- #29: load Helper permissions inside the service sandbox, retry monitoring after
  transient unsafe permissions without reading the pairing key, and recover late
  LG Home takeover within the existing retry limits. Back cancels recovery.
- #31 (#12): add opt-in, one-minute Home-button diagnostics and single JSON export
  to the desktop and Android installers. Reports correlate input, launch replies
  and foreground observations, label cached/unavailable data, and omit keys,
  addresses and raw logs. This collects evidence; it does not confirm a C5 fix.
- #32 (#22–24): distinguish safe Key Server failure categories and offer explicit,
  default-No recovery of verified unfinished No-root removal. Declined or failed
  recovery preserves the journal. An unlock error does not prove a wrong key.
- #33 (#21): check real Helper/controller/relay process identity before replacement,
  distinguish stale PID files, and make installer errors and their causes visible
  in desktop, Android and supported terminals. Uncertain/live state blocks setup.

## Updating after publication

Download the v1.0.2 installer for your platform from the verified release. On an
unrooted TV, keep Developer Mode active and the TV awake, stop the existing Helper
with three short Home presses, then use the No-root setup flow to install Home
1.3.8 and Helper 0.6.18. Review the displayed versions before confirming. Do not
select No-root or enable Developer Mode on an existing rooted installation.

Home-only OTA cannot replace the Helper. Existing Helper 0.6.17 users need the
full installer to receive recovery and diagnostic changes. Root TV components
remain unchanged; no Root runtime upgrade is part of this release.

After the actual package's diagnostic export is verified on a TV, use
[Home button diagnostics](HELPER-DIAGNOSTICS.md) to collect one report. Launch
acknowledgements alone do not prove the visible foreground app.

## Validation and release gates

Historical #29 hardware evidence covers equivalent corrections applied to Helper
0.6.17 on SDK 7.5.9 / firmware 04.56.75. It does not validate the complete source
package 0.6.18. The combined candidate, Android native save picker, AirPlay,
standby/startup and Home 1.3.8 → 1.3.7 rollback with Helper 0.6.18 are covered by the operator's confirmation of successful requested checks on 2026-10-25. Device details and
tested artifact hashes were not supplied; this is operator-reported acceptance,
not an independently observed hardware run. C5/webOS 26 and the reporting NANO81 devices remain unverified.

The signed-feed gate now accepts an explicitly tested runtime transition only
when the exact decompressed Helper archive (all contents and metadata), previous
Helper bytes and published Home rollback bytes match the committed approval.
Compression headers are ignored to support Python gzip implementations across
build hosts. The older permission-only transition check remains in place.
The approval records the operator's acceptance and its limits; any changed
runtime, installation control or baseline stops publication.

Local TV JS/C/compiler checks, 461 Root, 62 setup, 225 installer, 19 Android and
2 preview Python tests passed, along with preview bridge and 10 release-feed tests.
The public TV payload built and verified successfully. An independent release-code
review found no blocking issues. Trusted builds for all five platforms and
Linux/macOS checks must pass on the exact finalized candidate.
Do not treat source tests as artifact or physical-TV acceptance.

## Notifications

After successful publication and signed-feed verification, notify release PR #30,
implementation PRs #25/#26/#29/#31/#32/#33 and issues #12/#21/#22/#23/#24 using the
checksummed release inventory. Keep unresolved issues open. Send the guided #12
reply only after verifying real diagnostic export; describe #21–24 as partial
recovery/diagnostic improvements without claiming the original symptoms fixed.
