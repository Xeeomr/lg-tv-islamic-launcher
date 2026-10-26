# Root persistent lifecycle implementation plan

Goal: retain user intent across reboot without re-enabling Root mode after an
emergency exit, failsafe, failed recovery or interrupted startup. Keep the RC13
bounded escape implementation and production applications untouched.

Architecture: a durable intent journal is separate from the existing routing
recovery journal. The latter remains authoritative for restoring exact Home
state. A pure transition policy decides whether startup may be attempted. An
atomic root-private store serializes transitions and rejects stale generations.
A boot adapter may activate only after recovery, input readiness and independent
watchdog readiness. No persistent command is unlocked by this local milestone.

## Invariants
- An explicit enable first records a trial; only confirmed healthy trial enables
  persistent intent. Timer expiry is not confirmation.
- Emergency exit/failsafe/health loss writes disabled intent before recovery.
- Boot recovery restores previous routing before any new activation.
- A duplicate boot callback is a no-op. An interrupted startup never retries
  automatically; a new explicit enable is required.
- Every asynchronous result carries a generation and startup token. Stale events
  cannot enable, disable or recover a newer attempt.
- A failed or incomplete restoration prevents activation.
- No writes to the TV or changes to production launcher/helper in this phase.

## Execution (inline, test first)
- [x] Add lifecycle tests covering explicit confirmation, reboot, duplicate
  callbacks, interrupted startup, failsafe and stale event results.
- [x] Implement transition(state, event), returning durable state and one effect
  (`none`, `recover`, or `start_guarded`). Effects run only after state is saved.
- [x] Add atomic journal tests: symlink rejection, stale generation, failed
  replace, restart replay. Implement a store that uses the existing trusted_dir,
  safe_json and fsync primitives, with a separate lifecycle lock.
- [x] Exercise power-loss points by reloading the actual persisted journal and
  replaying callbacks; run complete repository checks.
- [x] Record local acceptance and exact remaining device integration gates.

Next integration: connect durable effects to transaction-bound restoration and
RC13 observer readiness; implement a renewable, independently watched lease,
then validate normal/failsafe boots and frozen-UI escape on the final TV bundle.
Until then, enable/confirm remain unavailable and no persistent package is shipped.

## Local verification record

Implemented `runtime/persistent_lifecycle.py`, `persistent_store.py` and
`persistent_lease.py`; no device commands/import hooks invoke them. They are
intentionally excluded from deploy.RUNTIME_FILES until transaction binding and
boot wiring have been reviewed and tested.

30 targeted tests cover state transitions, real atomic disk persistence/failures,
stale event rejection, lease validation and an independent guard surviving a
SIGSTOP of its heartbeat publisher. Existing CLI enable/confirm fail-closed tests
remain passing. The saved intent generation/token must be explicitly bound to the
routing journal transaction by the adapter; never substitute one ID for the other.

Outstanding integration (not completed by the local policy tests): durable
transaction binding, heartbeat publication driven only by input-loop PING,
independent watchdog process readiness, normal/failsafe boot adapter, explicit
confirmation UI, and final-bundle device acceptance. Persistent mode is not ready
to install or advertise as supported.

## RC14 integration follow-up

Implemented durable transaction binding and an opt-in `intent-trial` adapter.
Binding happens before any profile publication; gesture and deadline recovery
use the intent coordinator. CLI restore/boot preserve legacy dispatch and do not
unlock permanent activation. Coordinator recovery uses RC13's real restore path,
checks the full baseline, and retains evidence on conflicts/interruption.

The C3 accepted the bound gesture exit and unattended timer exit; evidence is in
RELEASE-ACCEPTANCE.md. Boot callback replay passed in the same boot. A physical
reboot/failsafe test of this exact binding is still pending. Renewable lease
publication/guard process, controlled promotion and confirmation UI remain the
next integration tasks; the persistent lease policy is still not shipped.

## RC15 implementation

- [x] Publish volatile leases only from valid input-loop PING.
- [x] Independent guardian continues while confirmed intent and input lease hold.
- [x] Supervisor verifies guardian pulses; observer/supervisor stalls expire leases.
- [x] Explicit transaction-bound promotion under routing lock, with deadline margin.
- [x] Restore-before-restart boot integration and fail-closed failsafe/startup.
- [x] Settings enable/confirm/status/exit and scoped LS2 methods.
- [x] Full local tests and independent code review; timestamp race fixed.
- [ ] RC15 hardware: promotion past 60s, emergency exit, reboot and failsafe.
- [ ] RC15 hardware: independent process fault recovery and clean uninstall.
- [ ] Supported release after final acceptance.
