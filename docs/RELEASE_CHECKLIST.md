# Release checks

- Complete the [candidate documentation pass](RELEASE-FLOW.md#update-documentation-for-every-candidate)
  before marking the release PR ready; repeat after scope or version changes.
- Update affected usage, installation, update/removal, troubleshooting and
  recovery guides, including translations, commands, links and versions.
- Record reviewed/updated files, checks and remaining documentation limitations
  in the release PR. Release notes alone do not complete this check.
- Run scripts/test.sh and scripts/build.sh.
- Build from a clean inventory; inspect package contents for credentials and state.
- Preserve licenses and upstream attribution.
- Mark hardware-tested and untested paths explicitly.
- Keep a rollback package locally.
- Publish checksums with artifacts.
- Never upload firmware, SSH/SSAP keys, live device backups or raw personal logs.

## Root Edition gate

- Keep development-only tools out of production IPKs.
- Source integration as Root Preview does not certify a stable binary release.
- Do not publish a stable Root Edition installer until the hardware gates in
  [Root Edition testing](../root-edition/TESTING.md) pass.
- Verify exact metadata, registration cache, both profiles and SAM Home rollback.
- Document native-button emergency behavior separately from No-root controls.
- Never present a diagnostic-app result as a production-launcher result.
