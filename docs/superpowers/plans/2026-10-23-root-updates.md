# Root Settings Updates Implementation Plan

**Goal:** Install compatible signed Root application updates from Settings with durable profiles and one-attempt rollback.
**Spec:** `docs/superpowers/specs/2026-10-23-root-updates-design.md` (approved 2026-10-23).
**Architecture:** Independent root-owned Python worker with flock and durable JSON storage; Node's built-in HTTPS/crypto verifies release metadata and downloads. A separate JS LS2 service accepts fixed commands; Root UI restores its data before rendering.
**Stack:** Existing Python 3, Node.js, webOS Luna tools; no new dependencies.

## Constraints and interfaces

- Do not touch the other checkout, TV, signing secrets or published releases.
- Root app `com.cleanyourtv.root.preview`; updater `com.cleanyourtv.root.updater`; updater service adds `.service`.
- State `/var/lib/clean-your-tv-root-updater`; immutable trusted code under `code/` provisioned by host.
- Ordinary update never replaces private routing runtime or updater. Pin exact compatible recovery-provision hash in host-seeded infrastructure receipt and manifest runtime contract `1`; mismatch blocks updates.
- Profile JSON `{schema:1,inventory:{apps:[],inputs:[]},config:{columns,dockApps,hiddenApps,...},settings:{"tvhome.order":string}}`; no renewal. 4 MiB UTF-8 total, 200 apps, 100 inputs, icon 256 KiB.
- Manifest `{schema:1,edition:"root",application:"com.cleanyourtv.root.preview",release:"vX.Y.Z",version:"X.Y.Z",runtime:1,updater:1,profile:1,url,sha256,size,notes}`; signed RSA-SHA256 envelope `{payload,signature}`. Feed `root-update.json`, distinct from Home.
- Service RPC wrapper `{returnValue:true,result:...}`. `check {}` → `{installed,candidate,canInstall,reason}`. `status {}` → transaction or null. `install {version,profile}` → persisted transaction. `restoreProfile {}` → `{profile,transaction,version,phase}` or null. `ready/confirm {transaction,version}`. `reconcile/rollback {}`.
- UI no arbitrary URLs or shell. Auth uses LS2 caller identity and strict field lists.
- Worker transaction APIs run under one process-independent flock. CLI commands enqueue by durable command/request under lock, detached worker retains lock and resumes polling. Ready/confirm use durable transaction-bound receipts so UI never waits for worker lock. Unknown installer outcome blocks further installations.

## Task 1: Durable update engine and profiles

Files: `root-edition/updater/core.py`, `store.py`, `profile.py`, tests in `root-edition/tests/test_update_core.py`.

- [x] Write failing tests using real temporary disk storage and deterministic external adapter: preserve exact profile, success, health timeout rollback, definite failure, unknown outcome, restart, no duplicate, corrupt journal/profile, rollback failure, stale receipts.
- [x] Run tests red, implement the minimal core and rerun green.
- [x] Store atomic fsync JSON; validate root-owned paths, refuse symlinks/oversize; immutable per-transaction profile. `Store(root, uid=0)`, `.read(name)`, `.write(name,value)`, `.lock()`; reject unsafe name/path.
- [x] `Manager(store,io)` methods `install(version,profile)`, `run()`, `ready(transaction,version)`, `confirm(transaction,version)`, `reconcile()`, `rollback()`, `restore_profile()`. Adapter `offer()`, `installed()`, `prepare(candidate,prior)` (verified cached local IPKs), `routing_status()`, `restore_route()`, `install(manifest,on_submit,on_terminal)` (durable evidence callbacks), `verify_installed(manifest)`, `launch()`, `now()`.
- [x] Phases persisted before side effects. Save old route intent; always restore route before installer. State includes id, prior/candidate, immutable profile digest, phase, deadlines, submitted/terminal evidence, rollbackAttempted. Never replay installing/rolling-back after crash without terminal proof. Healthy confirmation is 120 s; active Root requires fresh protected activation after commit, never automatic confirmation.
- [x] CLI worker may loop `run()` until awaiting confirmation/terminal; Manager methods support independent durable health receipts and read-only restoration while worker runs. Inject failures only at external effects and real Store writes.

## Task 2: Signed feed and device worker

Files: `updater/fetch.js`, `device.py`, `cli.py`, `service.js`, bootstrap/provision helpers and tests.

- [x] Test signature, wrong edition/identity, invalid URL/version/size/contracts, package hash and strict input rejection before production implementation.
- [x] Reuse Node crypto and constrained HTTPS; bound metadata and download, verify local IPK payload/identity and cached prior. Implement device adapter with independent installer observation, durable terminal records, recovery runtime route restoration and verified app launch.
- [x] Worker runs outside app package; detached and boot-reconciled; fixed Python executable and private code. Fail closed on incompatible infrastructure and missing prior cache. LS2 exposes only scoped methods and authorization.
- [x] Integrate lifecycle lock/gate so new enable/boot activation is refused while an update owns routing; explicit exit wins; existing runtime copied to new installations includes gate. Existing installations require reviewed infrastructure bootstrap.

## Task 3: Root profile bootstrap and settings

Files: `ui/root-profile.js`, `ui/root-updates.js`, `ui/root-settings.js`, CSS, `preview.py`, UI tests.

- [x] Test capturing icon data/config/order and restoring before rendering, corruption blocks empty grid, no renewal calls, readiness and confirmation transaction binding.
- [x] Add Software updates panel and recovery app with remote-key navigation, focused enabled buttons, Back handling, busy/failed states, confirmation after first launch.
- [x] Keep the existing look, use live status and visible focus; don't load ordinary updater scripts.

## Task 4: Build, bootstrap, release tooling and docs

Files: `build.py`, `preview.py`, `deploy.py`, host updater setup/build/sign helpers, `ROLLOUT.md`, `README.md`, `docs/EDITIONS.md`, `scripts/test.sh`.

- [x] Test versioned Root build, complete standalone updater bundle and dry-run host provisioning. Preserve existing default build tests.
- [x] Build updater IPK and trusted setup bundle; explicit host bootstrap installs updater, grants scoped permissions, seeds hash-verified rollback IPK and infrastructure identity. Never overwrite a live runtime in ordinary update.
- [x] Add public-key signing validation for root metadata, require explicit key file. No release publication.
- [x] Document one-time setup, compatible updates, recovery and exact hardware acceptance commands.

## Task 5: Integration and review

- [x] Run focused tests then `bash scripts/test.sh`, build both artifacts and inspect package contents.
- [x] Review full branch independently; fix important findings with regression tests.
- [x] Record limitations honestly: local validation only; signing/publication and isolated TV acceptance remain external release gates.

## Execution record

- Tasks 1–4 implemented. Full intended-tree tests and both offline builds passed; final scoped re-review and post-fix verification are recorded in the local execution ledger.
- Device terminal failure classification and isolated TV acceptance remain explicit release gates; no TV operation or publication was performed.


- Baseline: full repository tests started on clean `main` worktree.
- Ruling: native worktree creation returned Not a git repository for the container directory; used Git worktree in the authorized project root instead.
- Ruling: use one core implementer and independent final reviewer (subagent-driven-development/requesting-code-review); parent owns tightly coupled device/UI integration to keep contracts consistent. Never run two implementation subagents concurrently.
