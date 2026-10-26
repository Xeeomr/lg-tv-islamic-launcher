# Release flow implementation plan

**Goal:** Integrate features in `release/next`, choose a version at candidate freeze,
protect `main`, and notify shipped PRs/issues after verified publication.
**Spec:** `docs/RELEASE-FLOW.md`, amended by the request to choose versions late.
**Architecture:** A standard-library Python CLI validates a committed release plan
against merged GitHub PRs and creates a release inventory bound to the source SHA.
CI enforces the policy and reuses the existing publication verification before
idempotent notifications. GitHub branch protection requires the policy and tests.

## Tasks

- [x] Write behavioral tests for delayed version selection, release branch routing,
  complete PR coverage, excluded changes, immutable inventory and notification retries.
  Run `python3 -m unittest discover -s tests/setup -p test_release_flow.py -v`
  and confirm the missing implementation fails.
- [x] Implement `scripts/release-flow.py`: `check`, `inventory`, `notify` and
  `protect` commands. Validate only final candidates for main; accept null versions
  during development. Read PR scope from GitHub, preserve it in a release asset,
  and require publication verification before notifications.
- [x] Add a PR policy workflow and PR template; extend trusted Android builds to
  `release/next`; package inventory before checksums/upload and notify only after
  successful publication verification. Add a notification-only retry workflow.
- [x] Update contribution/release documentation for `release/next`, late versions,
  release-plan fields, hardware acceptance and rollout requirements.
- [ ] Run targeted tests, `scripts/test.sh`, workflow validation and `git diff --check`.
  Configure main protection with exact GitHub Actions check names and read it back.
  Prepare a feature PR into `release/next`; do not publish a product release.

## Constraints

Use the existing stable checkout; preserve unrelated `docs/research/` files.
Never expose signing secrets to PR code. Stable publication remains main-only.
Use no new runtime dependency. Keep real shipping notices disabled until a release
is actually published. Do not choose a version or close issues during setup.

Bootstrap uses one installation PR from `release/next` to `main` with versions unchanged; enable the trusted required status only after its workflow is installed.
