# Optional Root Python Implementation Plan

> **For agentic workers:** Use subagent-driven-development to implement and review the scoped tasks.

**Goal:** Root setup automatically supplies a private Python only when needed.

**Architecture:** An embedded immutable artifact pin authenticates an on-demand
host download. SSH shell provisioning installs a version slot before any Python
driver is invoked. State-local launchers bind Root and both updaters to the same
tested interpreter; existing working system installations retain their fast path.

**Tech Stack:** Python stdlib, existing SSH transport, shell, existing Node services.

**Spec:** ../specs/2026-10-25-bundled-root-python.md

## Global Constraints

- No bundled runtime bytes or normal-path network request in desktop/Android installers.
- No /usr/bin edits, global PATH changes, unverified executable or arbitrary runtime URL.
- Runtime identity is the pinned SHA-256 and executable is bin/python3.13.
- Do not replace active slots or delete interpreters needed by recovery or rollback.
- Preserve legacy /usr/bin/python3 behavior for installations without binding receipts.
- No claim of physical-TV acceptance; candidate integration is not stable publication.

## Task 1: Verified host acquisition and shell provisioning

Files: create cytv/python_runtime.py and tests/cytv/test_python_runtime.py.
Produces select_python(remote, cache_dir, progress, provision=False) -> executable
absolute string. It checks the system Python and only downloads/provisions when
provision=True and needed; caller may prefer an existing state launcher first.
Managed directory and inventory format are fixed by the spec.

- [x] Write failing tests for a working system interpreter making zero downloads,
  size/hash/cache/link/path failures, unsupported targets and smoke-test failure.
- [x] Implement bounded HTTPS acquisition, verified cache, safe archive normalization
  and atomic shell provisioning with space/ownership checks and progress.
- [x] Run the tests, inspect the pinned real archive, record results and commit.

## Task 2: Root runtime and recovery binding

Files: root-edition except updater/, build_updater.py and setup_updater.py; scoped tests.
Produces root-edition/python_binding.py exposing current_executable(),
launcher_bytes(executable=None), install_launcher(state, write), and verify_binding(state).
The helper defaults to /usr/bin/python3 unless running from the managed namespace;
it validates the managed inventory/ownership before persisting binding evidence.

- [x] Write failing tests for private launcher persistence, child interpreter and
  guardian identity, boot hook ownership, recovery proof and legacy compatibility.
- [x] Bind deploy/provision/boot/service to the selected interpreter. Copy the helper
  into build support; runtime children use actual sys.executable consistently.
- [x] Run Root/recovery tests, record results and commit.

## Task 3: Installer and updater integration

Files: cytv/operations.py, cytv/cli.py as needed, root-edition/updater/,
root-edition/build_updater.py, root-edition/setup_updater.py, system-updater/,
cytv/*updater_remove.py and scoped tests.
Consumes select_python and python_binding interfaces above.

- [x] Add failing tests for missing-Python Root install automatically selecting
  managed Python, zero-download maintenance, update workers and removal receipts.
- [x] Route every TV Python command through the selected interpreter/binding,
  preserve legacy hooks, include the binding helper in strict bundle inventories,
  and ensure system-updater infrastructure migration preserves valid bindings.
- [x] Run installer/updater/system tests, record results and commit.

## Task 4: User guidance, packaging, review and release integration

- [x] Add translated progress/error messages, packaging resource inclusion and docs
  explaining automatic download/cache, offline priming, retained slots and limits.
- [x] Run combined installer, Root, updater and packaging checks; review whole diff,
  resolve findings and run applicable CI on the implementation PR.
- [x] Merge implementation into release/next, collect inventory, update #35 and
  prepare candidate versions, release notes, builds and explicit acceptance gates.
