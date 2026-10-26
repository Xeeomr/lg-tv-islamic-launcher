# Release integration flow

Features, fixes and maintenance integrate in `release/next`. Only a finalized
release PR from that branch may merge into `main`. This repository calls its
primary branch `main`, not `master`. The preparation branch has no version in
its name: choose the version when the candidate's scope is known.

## Collect changes without choosing a version

1. Create `release/next` from `main`, or fast-forward the existing branch to
   `main` after the previous release. Use merge commits for all PRs. Squash and
   rebase merging are disabled to preserve ancestry across release cycles.
2. Start the new cycle with `release-plan.json` containing `version: null`, empty
   `changes`/`excluded` lists and empty `acceptance`. Keep the last shipped
   `release-versions.json` value until freeze; it is not the next version.
3. Target implementation PRs at `release/next`. Record linked issues using
   GitHub's closing references or a plain `Related issues: #123, #456` line.
   Links and inventory numbers refer to this repository. Do not close a partially
   delivered issue merely because its PR merged.
4. Open a draft `release/next` → `main` PR using the release template. Its policy
   check remains unsuccessful until the version, scope and acceptance are final.
5. After merging implementation PRs, collect the inventory on `release/next`:

   ```sh
   git fetch origin main
   python3 scripts/release-flow.py collect
   ```

   This updates the plan with PR titles and linked issues without selecting a
   version. Review the summaries, add any extra related issues, and commit it.
   The collector includes only merged implementation PRs present in the commit
   range since `origin/main`; previous releases are not repeated.

An issue describes work; its implementation enters through a PR. Metadata-only
commits such as preparing the plan and selecting versions may be made directly
on the preparation branch. Product changes should enter through reviewed PRs.

## Maintain the release candidate PR description

Every `release/next` → `main` release candidate must maintain a current release
record in its PR description, starting when the draft is opened. Use the
[release PR template](../.github/PULL_REQUEST_TEMPLATE/release.md). Updating
`release-plan.json` alone does not update this record.

The maintainer integrating an implementation PR must update both the release
inventory and the candidate PR description as part of that integration. Refresh
the description after scope changes, exclusions or reversions, version decisions,
new validation results and candidate freeze. Do not leave this until publication.

The description must contain:

- **Scope:** every included implementation PR and related issue, its resulting
  behavior, and any exclusions or partial delivery. Keep it consistent with
  `release-plan.json`.
- **Version table:** the overall release and every component (Home, Home Helper,
  cytv installer, Android installer, Root edition and independent updater). Show
  the last published version, the version currently committed in the candidate,
  the proposed/final target, the reason for changing or retaining it, and whether
  the bump is proposed or committed. Include Android `versionCode`. Before a
  target is selected, write `TBD`; never present a proposal as an applied bump.
- **Packaging impact:** identify packages/installers that need rebuilding and
  any pinned baseline that prevents source changes from shipping. In particular,
  Helper source fixes do not reach users while builders reuse the published
  package at the unchanged Helper version. Record the required version bump,
  manifest synchronization, new source-package validation and rollback checks.
- **Validation:** actual test/build results with links or reproducible commands
  and the checked commit or PR revision. Distinguish checks on an earlier PR
  from checks on the combined or frozen candidate; record pending and failed
  checks. A version bump or package rebuild needs validation of the new artifacts.
- **Acceptance and release gates:** physical-TV model/firmware and tested paths,
  known limitations, untested behavior, rollback evidence and remaining work.
  Keep the checklist current; automated checks are not hardware acceptance.

At freeze, replace tentative version targets with the final values, verify them
against release metadata and component manifests, link the release notes, and
record validation of the exact frozen candidate. Until then, explicitly state
that the PR is an unfrozen draft and which bumps have not been committed.

## Update documentation for every candidate

The maintainer preparing each candidate owns a documentation pass against its
actual release inventory. Start it while collecting changes, refresh affected
instructions when an implementation PR merges, and finish it before marking the
release PR ready. Release notes alone do not replace updated usage instructions.

- Review README, installation/update/removal guides, troubleshooting, supported
  devices and prerequisites, and affected component documentation. Update commands,
  download links, versions, screenshots and recovery/rollback instructions where
  behavior changed. Remove obsolete instructions.
- Review translated guides for the same changes. Update affected translations;
  record any remaining gaps explicitly in the release PR.
- Check documented commands and links against the candidate's actual CLI and
  artifacts. Distinguish candidate-only instructions from the published stable
  release, and retain honest hardware-tested and untested limitations.
- Add a **Documentation** section to the release PR listing the reviewed/updated
  files, verification performed and remaining work. If a guide needs no change,
  record why. Resolve stale instructions before marking the PR ready; document
  deliberate remaining limitations rather than checking an unfinished item.

Repeat this pass after scope changes, reversions or version changes. The release
template and [release checklist](RELEASE_CHECKLIST.md) make it a maintainer gate;
CI does not establish that documentation matches product behavior.

## Freeze and validate the candidate

To collect device feedback before hardware acceptance is available, first prepare
new version metadata and release notes, then explicitly dispatch **cytv standalone
builds** on `release/next` with `test_build=true`. This produces installer artifacts
without filling `acceptance`, publishing a release, or satisfying Release policy.
Ordinary unfrozen pushes still skip platform builds. Keep the release PR in draft;
test artifacts do not establish hardware acceptance or replace the final exact-head
build after acceptance is recorded.

Choose the final version based on the actual scope. Set it in `release-plan.json`
and `release-versions.json`, update changed component manifests/versions, and
write `docs/RELEASE-X.Y.Z.md`. Component versions are independent of the overall
release version. A final plan looks like:

```json
{
  "schema": 1,
  "version": "1.2.0",
  "changes": [
    {"pr": 123, "issues": [45, 67], "summary": "Fix focus after returning Home"}
  ],
  "excluded": [
    {"pr": 124, "reason": "Reverted in full before candidate freeze"}
  ],
  "acceptance": "TV model and firmware; tested paths; untested paths; rollback evidence/link"
}
```

The required **Release policy** status is produced by a trusted
`pull_request_target` workflow executing policy from `main`. Feature PRs receive a separate **Integration policy** status, so their checks
cannot satisfy the release gate on another PR with the same SHA. Candidate commits
are fetched and read as data; their scripts are never executed by this workflow.
It rejects:

- A PR to `main` from any branch other than this repository's `release/next`.
- An unset, invalid, unchanged or regressing release version; mismatched metadata;
  missing release notes or empty hardware acceptance evidence.
- Missing, duplicate or unexpected implementation PRs in the release inventory.
  Every merged PR must be included or explicitly excluded with a reason. Partial
  delivery belongs in `changes` with an accurate summary; exclude only changes
  that will not ship.
- Omitted issues linked to included PRs. The gate checks closing references and
  `Related issues:` lines and verifies that listed issues are actual issues.
- An unsuccessful or incomplete trusted push build of the exact candidate SHA.
  Android and all four desktop jobs must each succeed. The policy waits up to
  35 minutes; rerun it if builds finish later.

`main` additionally requires up-to-date Linux/macOS tests, a PR and resolved
conversations. Administrators follow the same rules. Force pushes and branch
removal are disabled. No second maintainer approval is mandatory, allowing solo
maintenance; review the release diff before merging and keep repository write
access limited to trusted maintainers.

Apply the [release checklist](RELEASE_CHECKLIST.md) and Root Edition hardware
gates. CI cannot certify physical TV behavior: record actual acceptance and
untested paths honestly. Any new candidate commit invalidates its previous
checks and triggers a fresh complete build. Mark the PR ready only after all
checks and acceptance are complete.

## Merge, publish and notify

Merge the release PR using a merge commit. The existing publication pipeline
reuses the successful candidate installers after verifying that the exact second
parent and Git tree match the resulting `main` commit. It runs the full tests,
packages, signs and verifies the release without recompiling platform installers.
A merge means integrated;
shipping is confirmed only after publication and verification of the packages
and signed update feeds.

Ordinary PRs run only affected checks: TV/webOS, installer, Android, preview or
packaging/release tools. Shared dependencies enable every affected group; unknown
paths conservatively enable all checks. Documentation-only changes skip application
checks and Pages builds while keeping the required Linux/macOS status names green.
Once a candidate is frozen (final new version, matching plan, acceptance and notes),
every subsequent candidate commit, including a documentation correction, needs a
complete build so shipped artifacts remain bound to that exact source tree.
Feature branches run tests on PR events; `main` and `release/next` also run tests
on pushes. Preview Pages runs its own focused tests instead of the full suite.

Packaging saves `RELEASE-INVENTORY.json` with the tag, exact source commit,
release PR, included implementation PRs, their issues and delivered summaries.
The asset is included in checksums. Notification scope comes from this frozen
inventory, not from later edits to PR descriptions.

After successful publication and final verification, automation comments on
every included implementation PR, every listed issue and the release PR. A
shared issue receives one comment listing all of its delivered changes.
Excluded PRs receive no shipping notice. Notices describe the delivered portion
and do not close issues automatically.

Retries verify the signed feeds again, bind the release tag and build metadata
to the inventory's source commit, verify its checksum and compare it with the
committed plan. A hidden `<!-- shipped:vX.Y.Z -->` marker identifies each
GitHub Actions bot comment. Existing matching comments are reused/updated;
human comments with the same marker are not touched. A failed target does not
prevent notices to other targets. The workflow reports the missing targets and
fails so the delivery can be retried.

If publication fails, no shipping notice is sent. If notices fail after
publication, the product is already released: do not republish it just to retry
comments. Run **Retry release notifications** on `main` with the published tag.
It shares the publication concurrency lock and only delivers missing/changed
notices. Releases predating this inventory format are verified and skipped.
Never reuse a published version for changed contents; use a new patch release.
Resolve a failed publication before integrating the next release.

After the release merges, fast-forward `release/next` to `main`, clear the plan
for the next cycle, and continue collecting features without a new version.

## Automatic next candidate and recovery

After signed publication passes its public verification, the publishing workflow
starts the next cycle automatically: it advances `release/next` to a commit based
on the published `main` tree, clears only `release-plan.json`, and opens a new
draft PR to `main`. Existing next-cycle work is preserved. A failed publication
does not reset the branch. Shipping notices still run if next-cycle setup fails.

The **Maintain next release candidate** workflow also checks pushes to
`release/next` and supports manual dispatch on that branch. It creates a draft
only when the branch has changes and no open candidate exists; it preserves the
description of an existing PR. Opening the draft does not freeze a version or
establish artifact/TV acceptance. Maintain its scope and validation record as
described above. Actions-created commits/PRs do not themselves trigger other
workflows; subsequent implementation pushes trigger the normal checks.

Repository Actions settings must enable **Allow GitHub Actions to create and
approve pull requests**. These workflows request PR write access and do not
approve or merge PRs. If automatic setup fails after publication, repair the
reported permissions/state and retry with:

```sh
python3 scripts/release-flow.py start-cycle --tag vX.Y.Z
```

For an already prepared next-cycle branch, run
`python3 scripts/release-flow.py ensure-candidate`. Both commands reuse an existing
candidate. The cycle reset verifies the published tag against current `main`,
checks the signed feeds, and uses a non-forced ref update so concurrent work
cannot be overwritten. Never reset or force-push an active preparation branch.

## Initial rollout and protection maintenance

The first installation is an infrastructure bootstrap: merge the workflow,
script, tests and documentation through an installation PR from `release/next`
to `main`, with product versions unchanged. Existing CI must pass. This one-time
step installs the trusted policy before its status becomes mandatory; the
already published product version is skipped by the publication planner.
It does not publish a product release or send shipping notices.

Then an administrator applies and reads back repository merge settings and the
complete branch protection policy:

```sh
python3 scripts/release-flow.py protect
```

This requires repository administration permission. Run it only for intentional
policy setup: it manages the exact required checks and merge methods described
above. Do not require the new status before the bootstrap merge, as its trusted
workflow does not exist on `main` yet. Product releases after bootstrap must
follow the final candidate gate; there is no permanent bootstrap exception.

Workflow changes themselves take effect only after integration into `main`.
Release-branch Android signing uses the persistent preview identity on trusted
pushes; PR workflows receive no signing secrets. Stable feed signing and
publication remain restricted to `main` and the `release-signing` environment.
