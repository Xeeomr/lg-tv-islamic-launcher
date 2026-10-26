# Optional managed Python for Root Edition

Approved direction: automatically use a private, pinned Python 3 runtime when the
TV's system interpreter cannot meet Root requirements. Do not grow normal desktop
or Android installer packages by embedding the runtime or download it on the normal
path. The user authorized full implementation and candidate integration, followed
by preparation of the candidate for main; hardware acceptance remains pending.

## Delivery and trust

Pin CPython 3.13.17, python-build-standalone release 20261021,
armv7-unknown-linux-gnueabi-install_only_stripped, 26256859 bytes,
SHA-256 4a71641c8d5536175e404a961624e8656eba30e97b5026f6bd7dc31e4bbeaaea.
The immutable descriptor ships in installer source, rather than trusting remotely
mutable metadata. HTTPS downloads must enforce size/hash bounds, cache only verified
bytes, validate every archive path/type/link, and never execute unverified files.
Progress and errors must explain download and compatibility outcomes. No pip,
system library replacement, global PATH mutation, Python 2 port, or /usr/bin edits.

Host normalizes the upstream archive into regular files and installs an immutable
version slot under /var/lib/clean-your-tv-python/<archive-sha256>/, with
bin/python3.13 as the executable. A .cytv-runtime.json inventory has schema 1,
archive_sha256, and files mapping relative regular paths to SHA-256 hashes.
Provisioning uses SSH and shell without requiring target Python. Reject symlinked,
foreign or writable paths, insufficient space, unsupported ELF/CPU ABI, corrupt
cache, incomplete slots and failed smoke tests. Never overwrite an active slot.

## Selection and binding

Use working existing bindings first, then suitable /usr/bin/python3. Provision only
for install or explicit enable-system-updates, never as a side effect of status,
doctor, restore or removal. System Python minimum is 3.9 and required operations
must work. Managed runtime must pass the same module/process/filesystem probes.

Root, Root Updater and System Updater each persist a root-owned python-launcher
inside their private state. It execs a literal verified interpreter path. Legacy
installations without a launcher keep /usr/bin/python3. Managed paths are restricted
to the pinned namespace. Internal child processes and guardian identity use the
actual selected interpreter. Runtime inventory/binding evidence belongs to recovery
validation; no mutable global current symlink or environment-based selection.

Never remove managed Python while any installed/recovery component can need it.
Uninstall may retain the small number of immutable runtime slots with explicit docs.
Runtime changes must preserve previous bindings needed for rollback.

## Validation and delivery

Tests cover no-download system path, SHA/size/archive/redirect/cache failures,
shell bootstrap without Python 3, partial provisioning, smoke-test failure, persistent
bindings, child identity, reboot hooks, recovery/updater ownership and backward
compatibility. Inspect the real pinned archive and run ARM emulation if available.
Run existing installer, Root and system-update suites and applicable CI. Integrate
through an implementation PR targeting release/next; update release-plan and #35.
Prepare versions, notes, builds and release gates without claiming TV validation.
