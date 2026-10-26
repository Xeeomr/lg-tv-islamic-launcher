# Contributing

In the maintained local workspace, use the project root as the only active checkout for
all development, documentation, builds, commits and releases. This includes
No-root, Root and the desktop/console installer. Run Git and build commands from
the project root. `release/next` is the integration branch; `main` accepts finalized release PRs only.
Switch branches within this checkout as needed.
The former `release-desktop/` checkout is archived under
`archives/2026-10-24-release-desktop/`. The former `stable/` checkout was moved
to the project root on 2026-10-25, preserving its Git history and local changes.
The previous workspace README and legacy Root symlink are preserved in
`archives/2026-10-25-workspace-flattening/`. Archives and the
legacy Root checkout are for reference/recovery only; do not develop or publish
from them. Coordinate concurrent edits and commit or stash incomplete changes
before switching branches. Contributors with their own clone can use its normal
checkout path; the single-checkout rule describes this maintained workspace.

Write technical and developer documentation in English. Maintain the ten localized
user guides under `docs/i18n/` when changing user-facing setup or controls.
For every release candidate, complete the [documentation pass](docs/RELEASE-FLOW.md#update-documentation-for-every-candidate),
record reviewed guides and verification in the release PR, and keep candidate
instructions separate from published downloads and historical hardware evidence.

Run `npm ci` first. TV web packages use Babel/core-js and PostCSS, with a strict
compatibility check after conversion; see [TV web build](docs/TV-WEB-BUILD.md).
Helper app/service JS uses a separate Babel/core-js/safe-buffer build for TV
Node 0.12.2+. Set `NODE012` to run its regression against that exact runtime.
Keep changes small and reproducible. Run `scripts/test.sh`; describe the test model,
firmware, expected behavior and actual behavior. Separate standby tests from cold
boots. Never claim compatibility from a successful package installation alone.

Input changes must preserve triple-Home emergency release (long Home in legacy
Helper versions through 0.6.13), watchdog behavior, key-up delivery
and unrelated buttons. Do not automatically clear emergency-stop state. Explain
any new persistent state, permission or network endpoint in the pull request.

Share only redacted logs. Exclude SSH/SSAP credentials, addresses, SSIDs, app
inventories and personal screenshots. Report security issues privately to the
repository maintainer once a reporting channel is configured; do not publish credentials.


Target feature, fix and maintenance PRs at `release/next`. No release version is
needed during preparation. Link related issues in the PR. At candidate freeze,
collect the inventory, select the version and complete the release PR checks;
see [Release integration flow](docs/RELEASE-FLOW.md). Shipping notices are posted
automatically only after verified publication.
