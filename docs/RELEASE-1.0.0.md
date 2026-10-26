# v1.0.0 — Stable distribution

Clean Your TV 1.0.0 packages the existing No-root and Root editions with the
shared desktop/console installer, signed TV update feeds and rollback packages.
Stability is scoped to documented configurations and checks; this version does
not certify every LG model or firmware.

## Components

- cytv 0.2.14
- Home 1.3.6
- Home Helper 0.6.17
- Root 0.1.10
- No-root Updater 0.1.5
- Android 0.1.5-preview (version code 6)

Home, Helper, Root and No-root Updater retain their v0.10.10 sources and versions.
cytv includes the fix that waits for old Root processes to stop before completing
removal, avoiding a false uninstall failure. Android embeds the updated installer
and keeps its existing preview signing identity.

## Release checks

The release uses a bounded verification session: the complete automated suite,
public TV payload build and hash/version verification, browser interaction and
language checks, plus a short supervised C3 hardware check. CI builds the platform
installers, verifies their embedded packages and Android signer, runs the full
suite on Linux and macOS, and signs/verifies both update feeds before publication.
Actual results and hardware scope are recorded in `RELEASE-1.0.0-VALIDATION.md`.

## Compatibility and retained limitations

- C3 hardware evidence is specific to OLED55C3RLA / firmware 43.21.71 and the
  recorded scenarios. C4 Helper 0.6.17 ownership repair has automated coverage;
  current C4 hardware confirmation is still pending. C5/webOS 26 startup remains
  under investigation and is not a supported configuration.
- A short supervised session does not establish long-term reliability or
  power-loss tolerance. Root direct AC power removal and interrupted production
  updates are not certified by this release. Earlier Root emergency-gesture
  observations remain in the acceptance record; passing a later check does not
  establish their cause or a fix.
- No-root Developer Mode auto-renewal remains opt-in Beta and real renewal on
  unrooted TVs remains unverified. Monitor LG's official session timer.
- Android remains a debug-signed ARM64 preview, separate from the stable desktop/TV
  scope. Physical Android-to-TV installation is not established by browser or
  emulator checks. Windows publisher signing is not configured.
- No-root cold startup can include a black interval, and returning after app exit
  can briefly show LG Home. Local networking and an active Developer Mode session
  remain requirements for No-root.

See [compatibility](COMPATIBILITY.md), [installation](INSTALL.md),
[recovery](RECOVERY.md) and [Root acceptance](../root-edition/RELEASE-ACCEPTANCE.md).
