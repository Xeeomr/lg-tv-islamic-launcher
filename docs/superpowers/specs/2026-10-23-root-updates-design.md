# Root Edition updates from Settings

Status: approved by the user on 2026-10-23; implemented locally, release acceptance remains open.

Implementation note: the production adapter currently classifies successful
installer completion only. Automatic rollback follows a verified completed
install with failed payload/readiness checks. Raw installer failures remain
blocked until firmware-specific terminal failure evidence is validated; the
core's definite-failure branch must not be confused with a device classifier.

## Outcome

Root Edition gains Settings → Software updates: check a signed Root release,
confirm installation, preserve the complete launcher profile, and recover the
previous application and profile after a confirmed failure. An independent
Root Updater application remains available when Root Home cannot start.

This design updates the Root application package. The independently provisioned
root routing/recovery runtime and the updater remain pinned infrastructure.
Releases requiring different infrastructure are blocked with an explicit
computer-assisted upgrade instruction. They must never install a newer web UI
against an incompatible private runtime. Supporting transactional replacement
of the recovery runtime itself is a separate infrastructure migration.

## Existing constraints

- Application: `com.cleanyourtv.root.preview`, currently version `0.0.1`.
- Recovery service: `com.cleanyourtv.root.preview.service`. Its active code is
  copied into `/var/lib/clean-your-tv-root/service`, outside the package.
- Routing runtime: `/var/lib/clean-your-tv-root/runtime`; integrity is checked
  against `recovery-provision.json`.
- Root packaging explicitly removes `user-data.js`, `profile-bootstrap.js`
  and `update-panel.js`. Re-enabling them unchanged would call the ordinary
  Home updater and Developer Mode renewal service.
- `apps.js`, `config.js` and packaged icons contain personalized launcher data;
  `tvhome.order` in localStorage contains the user's tile order.
- Existing `HomeData` provides a bounded data-only profile format. Existing
  signed-release policy is hardcoded to ordinary Home and cannot accept Root
  packages unchanged.
- Existing Root installation observes independent backend completion events.
  An accepted request, visible version, empty status list or dead client is
  insufficient evidence that installation has terminated.

## Approach and alternatives

Use an independent Root Updater with its own service, persistent journal,
cached rollback package and recovery screen. Reuse bounded profile validation,
signature verification patterns, safe storage and installer observation where
their contracts fit. Do not fork the ordinary renewal-dependent manager or
broaden its manifest policy to accept another application implicitly.

Running the transaction inside Root Home is rejected because replacing Home
terminates the transaction owner. Updating every private routing/runtime file
in the first release is rejected because it would require a new transactional
boot/provisioning migration, including recovery of the recovery mechanism.

## Trust and packaging

Introduce `com.cleanyourtv.root.updater` and its dedicated service. Provision its
root-owned independent worker and boot reconciliation once through the host
installer. Existing installations require this one-time computer-assisted
upgrade before updates from Settings become available. Later compatible Root
application releases update directly on the TV.

Use a separate `root-update.json` feed and Root-specific signed manifest. Pin
the edition, application ID, release tag, application version, required runtime
contract and updater contract, package URL, SHA-256, maximum download size,
profile schema and release notes. Accept only this repository's release URLs
and the GitHub release asset CDN. Verify RSA-SHA256 using a packaged public key;
never take a key, path, command, application ID or download URL from UI input.
Reject unsigned metadata, wrong edition, incompatible contracts and ordinary
installation downgrades. Rollback is restricted to the recorded previous
package for this transaction.

The Root builder must accept a validated release version rather than retaining
the hardcoded `0.0.1`. It produces the package and matching release description.
Signing is an explicit maintainer action using an existing private key outside
the repository. A locally built unsigned package is not an available update.

## Data preservation

Add a Root-specific profile bootstrap before `app.js`. Capture the current
application list, embedded icon bytes, inputs and labels, complete launcher
configuration and tile order. Exclude ordinary Home's renewal history and
control operations. Reuse `HomeData` limits: 200 applications, 100 inputs,
4 MiB serialized profile and 256 KiB per icon. Additional Root-specific fields
must be explicit schema fields, never an unrestricted localStorage dump.

Save the snapshot locally and in Root Updater's private persistent storage.
Validate it, synchronize it to disk and read it back before starting an install.
Unreadable existing data, missing icons, oversized profiles, insufficient disk
space or failed durable storage stop the update before package replacement.
Root routing intent is tracked separately from the launcher profile.

After installation or rollback, restore the transaction's profile before
constructing the launcher grid. An empty generic package must not replace a
saved populated profile. A corrupt profile must show recovery instead of
silently rendering an empty launcher. The transaction snapshot is immutable;
normal future preference changes must not mutate its rollback copy.

Preserving applications means preserving the launcher's inventory and icons;
the updater does not uninstall or reinstall third-party applications.

## Transaction and routing

Persist phases before their side effects: preparing → downloading → backed-up
→ restoring-route → installing → awaiting-launch → verifying → complete.
Failure paths use rolling-back → rolled-back, or recovery-required when the
installer outcome cannot be established. Use a process-independent exclusive
lock and transaction IDs; duplicate calls and restarts cannot create a second
installation.

Before replacement, cache and verify both the offered package and a matching
previous package. Installation is unavailable without a verified rollback
package. The first updater-enabled host installation must seed that package
and its trusted descriptor. Keep both packages and the profile until the next
successful transaction has safely established its own rollback baseline.

Record whether Root mode was active, then restore and verify the LG Home route
using the existing runtime. Do not overwrite routing journals, clear failsafe
markers or start the ordinary Home helper. Abort before installation if route
restoration is unconfirmed. The update journal coordinates with lifecycle
operations so boot recovery, enable, exit and installation cannot race.

The independent worker submits installation only after subscribing to backend
completion events and verifying installer idleness. Record submission identity
and terminal evidence durably. Reopen Root Home only after matching completion
and installed package identity/hash verification.

The new application restores its profile, renders its expected tiles and
reports readiness bound to the transaction and installed version. Require
explicit on-TV confirmation within 120 seconds of verified application launch.
Rendering alone cannot certify remote interaction. If Root was active before
updating, restore it through the existing protected 60-second trial and require
the existing Keep Root mode confirmation. Do not automatically promote a trial
or restore a prior generation's intent file. Updates begun with Root disabled
leave it disabled. Explicit Exit or an emergency gesture cancels reactivation.

## Rollback and interruptions

On a definite terminal installation failure, or a failed/timed-out health
confirmation after terminal installation success, restore LG routing and make
one observed installation attempt of the cached previous package. Restore the
same profile before launching it. Verify package identity and restored data;
report rolled-back and leave LG routing safe. Offer protected Root activation
again instead of silently reenabling a failed version's routing.

A timeout, lost subscription or interrupted submission is not a definite
failure. Persist recovery-required and keep LG routing; do not submit rollback
until matching terminal installer evidence establishes that the original job
has stopped. A version query alone never unlocks recovery. On reboot or worker
restart, reconcile the durable journal before permitting another transaction.
Keep unknown operations blocked when safe termination cannot be proved.

If rollback itself fails, preserve both packages, profile and journal, leave
LG Home selected and show the recovery state in the independent updater.
There is no retry loop, clear-lock button or automatic deletion of evidence.

## User interface and service boundaries

Settings adds Software updates with installed/available versions, release
notes, Check for updates, Update, explicit confirmation and Recovery. Display
download/install/verification/rollback state with actionable errors. Respect
Back and remote focus; disable duplicate actions while busy. If initial updater
provisioning is absent, explain the one-time computer setup.

The independent updater exposes only check, status, install, restoreProfile,
ready, confirm, reconcile and rollback operations. Installation accepts the
offered version, transaction identity and bounded data-only snapshot, never
arbitrary executable input. Enforce caller identities and scoped LS2 grants;
public/unrestricted callers cannot install, replace profiles or signal health.
The recovery app can inspect/recover when Root Home is broken.

## Verification and release gates

Automated tests must exercise successful update, exact profile restoration,
rollback after definite failure and missing health confirmation, failed
rollback, restart at each persisted boundary, duplicate requests, stale health
signals, corrupt data, missing rollback package, disk failures, wrong edition,
bad signature/hash, incompatible runtime and uncertain installer outcomes.
Use real durable temporary storage and deterministic transport/clock adapters.
Add build tests for Root identity/version and exclusion of ordinary updater
and renewal behavior. Verify remote navigation in both settings and recovery.
Run the existing full repository test script after focused checks pass.

Hardware acceptance uses an isolated application first: successful update,
preserved populated profile/order, definite failure rollback, killed UI,
interrupted worker, reboot reconciliation and independent recovery launch.
Only hardware evidence permits claiming TV validation. This work does not
authorize publishing a release, handling signing secrets or changing a TV.

## Workspace

The local source checkout is on `feat/cytv-installer` and contains unrelated
installer work. Implementation should use a separate branch/worktree based on
local `main` without carrying or reverting those changes. Implementation uses `feat/root-settings-updates` in a separate worktree.
Concurrent settings redesign edits are preserved outside the update commits.
