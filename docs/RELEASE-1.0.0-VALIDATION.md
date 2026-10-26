# 1.0.0 bounded release validation

Date: 2026-10-24. Source baseline: c17313dc97f00641b6c3ff17d19b9ec8cd2c1398,
plus the release metadata/documentation and explicit browser-test locale change.
The final release commit is recorded by CI in `BUILD-INFO.json`.

## Automated checks

- `scripts/test.sh`, using the prepared `.venv-cytv` environment with local socket
  access: passed. Includes 461 Root Python tests, 39 setup tests, 194 cytv tests,
  two preview Python tests, and the JavaScript/native/update checks. A preliminary
  system-Python run lacked dependencies; a sandboxed run denied loopback sockets.
  Neither preliminary run is counted as a pass.
- `python -m unittest discover -s android/tests`: 17 tests passed.
- `python scripts/build-cytv.py --payload-only`: passed; 89 public payload files
  verified by manifest hashes and component versions. Local build used Python
  3.14; CI rebuilds with its pinned Python 3.12 environment.
- Chrome browser checks passed: `tests/apps/ui.cjs`, `tests/i18n/browser.cjs`,
  `tests/settings-ui.cjs`, `tests/renewal-ui.cjs`, `android/tests/ui.cjs`,
  `android/tests/localization.cjs`, `android/tests/maintenance.cjs`.
- The app-editing browser test initially waited for English text under a Russian
  browser locale. Setting its locale explicitly to English reproduced and resolved
  the fixture mismatch; no TV application code changed. Separate ten-language
  coverage remains in place for both TV editions and Android.

## Supervised C3 session

Model/firmware: OLED55C3RLA / 43.21.71. Installer: cytv 0.2.14;
Root: 0.1.10. Root IPK SHA-256:
`7d6a65a3bcaf6123f2528f2b686e445c3cc7bdfd2424b2982e499155451be06a`.
This matches the published v0.10.10 Root IPK exactly. Local source bundle manifest
SHA-256: `65f48ff81a96cf79b1fd6ad9ec39c9aa286aba7fd5c2d10325eea6830843105d`.
The installer personalizes the installed application using the private TV inventory;
public release bundles contain no personal inventory.

1. Baseline readback: all three Home destinations selected LG Home.
2. Root installation/reinstallation via the normal cytv flow: passed. Read 30 apps;
   installed and verified Root Updater and recovery, activated Home control and
   launched Home. Existing removed-state recovery data was archived through the
   installer, without deleting the earlier recovery records.
3. User confirmed arrows/OK, application launch, short Home from an application,
   in-app Back and confirmed exit, volume, remote standby/wake followed by controls,
   and triple-short-Home escape all worked normally.
4. After escape, independent readback confirmed SAM Home, defaultApps Home and
   idleApp all selected `com.webos.app.home`; journal restored, intent disabled,
   no active guardian, recovery integrity verified, no pending installer receipt.
5. With the user's explicit approval, cytv uninstalled the project successfully,
   including the new old-process wait. Its final verification reported project
   apps, Root Updater service and startup registration removed, LG Home restored,
   inactive recovery records retained. This checks the fix on a physical TV;
   unrelated TV apps were not targeted.
6. Reinstalled Root through the same cytv flow after removal: passed. The installer
   re-read 30 apps, verified Updater and recovery, activated Home control and opened
   Home. Recovery archives from prior installations were retained.

## Scope

This is one short supervised Root session, not a repeated-cycle, cold-power,
frozen-renderer or interrupted-update test. It does not certify C4/C5, unrooted
Developer Mode renewal, physical Android installation or arbitrary firmware.
Historical evidence remains scoped in the Root acceptance and compatibility
records. No global hardware certification flag is changed. CI's platform builds,
package provenance, signing and feed verification gate actual publication.
