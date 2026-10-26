# Updates for every TV component

Approved by the user on 2026-10-25, including a one-time computer bootstrap.

## Outcome

Software updates offers one signed compatible release for the installed edition,
with installed/available component versions and Update all. Root access remains
required. No-root edition on an unrooted TV keeps computer installation.

## Architecture

A small independently provisioned System Updater service and detached Python
worker live outside Home, Helper, both Updater IPKs and the Root runtime. Its
root-owned journal, cached packages and boot recovery survive their replacement.
This bootstrap supervisor is the fixed installation/recovery mechanism; ordinary
release code cannot replace its trust key or broaden its allowed destinations.

A new RSA-SHA256 signed system-update.json feed describes edition-specific
components with fixed identities, versions, sizes and SHA-256. Packages are
downloaded only from this repository's GitHub release assets. Root infrastructure
is a bounded data bundle targeting only the existing managed runtime, private
Root recovery service and updater code, with hashes and recovery receipts updated consistently. Arbitrary commands,
paths and UI-provided URLs are never accepted.

The worker verifies and caches the entire candidate and baseline before changing
the TV. It rejects concurrent legacy updater transactions and records intent
before every installer call. Unknown installer outcomes block further writes;
they never cause a second installation or automatic rollback. Confirmed terminal
success permits payload verification. A failed readiness check after terminal
success permits one rollback in reverse order. Reboot resumes only safe local
steps and does not replay an uncertain installation.

## User state

Capture the full existing Home/Root profile before installation. Restore through
the independent service before rendering and report startup readiness tied to
the transaction and installed version. Keep previous packages and profile for
explicit rollback. Preserve helper preferences, emergency-stop latch and renewal
preference. Suspend input ownership and return Home to LG during mutation; do not
resume if the user explicitly or urgently disabled control during installation.
Root runtime/updater receipts and service registrations must remain usable after
both upgrade and rollback. Never report installation success as startup health.

## Integration and validation

Both editions' existing Settings entry points and standalone recovery apps open
the same panel after bootstrap; existing Home-only recovery remains available.
The computer setup provisions the independent service, baseline cache and boot
hook once, refusing unfinished or conflicting setup. Release preparation builds
and signs the system feed from exact final assets. Tests exercise real policy,
journal persistence, interrupted submission, rollback, profile restoration,
authorization, packaging and remote navigation. Hardware validation is separate
from local completion and must be reported honestly.
