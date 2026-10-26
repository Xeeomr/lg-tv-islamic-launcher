# Root Edition release acceptance

Distribution references reviewed 2026-10-24; hardware records below are dated 2026-10-23. Target: LG OLED55C3RLA, firmware 43.21.71.

## 1.0.0 bounded verification

The 2026-10-24 supervised Root 0.1.10 / cytv 0.2.14 session passed installation,
remote controls, standby/wake and emergency exit on C3, with independent LG Home
readback. Explicitly approved removal also passed. See the [1.0.0 validation
record](../docs/RELEASE-1.0.0-VALIDATION.md) for exact hashes and scope. Historical
records below retain their original artifact versions and limitations.

## 2026-10-24 startup correction

The installed shutdown/observer runtime correction was tested with two webOS
firmware-managed restarts using reason `remoteKey`: bootManager selected
`com.cleanyourtv.root.preview` as its first application, with fresh guarded routing
active after boot. The user confirmed normal operation. The runtime sources
match those included in Root 0.1.5; this is not an acceptance run of every
new installer binary or of direct AC power removal. A direct `systemctl reboot`
can still be treated as an input fault and disable Home control.

## Current release boundary

The implementation supports protected trials and explicit permanent activation.
The published v1.0.3 distribution contains **Root 0.1.12**; the unpublished
1.1.0 candidate contains **Root 0.2.0 / Root Updater 0.2.0**, optional Python
bindings and the separate System Updater bootstrap. See
[candidate notes](../docs/RELEASE-1.1.0.md) and
[current test steps](../docs/RC-1.1.0-TESTING.md). New candidate hardware acceptance
is pending. The 0.1.1 record describes earlier update evidence. See [scope and limitations](ROOT-0.1.1.md). Root Stable 0.1.0
routing/lifecycle evidence below applies to its earlier fixed artifact.
No blanket hardware certification is claimed for the final public artifact.

Latest evidence (RC19 with atomic-read correction): actual launcher app selection,
short Home and confirmed Back exit without observed LG flash; over eight minutes
of active health; normal software reboot with automatic reactivation and fresh
protections beyond the new trial deadline. User confirmed navigation and app exits
after that reboot. See [current validation record](../docs/development/ROOT-RC19-VALIDATION.md).

Earlier RC10/13–15 tests established normal UI exit, triple-Home escape (including
a frozen renderer) and persistent-mode escape. Earlier candidates passed recovery
in failsafe. These are useful regression evidence, not a substitute for repeating
the final package's lifecycle matrix.

The fixed-build session below supersedes earlier pending lifecycle gates.
Cold-power testing is deferred and the isolated first-attempt gesture miss remains
unexplained. Stable is a model-scoped release designation, not blanket hardware
certification. Do not set `hardware_validated` or `public_release_ready` globally.

## Fixed-build stabilization session

[The fixed-build acceptance record](../docs/development/ROOT-STABLE-ACCEPTANCE.md)
now documents matching installed/build manifest identity, UI and emergency exit,
instrumented frozen-renderer escape, quick standby and controls, genuine failsafe
with normal init.d skipped, clean uninstall/reinstall, preserved production hashes,
Kinopoisk and VK Video navigation/exit, and observer-stall recovery in 2.414 seconds.
Cold-power testing was explicitly deferred by the user. One initial second-attempt
gesture report was not explained by a trace; later captured triples and the
instrumented repeat passed. Keep that observation visible rather than claiming
it was fixed. The user selected the scoped stable designation with these limitations retained.

## Root Settings updates — isolated hardware validation

On 2026-10-23 the C3 passed a real Settings update from 0.1.0 to 0.1.1 and
automatic timeout rollback from 0.1.2 to 0.1.1 under isolated lab identities.
The complete 30-app/five-input profile, settings and tile order matched after
both operations, and the user confirmed the physical remote and application
launch. Pre-existing application manifests, ordinary Home profile and LG routing
were unchanged. See the [update validation record](../docs/development/ROOT-UPDATES-TV-VALIDATION.md).
Production artifact acceptance, updates from active Root routing and interrupted
update/reboot cases remain separate gates. This does not change global
`hardware_validated` or `public_release_ready` flags.

## Historical candidate records

The sections below record what was known at each earlier RC. Statements about
unimplemented or locked permanent mode describe that historical build only.
Use [installation instructions](ROLLOUT.md) for current commands.

## Completed on the corrected installed candidate

- Native short Home and confirmed Back exit to the real launcher UI, without an
  observed LG flash, with the legacy interception helper stopped.
- Arrows and OK during the bounded routing test.
- Independent timer restoration of SAM Home and both system-profile destinations.
- Software reboot during an active trial: automatic restoration, no manual restore.
- Recovery activity persisted across reboot; recovery integrity passed.
- Explicit production helper resumption; Home returned to the production launcher.

The TV candidate received audited corrections through RC5. RC7 subsequently passed clean installation and normal uninstall; routing and
reboot evidence still applies to the earlier corrected deployment. No cross-model support is implied.

## Ordered remaining work

| Priority | Gate | Pass condition |
| --- | --- | --- |
| 1 | Final bundle identity | Reproducible build, passing local suite, retained hashes, no private inventory |
| 2 | Clean install and removal | Passed on RC7; production static hashes unchanged and helper active |
| 3 | Failsafe recovery | RC7 automatic restoration passed; normal mode and arrows/OK/short Home confirmed by the user |
| 4 | Input/lifecycle matrix | Cancel and in-app Back, held arrows, volume, pointer/wheel, quick standby and cold boot on final bundle |
| 5 | Permanent-mode escape | Validated exit restores routing without zoom, reactivation or dependence on a reachable host |
| 6 | Permanent activation | Implement and accept after recovery/escape gates; preserve exact original state |
| 7 | Public release | Attach accepted artifacts and hashes; document install, restore, uninstall and limitations |

The host `restore` command and bounded deadline are the candidate's current escape
routes. Long Home is not a promised Root-mode emergency exit. System-library
patches and boot animations are outside this release.

## Normal UI exit

RC10 passed Settings → Exit Root mode → Confirm exit on the C3. Readback and LG
Home foreground were confirmed before the independent deadline. The helper stop
latch remained set. A frozen-UI emergency path is still a separate gate.

## Deferred observation

After software-reboot recovery, Live TV became foreground and the user reported a
black screen; Home returned to the working launcher. Investigate separately.
Do not describe this as fixed or as evidence of a launcher crash.

## Hardware records

Record bundle hash, installed payload differences, model/firmware, initial routing,
helper state, transaction, outcome, recovery readback and user-visible result.
Keep private logs and credentials out of the repository. An API success alone is
not acceptance.

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

Production restoration after RC13 was confirmed by the user: short Home from
Kinopoisk and launcher arrows work. The first UI-triggered helper restart stopped
safely with `FAIL source-held`; after the user released all keys, an explicit
normal helper application launch reached READY. No safety latch was bypassed and
no production helper code was changed.

## RC14 intent-bound escape — 2026-10-23

On OLED55C3RLA / 43.21.71 the user confirmed first-attempt triple-short-Home exit
without zoom. At uptime 3802.40, before deadline 3832.55, transaction
`afabfc61-62e7-415a-b25f-bc01e81a762e` was restored with reason `escape`.
Readback showed all three stock Home destinations, no active guardian and verified
recovery integrity. The separately persisted intent was disabled and its binding
marked restored. Replaying the boot entry point in the same boot returned restored
without activation. This is not evidence of a reboot or permanent-mode acceptance.

A second RC14 transaction `e6b4e33a-82b1-44b5-8854-bfbbf790e426` was left
untouched. At uptime 3886.89 it was pending with deadline 3891.95; at 3909.14
the independent guardian had restored all three Home destinations, disabled the
intent and marked the binding restored. No manual restore command was sent.
The working helper was subsequently launched normally after released-key and
baseline checks; its relay reported READY and production Home was foreground.
No production helper code or control latch was edited directly.
The user then confirmed production short Home, arrows and OK work as before.

## RC15 local permanent-mode candidate — 2026-10-23

Implemented explicit promotion, volatile two-second health leases, reciprocal
watchdog pulses, boot restore-before-restart and settings controls. Full local
suite passes: 314 Root Python tests, 11 setup tests and all JS/native/update checks.
Independent code review identified a timestamp/read race; a failing regression
was added and the watcher now samples validation time after reading a lease.

Reproducible bundle.json SHA-256:
`a7d1db3a3da27123a8dc860ae45d3380c849dea28d714954b1ab46f55101b0f7`.
RC15 device acceptance is pending. Do not inherit RC14 bounded acceptance as proof
of permanent operation. Production launcher/helper remain separate.

RC15 device results: user confirmed Settings → Keep Root mode displayed active.
Transaction d13dcd2c-df65-4a1a-9e89-d50c855a6c5a remained active at uptime
5198.88, beyond its original deadline 5177.34, with fresh input/guardian pulses.
Triple Home then restored all three stock destinations and disabled intent.

The next confirmed transaction 041b15c5-a42d-42a3-8e1f-0066fe0bc378 did not
resume after approved reboot: kernel input removal raised ENODEV during shutdown,
which correctly triggered the existing fault policy but incorrectly erased the
user's reboot intent. Stock recovery was verified; permanent reboot acceptance
failed. RC16 distinguishes PID 1's independently observed `stopping` state from
ordinary input failure. Explicit escape and UI exit still disable intent. Unknown
or unavailable manager status remains fail-closed. RC16 device test pending.

RC16 reboot still disabled intent. A subsequent read-only shutdown probe clarified
that input did NOT disappear before PID 1 entered stopping: at uptime 151.317 the
manager reported stopping; a query timed out at 151.872; input ENODEV followed at
151.988; stopping was readable again at 152.630. The synchronous query could miss
the valid shutdown state due to that transient timeout.

RC17 adds a background manager observer with a root-private volatile five-second
record bound to boot identity and transaction. Only an actual stopping response
creates it. Expired, foreign-boot or different-transaction records are rejected;
explicit escape/UI exit still disable intent. Full local suite: 338 Root Python
and 11 setup tests, plus JS/native/update checks. RC17 hardware result pending.
