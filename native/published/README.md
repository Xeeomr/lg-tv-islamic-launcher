# Published Helper baseline

These files preserve specific historical rollback baselines. Published v1.0.3
uses Helper 0.6.18; the unpublished 1.1.0 candidate builds Helper 0.6.19 from
source and needs its own exact archive/rollback approval. Selecting 0.6.19 does
not reuse the 0.6.17 file below. See [candidate notes](../../docs/RELEASE-1.1.0.md).

`com.local.nativehome_0.6.17_arm.ipk` is the exact Helper from
[v1.0.0](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/tag/v1.0.0),
extracted from `clean-your-tv-no-root-1.3.6.zip` after verifying the release's
`SHA256SUMS`. Its SHA-256 is
`165d933c17f1ed24f0ab65986293c7488b0b5d875db5f7b1215e46f24d422f92`.
Both source and installer builders reuse these bytes while version 0.6.17 is
selected. Later Helper entrypoint changes in main are not silently shipped under
that published version; a future native release needs its own version and
reviewed rollback compatibility. v1.0.1 changes the web UI, not the native Helper.

## Historical 0.6.16 baseline

`com.local.nativehome_0.6.16_arm.ipk` is the exact public Helper from
[v0.10.8](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/tag/v0.10.8),
extracted from its digest-verified `clean-your-tv-no-root-1.3.4.zip`.

SHA-256: `ccabf56c814d2aaf35853d95be2aac67614a67b79e223151b93260d58b82f5f1`.

The builder pins this hash and reuses these bytes while the Helper version is
0.6.16. This preserves the signed update/rollback baseline. The published 0.6.17 includes the ownership
repair and icon refresh. The release compatibility record pins the 0.6.16
package and the exact Home 1.3.5 rollback; release preparation verifies that
input executables and the other runtime/protocol files remain unchanged.
