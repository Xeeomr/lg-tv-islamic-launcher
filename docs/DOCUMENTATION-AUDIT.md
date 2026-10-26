# Documentation audit — 1.1.0 candidate, 2026-10-25

Scope: current maintained usage, setup, update/recovery, build/release guidance
and all ten localized guides on `release/next`. Truth sources are
`release-versions.json`, app/service manifests, actual cytv CLI/operations,
System Updater setup/policy and the checked installer artifacts. The candidate is
unpublished; the public latest release remains v1.0.3.

## Reviewed and updated

| Area | Files / result |
| --- | --- |
| Entry points and release scope | README, CHANGELOG, CONTRIBUTING, LANGUAGES, RELEASE-1.1.0; distinguish candidate versions/Actions artifacts from published stable and dated evidence |
| Setup and maintenance | INSTALL, CLI, DESKTOP_INSTALL, MANUAL_INSTALL, android/README, EDITIONS, COMPATIBILITY, MAINTENANCE and COMPANION-APPS; current versions, Root prerequisites, optional Python and separate supervisor bootstrap |
| Updates and recovery | UPDATES, RECOVERY, Root README/UPDATES/RECOVERY/STATUS/ROLLOUT/DOCTOR, package/runtime READMEs; whole-edition sets, old updater boundaries, retained recovery and refusal of uncertain retries |
| Helper diagnostics and baselines | HELPER-DIAGNOSTICS and native/published/README; distinguish current capture versions from retained immutable historical packages |
| Hardware gates | Root TESTING and RELEASE-ACCEPTANCE current-scope sections; automatic activation has no ordinary Keep step; previous artifact records remain historical |
| Translations | All ten docs/i18n guides: en, de, es, pt-BR, fr, it, ko, hi, pl, ru; candidate/download distinction, versions, optional runtime, system setup and recovery |
| Development and delivery | BUILD, RELEASE-PROCESS, TLS-TRUST and THIRD_PARTY_NOTICES; source requirements, draft build dispatch, optional Python provenance and updateable versus fixed infrastructure |
| Test handoff | RC-1.1.0-TESTING; exact existing five-platform build, macOS package selection, staged remote checks and limits of a modern-TV Python test |

## Reviewed without behavior changes

APP-MANAGEMENT still matches app inventory flows.
DEVELOPER-MODE-BETA retains its actual unrooted-renewal limitations.
TV-WEB-BUILD now also documents the separate Helper Node 0.12 build; Chromium 38 frontend behavior remains unchanged.
RELEASE-FLOW, RELEASE_CHECKLIST and the release PR template already contain the
new recurring documentation gate from #46. They remain the process reference.
Assets/font/icon notices describe their own source/attribution scope.
Vendored ws documentation is upstream material.

Dated release notes, development/lab records, version-specific Root acceptance,
plans/specifications and this audit's older section preserve original versions
and results. They are evidence, not current installation instructions; historical
claims do not certify 1.1.0. No published historical release is relabelled as RC.

## Verification and device boundary

- Independent documentation review and targeted rereview passed after clarifying
  retained Root Updater migrations in both primary guides and all ten languages.
  Local verification passed for 45 changed Markdown files, 353 relative
  links/anchors, balanced command fences and `git diff --check`.
- Checked current command names/options against cytv CLI and setup sources.
  Root supervisor setup is separate from Install. A No-root cytv profile uses
  prisoner SSH; rooted No-root setup instead needs the documented root SSH bundle
  procedure. Existing Root Updater state can block generic reinstallation.
- Existing Actions run 40178512948 passed all five platform builds at source
  acf1acccb0ec0802c993f94a39080859dcda9591. Later documentation edits do not change
  those bytes; final freeze still requires builds at its actual final commit.
- The downloaded macOS ARM64 console passed version/payload checks locally;
  the extracted app passed code-signature verification and offscreen GUI smoke.
- Read-only checks on OLED55C3RLA reported webOS 11.2.0, Python 3.12.6 and Node
  20.12.2. Candidate status/doctor connected successfully and existing recovery
  integrity verified. Root 0.1.11 / Root Updater 0.1.0 remain installed.
  No candidate installation, visible controls, cold boot, upgrade or rollback
  acceptance was performed. A manufacturing-version field is not evidence of
  the currently installed firmware number.

Remaining release work is physical-TV acceptance, the Helper 0.6.19 exact archive
and rollback approval, signed test release-set coverage and final frozen-head
validation. Local Markdown verification covers links/anchors, fenced commands and
whitespace; external LG documentation, OS permission dialogs and every published
historical asset are not re-certified by this audit. The build's existence and
artifact inventory were read through GitHub; no stable feed or publication changed.

---

# Historical documentation audit — 2026-10-24

Historical workspace layout: on 2026-10-25 the `stable/` checkout was moved to
the project root. Current work and Git commands use the project root; references
to `stable/` below describe the layout at the time of this audit.

Scope: the primary `stable/` checkout's 61 tracked Markdown files, plus the local
workspace README. The former release-desktop checkout is now archived at
`archives/2026-10-24-release-desktop/` in the workspace container, including its
uncommitted UI work. All future work uses `stable/` only. Archives and legacy
symlinked checkouts retain their historical contents. Third-party notices and vendored
library documentation are upstream material.

Sources of truth: `release-versions.json`, application manifests, `cytv` setup
and maintenance operations, the current Home settings implementations, build
scripts and dated hardware acceptance records. No TV installation, network
connection or new hardware validation was performed for this documentation pass.

## Findings and corrections

| Area | Outdated or conflicting information | Correction |
| --- | --- | --- |
| Installation | INSTALL covered only No-root and said Root had no supported installer | Shared No-root/Root entry point: requirements, cytv downloads, edition-specific setup, verification, recovery and manual/source paths |
| Project overview | Claimed the described release was No-root only; listed Home 1.1.0 and Helper 0.6.13 as current | Both editions; cytv 0.2.7, Home 1.3.3, Helper 0.6.16, Root 0.1.5 and No-root Updater 0.1.5 |
| Manual command examples | Home 1.2.2, Helper 0.6.13 and Root 0.1.1/0.1.3 filenames/build arguments | Current component versions; retain explicit legacy-version recovery guidance |
| Root overview and acceptance | Current distribution still described as Root 0.1.1/0.1.2 | Root 0.1.5, while keeping the original versions and limits of hardware evidence |
| Home controls | Old activation/exit labels and obsolete Keep confirmation in test instructions | Change Home enables/disables persistent routing; Open LG Home is a one-time visit; normal activation has no Keep step |
| Emergency gesture | Root rollout assumed every No-root Helper used holding Home | Triple Home for current builds; holding Home only for Helper through 0.6.13 |
| Beta renewal | Enable Beta presented as the current button | Current auto-renewal controls, historical label noted; real unrooted renewal remains unverified |
| Localized guides | All ten introductions described the desktop app and language selection as future work | Reference v0.10.3 availability and the shared install guide |
| Maintenance and recovery | No-root webOS CLI commands looked like general instructions | Clearly scoped to No-root source installs, with cytv and Root recovery/removal paths |
| Root doctor/package docs | Claimed no installer existed or permanent enable was unavailable | Distinguish read-only doctor from installer; describe implemented activation and manual updater setup |
| Compatibility and inventory | App discovery described as computer-only; Windows described only as a shell workflow | Document + / Add app refresh, native Windows cytv console, and separate source/OS acceptance limits |
| Build/contribution guidance | Updater described only against v0.7.1; English-only rule conflicted with localized guides | Current component source, separate updater build, localized user documentation and current emergency behavior |
| Historical development notes | Undated-looking blockers could be mistaken for current release requirements | Explicit history boundaries and links to current installation; retain original evidence |
| Local workspace map | stable described as v0.8.1; integrated Root and release checkout were missing | Current distribution and checkout roles |

## Evidence retained and remaining limits

Release notes, changelog entries, dated plans/specifications, RC records and
version-specific acceptance reports keep their original versions and outcomes.
Updating a version label does not certify a new binary. Root cold-power testing,
the intermittent gesture observation, C4 follow-up checks, C5/webOS 26 startup,
Termux end-to-end behavior and unrooted renewal remain subject to their documented
validation limits. Parallel runtime, release metadata and release-desktop changes were preserved.
The final command examples follow the concurrently prepared v0.10.4 metadata;
v0.10.3 remains the introduction point for desktop language selection.

Local file and heading links were checked across tracked Markdown. Three existing
links in `native/app/vendor/ws/README.md` refer to omitted upstream `doc/ws.md`;
these were left in the vendored documentation. External websites, published asset
availability and OS dialogs were not independently revalidated in this pass.

Current guides still use preview terminology in places because the Root package
identity and manual bundle maturity remain separate from model-scoped historical
stable acceptance. Do not remove those caveats simply to match a version number.

## Helper Node 0.12 correction — issue #47

Reviewed the merged candidate setup/runtime guidance after adding Babel, local
polyfills and the legacy WebSocket path to Helper 0.6.19. Updated COMPATIBILITY,
INSTALL, TV-WEB-BUILD, all ten user guides, installer translations, CONTRIBUTING,
THIRD_PARTY_NOTICES and RELEASE-1.1.0. Removed the stale additional Helper
Node 10 requirement from translated system-update instructions; the separate
supervisor/Root Node 8 requirement remains. Historical downloads and immutable
Helper baselines retain their original scope. The existing five-platform test
artifacts predate this fix and must be rebuilt.

Local checks: complete scripts/test.sh and TV payload build; actual official
Node 0.12.2 executes the packaged Helper controller, status/listApps and WSS
regression. Independent implementation review/rereview found no actionable
issues. No LG 49UJ750V input-grab, standby, cold-boot or new rollback acceptance
is claimed. CLI interfaces and unrelated Root/recovery instructions are unchanged.

## Stable publication documentation pass — 2026-10-25

Updated README, all ten localized guides, current installation/maintenance/update references, Root documentation and Android download guidance for v1.1.0 stable. Current downloads point to the final release; the RC testing guide is marked superseded and its old Actions run remains historical. Earlier audit entries, specifications and hardware records retain their original scope.

Added the one-time Home Root GUI restart after supervisor bootstrap when `Denied methods call status` appears. Current C3 evidence and untested paths are recorded in [1.1.0 acceptance](RELEASE-1.1.0-ACCEPTANCE.md); stable publication does not validate every model, Helper 0.6.19 hardware behavior or complete signed system upgrade/rollback.

Verification: checked the documentation diff for whitespace errors, confirmed all ten guides name v1.1.0 stable and contain no obsolete Actions run or Node 10+ Helper requirement, checked changed Markdown relative file links, and scanned current user guides for stale unpublished-release/download instructions. Historical RC/build/audit references remain explicit history. The full local test suite passed in the coordinating publication task; no product source changed in this documentation pass.
