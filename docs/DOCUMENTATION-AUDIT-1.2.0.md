# Documentation audit — 1.2.0 candidate, 2026-10-25

Inventory: #60/#59, #61/#55 (partial), #62/#51 (diagnostics only), #63.
The release PR is #58. This audit does not certify hardware acceptance.

- Reviewed the inventory's changes in README, MANUAL_INSTALL, CLI, Root README,
  LG-FIRMWARE-UPDATES and all ten localized guides: en, de, es, pt-BR, fr, it, ko,
  hi, pl and ru. Existing candidate sections cover confirmed Helper start,
  early migration validation, guarded cleanup, sanitized diagnostic fields and
  Homebrew firmware blocking. They now identify 1.2.0 explicitly; these release-branch changes become current
  stable guidance only after the protected merge and verified publication.
- Added RELEASE-1.2.0 with component versions, partial delivery, old-driver and
  app-only update limitations, restart behavior, recovery/rollback boundaries
  and outstanding physical checks. Updated CHANGELOG to distinguish published
  1.1.0 from this candidate and Android README to match the new manifest.
- Reviewed INSTALL, DESKTOP_INSTALL, UPDATES, RECOVERY, COMPATIBILITY, Root
  UPDATES/RECOVERY/TESTING and prerequisites against this scope. Setup commands,
  required privileges, endpoints and recovery-service contracts are unchanged.
  Updated current component tables, download targets and build examples for
  1.2.0. Historical hardware records retain their original versions.
- Updated Home/renewal, updater/service, cytv and Android manifests together
  with release-versions.json. Root service metadata is synchronized; Root app and Root Updater versions are generated from
  release metadata by their builders. Helper and the fixed supervisor retain
  their existing versions and approval boundaries.

Verification commands/results and exact candidate hashes belong in PR #58.
Local package validation must inspect embedded manifests and payload hashes;
final platform builds and signed publication remain separate gates.

The maintainer confirmed checks were normal; RELEASE-1.2.0-ACCEPTANCE records
that confirmation on OLED55C3RLA / 43.21.71 without inventing build details. Updated current stable
version/download guidance and all ten translations, replacing candidate-only
wording while preserving historical acceptance claims. The candidate branch
targets the forthcoming 1.2.0 publication; public main remains the prior release
until merge. Release PR #58 must verify actual publication before announcing
delivery. Relative links/fences and localized inventory checks are recorded
there separately from hardware evidence.
