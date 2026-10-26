# Root candidate runtime

Install these Python files under `/var/lib/clean-your-tv-root/runtime` as root-owned files without group/world write permission. Python 3.9+ and `/usr/bin/luna-send` are required; Root setup also requires TV Node.js 8+,
Homebrew services and supported ARM32 input. With system Python, invoke
`/usr/bin/python3 /var/lib/clean-your-tv-root/runtime/cli.py COMMAND` as root.
For a managed-runtime installation use its retained verified interpreter binding;
do not substitute a missing system interpreter or change global PATH.
[Optional Python](../../docs/OPTIONAL-PYTHON.md) is provisioned only by setup,
never by status, restore or removal; referenced runtime slots remain retained.

- `status`: read actual system profiles and independent Home setting, journal and recovery integrity.
- `trial`: activate **com.cleanyourtv.root.preview** for at most 60 seconds using a detached rollback guardian. Refuses any unresolved journal, unexpected baseline, missing Home registration or missing recovery provisioning.
- `restore`: conflict-checked removal of only the owned override, rescan, restore stock Home and verify the full original profiles. Retries bounded transport failures. Exit 2 means recovery is unresolved; preserve state for retry/investigation.
- `boot`: restore the previous routing transaction first. A confirmed active intent may then start a fresh protected transaction and open the candidate. Failsafe or interrupted startup disables intent; duplicate callbacks preserve only a healthy matching guardian.
- `enable`: activate persistently after automatic input, guardian and routing checks; requires the old helper to be stopped. Failed readiness restores LG Home. No user confirmation or timed session.
- `confirm TRANSACTION`: diagnostic promotion of that exact live trial. Requires fresh input/guardian heartbeats, effective candidate routing and at least five seconds before rollback. No confirmation means automatic rollback.
- `intent-trial`: diagnostic intent-bound trial, useful for regression checks; separate from user activation.

The independent updater uses root-only internal commands `suspend-update TX`,
`finish-update TX` and `abort-update TX` with its exact 32-character transaction
identity. Suspension preserves the prior confirmed Home preference before
restoring LG Home. After automatic application-health success, finish restores an
enabled preference only when the suspension snapshot, boot and reservation still
match and failsafe is absent. Activation uses the normal guardian/input checks.
There is no manual post-update confirmation. Abort never activates Home.

Private `update-home-resume.json` records the suspension and one activation
attempt; `update-home-cancel.json` records explicit/emergency off without waiting
for the update lock. Reconciliation never replays an uncertain activation. A
fresh reservation starts a new suspension cycle, including a later rollback of
the same update. Successful No-root updates preserve their independent Helper
state instead of using this Root runtime.

A confirmed normal shutdown retains the Home override, generated profile and transaction binding so bootd can select Clean Your TV as its first app. Startup recovery still restores the old transaction before arming fresh health protection. Explicit exit, input failure without a shutdown signal, and failsafe recovery restore LG Home.

Boot recovery rearms protection without issuing a second Home launch after
readiness. Native boot presentation uses the retained profile; reopening Home
late would interrupt an app the user already selected during startup. Manual
enable and ordinary Home routing retain their explicit user-requested behavior.

Runtime state is `/var/lib/clean-your-tv-root`; owned profile is `/var/webos-profile/override/clean-your-tv-root.json`. Both directories must be root-owned and not group/world writable, and must reside on the same filesystem for crash-safe hard-link publication. Runtime never edits app files, stock libraries, zoom behavior, or the existing no-root launcher.

Recovery provisioning is `recovery-provision.json`: version 1, mode `recovery-only`, absolute `boot_callback`, and `files` mapping absolute callback and every runtime Python path to its SHA-256 hex digest. All files and ancestors must be trusted. The installed callback must invoke the fixed runtime `cli.py boot`. The installer finalizes this manifest only after boot activity registration is verified. A valid manifest establishes installed-byte integrity, not hardware acceptance.

Device-specific assumptions requiring hardware acceptance: webOS systemprofile getProfiles/debug/rescan methods; defaultApps and idleApp schema; settingsservice general.defaultApps readback representing SAM's setting; applicationmanager setDefaultApp; appCategory home registration; stock app `com.webos.app.home`; Linux `/proc` guardian identity; `/var/luna/preferences/webosbrew_failsafe`; filesystem durability; boot activity delivery under reboot and failsafe. Trial requires all three original routing values to name stock Home and idleApp.support true.

Local tests exercise policy, real file ownership/conflict handling, subprocess timer readiness, abrupt publication process death, provisioning gates, isolated identity and restoration. They do not establish TV boot, remote Home/Back routing or power-loss behavior.

## Existing No-root helper

Trial preflight refuses an existing controller PID marker or running known No-root relay, including ambiguous stale markers. It rechecks before publishing the profile. It never edits the helper's control or blocked files and never relaunches that app. The legacy `stop` command creates the same blocked latch as a user disable, while manual relaunch clears it; an automatic stop/relaunch cannot preserve user intent. Explicitly stopping the old helper is therefore required before this candidate's trial; it remains stopped afterward. Transparent pause/resume requires a separate transaction-aware helper protocol and is not provided here. Do not launch the helper during a Root trial.

During hardware acceptance, use three short Home presses within two seconds to
disable the current No-root helper first (through 0.6.13: hold Home about two seconds). After Root restoration, verify stock routing and explicitly use the existing helper button to re-enable No-root if desired. Neither runtime nor uninstaller removes stale controller markers automatically; investigate stale state rather than blindly deleting it.

## RC15 persistent candidate

Settings exposes Turn on Home control. Activation automatically records durable
intent after readiness checks; it does not disable watchdog protection. The
internal startup deadline remains a recovery backstop until readiness succeeds.
The independent guardian then uses a renewable two-second input-loop lease. The
supervisor checks the guardian's own pulse. Volatile health files live under a
root-owned `/tmp/clean-your-tv-root-health`; frequent heartbeats do not write flash.

Three short Home presses within two seconds or Home settings → Return to LG Home disable
intent before restoring original routing. A fault does the same. No-root helper
is never automatically resumed. A later explicit enable is required after a fault,
failsafe or emergency exit. Installation alone does not enable Root mode.

Permanent operation is implemented in RC15 but final-bundle on-TV confirmation,
reboot, failsafe and fault-injection acceptance remain pending. Build metadata
continues to say `hardware_validated: false` and `public_release_ready: false`.
The historical provisioning schema name `recovery-only` remains an integrity
receipt format, not a promise that a confirmed boot intent cannot activate Home.
