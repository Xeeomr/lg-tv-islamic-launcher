# Root Edition status and evidence

## 1.1.0 stable status — 2026-10-25

[v1.1.0 stable](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/tag/v1.1.0) includes Root 0.2.0, Root Updater 0.2.0, System Updater supervisor 1.0.0 and optional pinned ARMv7 Python. Root **0.2.0**, Root Updater **0.2.0** and System Updater supervisor **1.0.0** were checked on **LG OLED55C3RLA / firmware 43.21.71 / webOS 11.2.0**, using `d344d92` (product contents identical to `4b66951`). Arrows, OK, app launch, Home, Back/Cancel/confirmed exit, volume/mute, triple-Home emergency exit and explicit resume passed. Standby/wake with Emby left open for 70 seconds and the installed-version menus passed; an unavailable update feed showed a friendly message. True cold boot, Helper **0.6.19** on a TV, UK6540PTD, and a complete signed system upgrade or rollback remain untested. Stable publication accepts this limited evidence; it does not validate every model or path.

See [current acceptance](../docs/RELEASE-1.1.0-ACCEPTANCE.md) and [update instructions](UPDATES.md). The dated records below retain their original artifact and hardware scope.

Updated 2026-10-23. Test device: **LG OLED55C3RLA / firmware 43.21.71**.
This file retains historical investigation results. **Current status:** Root Preview
supports explicit permanent mode; software-reboot reactivation, actual launcher
Home/Back routing and sustained health passed on this TV. See
[release acceptance](RELEASE-ACCEPTANCE.md) for current evidence and remaining
final-artifact gates. Earlier statements below about unimplemented features or
long-Home blockers refer to historical builds; triple-short-Home is the current
emergency gesture. This is not a cross-model compatibility promise.

## What passed

- Native short Home opened a diagnostic Home while the normal helper was stopped.
- A paired override of `defaultApps.categories.home` and `idleApp.appId`, together
  with SAM's explicit default Home setting, routed a confirmed Kinopoisk Back exit
  to the diagnostic screen. The user observed no LG Home flash.
- SAM logs identified `closeByAppId` from system UI and `LAUNCH_LASTAPP` selecting
  the diagnostic destination. No key-interception helper was active.
- A real, temporary paired-profile override was automatically removed and all
  three original Home values read back correctly. The normal helper resumed.
- Earlier recovery-service boot tests ran in normal mode and Homebrew failsafe,
  including when ordinary `init.d` startup was unavailable. Those tests did not
  contain the final real-manifest change.
- Local file-publication tests terminated child processes at each staging
  boundary. Recovery preserved conflicting files instead of overwriting them.

## Earlier registration failure and subsequent isolated success

The production Home 1.1.0 manifest does not declare `appCategory: ["home"]`.
System profile and settings readback accepted its ID, but pressing Home caused
SAM `launchDefaultApp` to return **“no default app is set for the category”**.
The diagnostic candidate did declare the category. This is a prerequisite to
investigate, not proof that adding the field alone completes integration.

The production test was rolled back. The user confirmed normal Home and controls
worked. Production launcher metadata and startup configuration were not changed.
Native Back without a flash is **not yet established for an in-place production upgrade**.

A subsequent 60-second trial used the real launcher UI under an isolated diagnostic
ID with the Home category declared. The user confirmed short Home, arrows/OK and
confirmed Back return without an observed LG flash while the helper was stopped.
The independent timer restored routing, the helper resumed and the original
diagnostic package was restored. This does not validate persistent installation
or migration of the production app’s browser storage.

A physical long-Home test triggered emergency recovery and restored the working
setup, but also activated LG screen magnification. The user dismissed it with
Back. A clean long-Home escape is therefore still a release blocker. The local
library callback experiment is not installed and is not part of the preview.

An early test also revealed repeated boot callbacks while already running.
The lab recovery hook now defers such a callback only for a matching live,
time-bounded guardian process; failsafe still requests recovery immediately.
This corrected adapter needs real changed-manifest reboot/failsafe tests before
shipping.

## What remains before a release

- Preserve exact original manifest bytes and ownership; publish only the category
  change and verify the registered app information, not just the file contents.
- Establish a bounded cache-refresh method and its inverse without restarting
  broad system services or disturbing the existing launcher state.
- Recover manifest, registration cache, paired profiles and SAM setting together.
- Repeat short Home, confirmed Back, Cancel, in-app navigation and long-button
  behavior with the real launcher.
- Test normal reboot, fast standby/resume, cold boot, failsafe and interrupted
  installation with the real candidate.
- Provide a documented emergency escape and uninstall route that also restores
  root-mode routing; the No-root long-Home action alone is not that guarantee.

## Scope of public tools

The public doctor is read-only. The metadata planner and tests are local-only.
The separate candidate builder includes an installer and recovery runtime for
supervised hardware tests. It does not enable permanent routing. No Root Edition
IPK is produced by the standard No-root build.

## Release preparation

The [rollout plan](ROLLOUT.md) separates verified isolated routing from remaining
persistent-installation gates. `preview.py` stages a sanitized UI under a new ID
from public source files, with per-file hashes and no services or activation hooks.
Five offline tests cover isolation, private-file exclusion, indirect-source
rejection, reproducibility and refusing to overwrite existing output.

## Current installable candidate

The separate `com.cleanyourtv.root.preview` package now includes a recovery-only
service, host installer, persisted installation journal and bounded routing runtime.
Local tests cover these components. An installed candidate with audited recovery corrections has passed bounded routing
and software-reboot recovery on the test TV. A clean install of the final bundle
still requires acceptance. Persistent enable/confirm are deliberately blocked.

Unlike earlier lab trials, this candidate does not automatically resume the legacy
helper: stopping it sets the same latch as the user's emergency exit. The user must
stop it explicitly before a trial and explicitly resume it after rollback. No
production helper protocol or system library is modified. See [rollout](ROLLOUT.md).

## Integrated recovery preparation — 2026-10-23

Merged main `b182393` (v0.8.1 signed-update fixes). On the C3, the initial candidate
failed closed before Home activation because packaged data and the Homebrew runner
had desktop/world-writable permissions. The recovery service now executes from
private root-owned state using the firmware's Node bootstrap. Homebrew is unchanged.

Activity registration is performed by the root installer with a fixed sender,
not by granting the web service broad management rights. This firmware requires
the compatible ActivityManager URI and explicit list flags; `current:false`
is essential to inspect the stored definition rather than live trigger results.
The owned task and recovery integrity passed readback. All three Home destinations
remained LG; no routing trial ran during this preparation. Boot/failsafe delivery
of the final candidate remains a separate hardware acceptance gate.

## Integrated routing and reboot recovery — 2026-10-23

With the legacy helper explicitly stopped, the isolated real-UI candidate passed
short Home, arrows/OK and confirmed Kinopoisk Back exit without an observed LG
flash. The independent 60-second guardian restored all three original routing
values. The user explicitly resumed the production helper and confirmed controls.

A second trial was interrupted by an acknowledged software reboot. At post-boot
uptime 36 seconds, its journal was already restored, all three Home destinations
were stock, and recovery integrity verified. No manual restore was invoked.
The persistent recovery activity retained its expected creator, callback, trigger
and type. The old guardian's monotonic deadline was still over 3,100 seconds;
this was boot recovery, not expiry of the old timer.

The kernel boot ID did not change on this device despite the uptime reset. Do not
use boot ID alone to classify restarts on this firmware.

After recovery, the user reported a black screen and then returned to production
Home with the Home button. Logs showed Live TV foreground before that press;
production Home and the legacy helper were active afterward. This visual transition
is deferred, not fixed, and does not invalidate the routing restoration readback.

These results apply to the installed candidate with audited corrections through
RC5, not a pristine RC5 installation. They do not establish permanent startup,
power-loss recovery or failsafe delivery for this exact deployment. Persistent
activation remains locked. See [release acceptance](RELEASE-ACCEPTANCE.md).

## Clean installation and removal — RC7, 2026-10-23

The first uninstall revealed that webOS leaves an empty package metadata directory
after a matching terminal removal event. The driver now removes only that fixed
empty directory after checking the terminal package identity, with application
and service directories absent. Nonempty directories, symlinks and unverified
events still stop cleanup. No recursive removal is performed.

RC7 then passed clean installation and normal uninstall on the test TV. Production
Home and helper static-file hashes matched before/after installation, and the
helper remained active. The installer did not change the three system Home values.
Recovery integrity passed after installation. Retained state was archived rather
than discarded. These tests do not activate permanent routing.

## RC7 failsafe recovery — 2026-10-23

After clean installation, a bounded trial selected the candidate in all three
Home destinations, with the legacy helper explicitly stopped. The standard
Homebrew failsafe flag was set and a software reboot acknowledged. The user
observed the Homebrew failsafe prompt. SSH was unavailable as expected; the
readback was collected through Homebrew's emergency Telnet.

At uptime 67 seconds, the same transaction was restored, all three Home values
were stock and recovery integrity verified. The old guardian deadline was 764
seconds on the previous uptime clock; no manual restore was sent. After the
failsafe flag had cleared, another software reboot returned SSH and normal mode.
The recovery journal remained restored and the legacy helper's stop latch was
preserved. After explicitly resuming Home control, the user confirmed arrows, OK and short Home all work after both reboots.

## RC8 local exit UI

The isolated candidate now includes a remote-navigable Settings panel with a
confirmed Exit Root mode action. It calls only recovery, verifies all three stock
Home destinations, then launches LG Home. Requests are serialized and service
errors/timeouts do not count as successful restoration. The candidate receives a
narrow control group for status/restore, without activation or boot privileges.
Local tests cover malformed readbacks, conflicts, duplicate requests, confirmation,
Back cancellation and focus handling. On-TV permissions and visual behavior remain
unverified. This does not close the frozen-UI emergency-escape gate.

## RC10 UI exit accepted — 2026-10-23

RC8 failed the web-process inbound check; RC9 passed inbound but failed the method
security-group check. On this TV WebAppMgr calls as the application ID plus a PID
suffix. Both the inbound role and narrow status/restore client group now include
that app-specific suffix pattern, matching the established updater approach.

In RC10 the user confirmed Exit Root mode opened LG Home. Independent readback at
uptime 1015.42 seconds showed all three stock Home destinations, journal restored,
and LG Home foreground, before the guardian deadline of 1045.87 seconds. No manual
restore was sent. The old helper remained stopped with its latch set. The production
launcher was opened for explicit helper resumption. The user then confirmed
short Home and arrows work in the production setup. This validates the normal UI
exit, not escape from a frozen interface. Permanent activation remains locked.

## Independent triple-Home observer — local candidate

Added an opt-in emergency-trial path. Three short Home presses are observed outside
the renderer, with a separate heartbeat supervisor and unchanged independent
60-second guardian. No key grab/filter, system-library modification or production
helper change. Readiness is required before activation and recovery is bound to the
original transaction. Hardware acceptance, including a suspended renderer, remains
pending. This does not unlock permanent activation.

## RC13 bounded emergency exit accepted — 2026-10-23

On OLED55C3RLA / 43.21.71, three short Home presses restored LG Home on
the first attempt, without observed zoom, both normally and with the separate
candidate renderer stopped by SIGSTOP. The legacy helper was stopped throughout.
The observer does not grab, consume or reinject keys.

RC11 exposed an inactive input node returning ENXIO; discovery now skips only
ENXIO/ENODEV/ENOENT and still rejects ambiguous or inaccessible active channels.
RC12 required a second gesture attempt. A passive trace showed cursor-show 1198
cleared the first Home tap. RC13 excludes that notification from gesture resets;
physical buttons, repeats, long holds and the existing time limits remain unchanged.
The exact recorded failing sequence is now a regression test. Both corrected
passive sequences were recognized (approximately 599 and 522 ms).

Normal trial a477d2ff-0b36-40ec-a8d4-98e30ee8d341 restored all three stock
Home destinations by uptime 2246.19, before deadline 2269.64, with reason `escape`.
Frozen-renderer trial ee8889b2-0bc5-4943-b901-19558a774e51 recorded restoration
at uptime 2306.37 while the renderer was still `T (stopped)`. The separate
resumer then issued SIGCONT because the journal was restored, not because its
45-second timeout expired. The independent Home deadline was 2351.15. The user
confirmed first-attempt LG Home and no zoom in both trials. Subsequent readback
showed stock SAM/defaultApps/idleApp, no active guardian and verified integrity.

Full local suite passed (171 Python tests, 11 additional tests and remaining
script checks). RC13 bundle.json SHA-256: `f85fb75dc77cec7a867fdb927711ddb560e4d292161dcc53370e9e2edd9f5e56`.
The installed candidate includes locally migrated packaged preferences; private
inventory and raw device logs are not published. RC12 artifacts/state are retained
for rollback. Production launcher and helper files were not modified.

This closes the **bounded-trial** frozen-UI escape check on this model. Permanent
observer lifecycle, persistent activation and final-bundle lifecycle acceptance
remain separate gates; `hardware_validated` and permanent activation stay locked.

## Persistent-mode lifecycle foundation — local only

The intent state machine, private atomic state store and independent two-second
lease policy are implemented and locally tested. Emergency/fault/failsafe intent
is disabled before recovery; a healthy explicitly confirmed trial is required
before retaining enabled intent. Boot restores prior routing before requesting
activation; interrupted startup disables retry. Stale generations and attempt
tokens cannot authorize a later transition.

An actual subprocess test stops the heartbeat publisher with SIGSTOP while a
separate guard detects lease expiry. This validates the local guard policy, not
on-TV persistent recovery. These modules are deliberately not in the install
bundle and are not called by existing RC13 paths. The production TV was untouched.
Transaction binding, device orchestration and boot/UI integration remain required;
persistent enable/confirm remain locked. See the dated lifecycle plan.

## RC14 intent-bound trial integration — 2026-10-23

A separate `intent-trial` command durably binds lifecycle generation/attempt to
its routing transaction before publication. Gesture, timer and explicit restore
use this binding to disable intent before RC13 recovery. Successful recovery must
match the journal baseline across SAM and both profile destinations. Boot dispatch
preserves a live bounded guardian, restores after a new kernel start/failsafe,
and does not adopt a later unrelated legacy trial. An interrupted first start can
be reconciled only after independently verifying stock and no unresolved evidence.

Local integration tests use the real recovery adapter and actual temporary profile
files, with only the TV service replies substituted. They cover foreign routing,
concurrent stop, disk reload, failed binding before publication and readback drift.
Full suite passed: 227 root Python tests, 11 setup tests and remaining scripts.
Two complete builds were byte-identical; RC14 bundle.json SHA-256:
`edfd23229df3fe0a918ff1eb2a385d55569a95d4578e0c5ac22a368bf25aa8d8`.

This bundle retains the independent 60-second deadline. It does not renew a lease
or enable a permanent profile; `enable`/`confirm` remain locked. The renewable
lease policy is still local and not included in this install. Permanent observer
lifecycle, promotion/confirmation UI and final device acceptance remain required.

## RC15 permanent lifecycle implementation — 2026-10-23

Implemented explicit enable/transaction-bound confirmation, volatile input-loop
leases, independent guardian continuation and reciprocal guardian pulse checks.
Confirmed intent resumes only after verified boot recovery and fresh guarded
activation. Failsafe, interrupted startup, emergency exit and faults disable intent.
Settings now provides Try Root mode / Keep Root mode / active status and Exit.
Production app/helper files are untouched; candidate identity remains isolated.

Full local suite passes (314 Python root tests, 11 setup tests and all JS/native
checks). Includes a stopped real publisher with an independently running health
adapter, deadline promotion rejection, and publication-during-read regression.
Independent review found the timestamp race; it was reproduced and fixed.
RC15 hardware acceptance is pending; permanent mode is not a public release yet.

## RC18: Homebrew normal-startup gate (2026-10-23)

RC15–RC17 did not retain Root routing after reboot. Local review of Homebrew
0.7.3 `services/startup.sh` found that its failsafe flag is also set during normal
startup. Normal startup runs init.d, then waits ten seconds before clearing it;
real failsafe skips init.d but also clears the flag later. Absence of the flag
alone is therefore not proof of normal startup.

RC18 restores the recorded stock route before waiting. A dedicated, owned
`50-clean-your-tv-root` hook writes a private current-kernel-boot marker and
returns immediately. Reactivation requires both that marker and a cleared flag;
a bounded timeout disables intent. The independent recovery activity still runs
when init.d is skipped. The hook never activates Home or changes Homebrew code.
Its ownership receipt is retained for repeatable removal and rejects name/content
collisions. Boot decisions are recorded in private `boot-decision.json`.

Local verification: 349 Python tests pass, including real-failsafe flag clearing,
normal startup ordering, missing/stale marker, private marker storage, hook
collision/removal, and restore-before-gate ordering. Hardware reboot acceptance
is pending; these results do not constitute release approval.

RC18 hardware result: normal-startup marker was present and bound to new boot
`7bff50ef-5612-4f23-b295-e0eabf1833b3:1792740634`. Boot audit at uptime 28.81s
recorded *prior* intent already `recovering`, `enabled:false`, generation 1.
Therefore this reboot did not exercise successful reactivation: shutdown had
revoked intent before the boot callback. At 46.22s all three Home routes were
stock and the old transaction `62755c54-da0b-482c-aa80-eee35461c084` was restored.
The emergency log reports input ENODEV / observer_exit. Root cause of the missed
shutdown evidence is still unresolved; do not attribute this run to the failsafe
gate or weaken watchdog behavior. Production launcher and helper were relaunched
through their normal application entry points after the test.

## Shutdown lifecycle correction (local validation, 2026-10-23)

The RC18 audit narrowed the failure to shutdown, before boot recovery. Two
mechanisms now address the observed timing and a reproduced recovery race:

- A separate 50 ms observer recognizes a newly created, root-owned, non-writable,
  single-link `/tmp/poweroff_reason` containing exactly `poweroff_reason=remoteKey`.
  A file present when observation begins, symlinks, crash/unknown reasons and
  untrusted files do not authorize preservation. It does not depend on a working
  systemd RPC. Publication retries are bounded; evidence remains boot/transaction
  scoped and expires after five seconds until accepted.
- Once accepted for an already confirmed mode, the coordinator persists `stopping`
  before routing RPCs. Restoration timeout/retry cannot reclassify the same shutdown
  as an input fault after the short evidence window expires. Explicit user exit
  still disables intent. A new boot restores baseline and requires normal-startup
  evidence plus new input/guardian health before reactivating.

Regression coverage includes a blocked systemctl call, transient evidence-write
failure, restoration timeout followed by expired evidence, explicit escape after
shutdown classification, and identical input failure without shutdown evidence.
The last case disables intent and does not restart it on boot. Hardware acceptance
of this correction is still required; no release-success claim is made here.

RC19 software reboot successfully restored active generation 2 and all three
candidate Home routes. The audit recorded prior phase `stopping` and normal gate
completion at uptime 32.96 s. A later safe rollback around uptime 62 s exposed
an independent lease arithmetic defect: `(issued + 2) - issued` can exceed two
by floating-point rounding (for example issued=62.4). Both validators now compare
`issued < expires <= issued + 2`, matching the producer without a tolerance or
longer timeout. Publisher/reader and guardian boundary regressions pass, including
rejection at exact expiry. Full local suite: 361 tests. Hardware persistence
beyond the original minute remains the next acceptance check.

Boot orchestration also had a locally reproduced overlap: while one boot callback
waited for the normal-startup gate, a duplicate callback could treat its `starting`
intent as an interrupted attempt and disable it. A separate root-owned flock now
covers the whole boot dispatch; duplicates return `boot-in-progress`, while user
restore keeps its independent operation path. Boot exceptions are recorded for
diagnosis. Full suite with this regression: 362 tests. This is a proven local race;
the preceding device failure did not retain the exception needed to establish it
as that specific failure's cause.
