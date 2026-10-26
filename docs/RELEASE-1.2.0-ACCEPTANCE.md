# 1.2.0 maintainer confirmation and evidence limits

On 2026-10-25 the maintainer requested a release from candidate PR #58. After
being asked about Home/Back, triple-Home, standby/restart, rollback and the new
firmware-blocking setting, the maintainer replied: “I checked; everything is
normal.” This records the operator's overall confirmation and decision to
continue the release. It is not a detailed per-stage test log.

The maintainer separately confirmed the same LG OLED55C3RLA / firmware 43.21.71
as in the earlier record. The tested installer/source revision was not restated;
do not claim that final platform installers have already been tested. The earlier
[1.1.0 acceptance](RELEASE-1.1.0-ACCEPTANCE.md) remains historical evidence for its
own build. No additional per-stage timing or failure-injection log was supplied.

## Automated and rollback evidence

Product versions were prepared at `b822fe4e313eecd673808d467a86d3eaf45fc0d7`.
Complete local `scripts/test.sh` passed: 975 Python tests with two platform skips,
plus JS/C and TV compatibility checks. `scripts/build.sh` and
`scripts/build-cytv.py --payload-only` passed. App/service versions and clean
runtime-state inventories were inspected. Final exact-source CI and publication
provenance are recorded in PR #58 and the release's BUILD-INFO.json.

The published v1.1.0 No-root bundle was retained and checked against SHA256SUMS.
Its Home 1.4.0 rollback IPK has SHA-256
`4692ab0b2a99788a3829a0509e750fc8a47dd6e1b0d7a8efd67e10615e3a40c0`.
The unchanged Helper 0.6.19 archive matches its exact compatibility pin
`641f06d8aa9d850e887b04ac841181e0e073d46626abbc4e254771511c092cb1`.
Local Python 3.14 changes the gzip OS header relative to published Python 3.12;
the decompressed archive and all files match. Release CI uses Python 3.12 and
must retain published Helper bytes with SHA-256
`52510c9115a518a05849f6618516b41886aea54b7f74ea4763ffeeaf63c03e7b`.
These are offline integrity checks, not additional physical rollback results.

## Outstanding original-device evidence

Keep #59 open for the OLED48C24LA / 43.21.74 reporter's confirmation on the
published version. The maintainer's separate check does not certify that model.
Keep #55 open: the OLED Flex recovery-service startup/finalize failure is not
fixed by the pre-provision cleanup improvement. Keep #51 open: sanitized
diagnostics do not fix the UN70006LA installation refusal.

The firmware switch represents Homebrew's saved preference, not proof of active
server blocking. Restart timing, remaining LG prompts, Homebrew ownership after
rollback/removal and other-model compatibility retain the limits documented in
[LG firmware updates](LG-FIRMWARE-UPDATES.md). Do not turn this general operator
confirmation into a claim that every device or failure scenario was certified.
