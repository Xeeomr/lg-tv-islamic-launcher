# System updates implementation plan

> For agentic workers: use subagent-driven-development for the independent work below. Preserve all pre-existing local changes; do not commit unrelated work.

**Goal:** Update Home, Helper, Updater and Root infrastructure from the TV.
**Architecture:** Independent fixed supervisor, signed edition release sets, durable multi-component journal and retained rollback.
**Tech stack:** Existing Python 3.9+, Node.js, Luna, reproducible IPKs and ES5-compatible launcher UI.
**Spec:** docs/superpowers/specs/2026-10-25-system-updates-design.md

## Global constraints

- Root is required for on-TV installation; existing unrooted support stays intact.
- All app identities and infrastructure destinations are fixed by trusted code.
- No replay of an ambiguous installer submission; no concurrent legacy installs.
- Retain complete baseline and profile; preserve emergency-off intent.
- No TV access, publication or changes to stable feeds during development.

## Task 1: Independent supervisor and device adapter

Files: new system-updater/{policy.js,core.py,device.py,cli.py,service.js}; tests under tests/system_updates/.
Produce fixed service com.cleanyourtv.system.updater.service with check({edition}), status({}), install({edition,release,profile}), restoreProfile({edition}), healthy({edition,transaction,version}), rollback({}), reconcile({}). Return result envelopes through Luna.
Feed: signed schema 1, release vX.Y.Z, edition root|no-root, supervisor 1, notes, components array. Each component has name, application, version, url, sha256, size, kind (ipk|infrastructure). Identity names: home=com.gathin.tvhome; helper=com.local.nativehome; updater=com.cleanyourtv.updater; root=com.cleanyourtv.root.preview; root-updater=com.cleanyourtv.root.updater; root-infrastructure has no application and fixed managed destinations. URL asset name is supplied by signed metadata but restricted to this release/repository and a simple basename. Policy exported validate/verify/get like root updater fetch.js. State is /var/lib/clean-your-tv-system-updater. Reuse root updater store, archive and observed installer support by bundled copies/imports.

- [x] Write failing tests for policy identity/signature rejection and durable interruption behavior; run them to confirm failure.
- [x] Implement policy, core, device effects and detached service worker. check returns {edition,release,notes,components:[{name,installed,version}],canInstall,reason}; status returns transaction or null with phase, release, components, error, id, edition. install refetches signed feed and returns promptly after durable reservation. Restore returns {profile,transaction,version,phase} or null. No UI paths/URLs accepted.
- [x] Run policy and Python tests, including rollback, unknown outcome and all packages cached before mutation.

## Task 2: Shared TV interface

Files: launcher/system-updates.js and existing update panels/build includes; tests/system_updates/ui.cjs.
Consume Task 1 RPC API. Export window.SystemUpdates.open({edition,onClose}), rpc(method,payload) returning Promise. Offer versions, notes, Update all, Recovery/rollback and Back; retain arrow-key focus/read behavior. Capture HomeProfile (callback) or RootProfile (Promise) before installing. Poll durable state without stealing focus. Detect supervisor absence and retain old Home-only UI. Standalone apps can inspect/recover; installing requires a launcher profile.

- [x] Write failing runtime UI checks for root/no-root, capture, confirmation, state polling and navigation.
- [x] Implement panel and hooks in existing update panel open functions; include shared asset in ordinary/root build and standalone recovery apps.
- [x] Run affected UI/compatibility tests.

## Task 3: Build, setup and signed release assets

Files: system-updater/{build.py,setup.py}; scripts/build-cytv.py and release preparation/signing; tests/system_updates/test_build.py.
Consume Task 1 files plus bundled copies of root store/package/luna/observed installer support. Build independent IPK, bootstrap bundle and baseline descriptor inventory. Explicit computer setup installs provisioned service, caches exact installed baseline IPKs, owned LS2 permissions and boot reconciliation hook. Seed root and ordinary baselines from computer payloads; skip setup on unrooted ordinary installs with a clear computer-update path. Never replace an unfinished supervisor setup.

- [x] Write failing build/setup tests checking final archives, permissions, inventory and baseline readback.
- [x] Build exact reproducible assets and wire payload/host installer integration. Prepare system feed candidates for both editions from final assets; sign/verify as part of existing release pipeline.
- [x] Run build, release and installer tests.

## Task 4: Profile bootstrap, review and full verification

Files: launcher/profile-bootstrap.js, root-edition/ui/root-profile.js, docs/UPDATES.md, scripts/test.sh.

- [x] Add failing integration tests for independent profile restore and health receipts, maintaining legacy fallback.
- [x] Restore independent snapshot once per transaction/version before rendering; send health only after populated grid matches profile.
- [x] Review tasks against spec and fix gaps; run tests for TV, installer and setup plus compatibility checks.
- [x] Document one-time migration, safe recovery and precise hardware-validation limits.


## Implementation verification (2026-10-25)

Implemented in `codex/system-component-updates`, isolated from parallel work.
Independent review findings were fixed with regression tests: explicit rollback
resume cycles, legacy installer exclusion, transition-before-baseline, complete
Root layout and same-launcher-version rollback restoration. Root infrastructure
also includes its active private service, with verified restart and receipts.

Passed `scripts/test.sh` across TV, setup, installer, Android and preview groups;
the final public installer payload build and hash/version verification passed.
The final preview bridge change passed its Node/Python checks and TV compatibility
lint. Real Chrome checks booted both editions, exercised the shared panel and Back,
confirmed installation is disabled in preview, and found no page errors at 1920x1080.
No TV was modified. Hardware acceptance, including power loss and runtime UID/state
access after installation, remains required before shipping a release.

Integration target authorized by the user: reviewed PR into `release/next`.
The release version and hardware acceptance are deliberately left to candidate freeze.


After integration with the current candidate (including PR #39), the full suite
and public payload build passed again. Bootstrap baselines now record known
missing infrastructure files against the pinned inventory, allowing older Root
Updater installations to upgrade and roll back newly introduced CA files safely.
Independent review approved that migration delta and per-component downgrade
protection. Feature PR: #40, targeting release/next.

The separate compiled legacy-browser gate was also run locally in all three
profiles (modern, missing inset, missing inset/ES2015 APIs). The test bus now
models LS2's explicit missing-supervisor envelope, retaining the production
rule that ambiguous service failures must not activate a legacy installer.
All three profiles passed with an intact grid, navigation and full-screen dialogs.
