# Root Settings update and rollback validation

Date: 2026-10-23. Device: LG OLED55C3RLA, firmware 43.21.71,
webOS SDK 11.2.0. Tested implementation:
`7f3f01f3c6e298a1065d6b6b413b45ccab6d6fd8`.

## Scope and isolation

Real IPK installation and downgrade were exercised through Settings → Software
updates on the television. Disposable application IDs were
`com.cleanyourtv.root.updatetest` and `com.cleanyourtv.root.updaterlab`, with separate
services, LS2 permissions, state directories and boot hooks. LG Home routing
remained selected throughout; this run did not activate Root system routing.

Fixtures came from `git archive` of the implementation commit. The lab builder
substituted identities, state paths, hook names, the feed transport and public
verification key. Packages had empty inventories before profile restoration.
The signed feed and IPKs were served over a loopback-only SSH tunnel. An ephemeral
RSA private key remained in the builder process; the production public key was
unchanged and no production private key was used.

Reusable fixture build, without contacting a television:

```sh
python3 scripts/build-root-update-lab.py --output build/root-update-lab
python3 -m unittest discover -s root-edition/tests -p test_update_lab.py
```

The output directory must be new. Setup and device actions remain explicit;
the builder does not install anything. Raw profile captures and device logs are
private local evidence under ignored `build/root-tv-acceptance-2026-10-23/`.

## Successful update

The baseline was version 0.1.0, populated with 30 application entries and five
inputs from the existing packaged profile. Test controls changed columns to four,
preserved hidden applications, hid the two lab applications and reversed visible
tile order (five visible tiles). This gave a distinctive profile to compare.

The Settings UI offered the verified signed 0.1.1 release. Update → Install update
submitted transaction `1c60e75150fb40509ca15edccbc30e51`. The independent worker
installed the actual package, restored the profile and received UI readiness.
The user selected Confirm working update with the physical remote and confirmed
arrows, OK, tile order and application launch worked. The journal reached
`complete`; the restored application reported version 0.1.1.

## Automatic rollback

A second signed release offered 0.1.2. The same Settings controls submitted
transaction `30cf9c0b143c43b4bad5efefc949f6dd`. Version 0.1.2 rendered the restored
profile and reached `verifying`. Confirmation was deliberately withheld.

After the two-minute confirmation deadline, the independent worker recorded
`application health confirmation timed out` and progressed through `rolling-back`,
`verifying-rollback` and `rolled-back`. The journal contains one rollback attempt.
Independent installer evidence matched the prior package, installer client and
application, with terminal `statusValue=30`, `state=installed` and `downgrade=true`.
The restored 0.1.1 UI supplied the separate rollback readiness receipt. No manual
reinstallation or rollback command was used.

Final UI readback reported 0.1.1 and `rolled-back`. The user again confirmed the
physical remote, previous tiles, their order and application launch worked.

## Data comparison

Both post-update and post-rollback captures matched the entire expected normalized
Root profile byte-for-byte under canonical JSON serialization, including
applications, embedded icons, inputs, configuration and tile order. The actual
rendered tile IDs also matched the expected order.

Profile SHA-256:
`8ad1f388d6928882d6c755f71a708c3a7617ee904ed13ca19309ef2bd3f59cfa`.

The candidate packages contained empty inventories, so the populated result came
from profile restoration. All 27 pre-existing developer/cryptofs application
manifest hashes and versions remained unchanged. The ordinary Home source profile
hash remained
`70c02f910bcd0be992e06218dcb1ca1f3f532b2dd90e13175f3d260aa23fcc5f`.
SAM Home, profile Home and idle application destinations remained LG Home.

## Cleanup and local verification

Both disposable applications were removed after the user completed the remote
checks. Removal produced terminal installer evidence. Their recovery activity,
boot hooks, LS2 registrations, scoped recovery permissions and profile override
were removed. Final application inventory exactly matched all 27 original
manifest hashes and versions; ordinary Home profile and LG routing still matched
the baseline. Private root-owned test journals and cached recovery packages were
retained, without active hooks. The temporary HTTP server and SSH tunnel stopped.

Fresh local verification passed all 416 Root Python tests, including three
fixture-builder tests. The fixture tests build actual baseline, candidate,
rollback and updater packages, verify signed offers and isolation, and reject
reuse of an existing output directory.

## Acceptance limits

This validates a real Settings update and one automatic timeout rollback with data
preservation on this device and firmware, under the isolated lab identities.
It does not certify the final production-signed artifact or GitHub transport,
updates starting from active Root routing, reboot/power-loss recovery during an
update, or a terminal installer-failure classifier. The adapter still treats
unclassified installer failures as unknown outcomes and retains recovery state.
See [Root update operation and remaining acceptance checks](../../root-edition/UPDATES.md).
