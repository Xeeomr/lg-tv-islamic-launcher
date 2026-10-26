# Installer publication plan

Goal: publish Android preview and Windows GUI with reproducible latest download links.

1. Add Android to the trusted main build workflow using the existing preview certificate stored in a repository secret. Validate actual APK package metadata, signer, embedded payload and component versions; bind its report to the source commit and APK hash. Release assembly must require this artifact and the existing Windows GUI validation.
2. Publish v0.10.9 with cytv 0.2.12 and Android 0.1.3-preview, preserving the exact published Helper 0.6.16 baseline; the current changed Root UI requires Root 0.1.9. The concurrently merged webOS 5 network-settings fix requires Home 1.3.5 and the exact published Home 1.3.4 rollback baseline. Commit only this conversation’s installer/brand/docs work; exclude unrelated local documentation images.
3. Replace download-card marks with platform icons and direct latest asset links. Run relevant tests and review, push the authorized release source, wait for trusted native builds and publication, then verify every latest link and downloaded package hash.

Validation: full repository tests, Android bridge/release tests, APK assemble/lint and signer checks, Windows extracted-package smoke checks on Windows CI, release payload verification and signed-feed checks. Android remains a debug-signed preview; no new physical TV acceptance is claimed.
