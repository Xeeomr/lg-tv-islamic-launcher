# Root Edition Stable Acceptance Plan

> **For agentic workers:** Use executing-plans to implement this plan task-by-task. No new interface architecture is part of this stabilization pass.

**Goal:** Qualify a fixed Root build on OLED55C3RLA / 43.21.71 before describing it as stable on that configuration.

**Architecture:** Preserve separate application identity, explicit persistent intent, reciprocal watchdogs and exact baseline recovery. Test the same immutable executable bundle throughout; any runtime fix invalidates affected evidence and requires targeted retesting.

**Tech Stack:** Python 3 runtime/installer, JS webOS service and launcher, SSH, LS2.

**Spec:** root-edition/RELEASE-ACCEPTANCE.md and root-edition/TESTING.md.

## Constraints

- Keep original launcher/helper and private profile intact; never run both input owners.
- Do not disable guards or override safety latches.
- Keep private backups/logs outside Git; record only sanitized results and hashes.
- Reboots and physical interactions require user availability. Never simulate user confirmation.
- Unified Root/No-root installer and boot artwork are deferred.

## Tasks

- [x] Identify installed bundle against reproducible local artifact; verify local suite.
- [x] Capture state and ordinary launcher/helper hashes for rollback and comparison.
- [x] Validate UI exit and triple-Home emergency on this artifact, including independent frozen-renderer test with bounded resumption.
- [x] Validate native controls, Back Cancel/exit in multiple available apps, and quick standby.
- [x] Validate genuine failsafe restoration and subsequent ordinary startup with user-authorized reboots.
- [ ] Validate cold-power startup with user participation; do not substitute software reboot.
- [x] Validate clean removal/reinstallation of the same bundle, retaining state and user profile.
- [ ] Review results; resolve only demonstrated faults with regression tests.
- [ ] Produce model-scoped release notes/artifacts/checksums, merge and release only after required gates pass.

Each hardware result must include artifact identity, transaction, baseline/after readback, protection status and user-visible behavior. Unknown results remain open.
