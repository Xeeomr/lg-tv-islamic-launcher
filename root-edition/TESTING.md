# Root Edition test plan

For **[v1.2.0 stable / Root 0.3.0](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/tag/v1.2.0)**, start with [installation](../docs/INSTALL.md), [supervisor setup](UPDATES.md) and [current acceptance](../docs/RELEASE-1.2.0-ACCEPTANCE.md). The [candidate test guide](../docs/RC-1.1.0-TESTING.md) is superseded historical guidance. The bounded trials below are explicit developer tests, not a normal installer Keep/confirmation step. Historical acceptance remains tied to its original build.

## Local checks (no TV required)

```sh
python3 -m unittest discover -s root-edition/tests -v
scripts/test.sh
```

The Python suite checks doctor parsing and privacy filtering, manifest validation,
exact-byte rollback decisions, preservation of unrelated fields, tampered plans,
conflicts and refusing to overwrite output files. Preview tests also verify
separate identity, exclusion of personal inventory and helper scripts, rejection
of indirect source files and reproducible content hashes. It does not emulate SAM,
registration-cache updates, power loss or Homebrew failsafe.

Existing launcher/helper tests remain part of the normal suite. Root tooling is
not included in the production IPKs by `scripts/build.sh`.

## Hardware gates (user present)

Before each stage, verify the baseline, off-device backup and independent recovery.
Use one bounded change at a time. Do not count a successful API reply as a visible
or cached-state result.

| Stage | Required evidence |
| --- | --- |
| Manifest registration | Only Home category changed; getAppInfo and actual category-based launch both agree |
| Metadata rollback | Exact original bytes restored; SAM registration matches original; settings untouched |
| Short Home | From an ordinary application screen, returns to real Home while the interception helper is stopped |
| Back Cancel | Back still navigates in-app; Cancel leaves the app running |
| Back exit | Confirmed exit returns to real Home; observe any LG flash |
| Other controls | Arrows, held arrows, OK, volume, pointer, wheel and app launches work |
| Emergency behavior | A documented escape returns to LG and restores routing, with no automatic re-enable |
| Timer/crash recovery | Forced activation/worker failure returns all routing and metadata state to baseline |
| Startup | Normal reboot, quick standby and cold start preserve controls and intended startup |
| Failsafe | Recovery runs with ordinary init.d unavailable; normal operation resumes after leaving failsafe |

Repeat application-exit tests across multiple apps. A dialog intercepting Home is
not the same case as Home pressed from an ordinary app screen. Record the screen,
transaction timing and whether the helper was actually stopped.

## Report results

Use the Root Edition issue template. Include model, firmware, component versions,
which exact stage ran, expected/actual behavior and whether rollback succeeded.
Review/redact doctor output. Do not attach root credentials, pairing tokens,
SSH keys, private backups, firmware images or complete device logs.

## Integrated candidate acceptance record

For the new package, record its `bundle.json` SHA-256 before starting. Earlier
private tests do not count as acceptance of this build. Run these steps together:

1. Inspect existing recovery/updater state before replacing anything; check the
   candidate payload and record its exact source/build. Do not bypass retained
   updater or unresolved-operation checks.
2. Use the supported interactive setup; confirm candidate hashes, service root
   identity, independent recovery and automatic Home activation.
3. Confirm native Home, Back Cancel, confirmed Back exit and other controls with
   the No-root Helper stopped. There is no normal installer trial/Keep step.
4. Exercise Change Home off/on and triple-Home escape; verify LG destinations and
   user-visible control, with no automatic re-enable after emergency off.
5. Repeat the startup/recovery matrix with the user present, then separately
   prepare supervisor upgrade/rollback and Homebrew failsafe tests.
6. Exercise interrupted installation and uninstall only in a prepared test;
   preserve conflicting/unknown state for inspection.

Local tests cover independent installer completion, unknown outcomes, exact
payload hashes, recovery provisioning and the helper stop latch. They cannot
prove delivery of a boot activity on this firmware. Explicit permanent activation is now implemented and tested on one C3; repeat
the lifecycle and emergency matrix on the final release artifact.

## Triple-Home emergency regression matrix

`setup.py emergency-trial --ssh my-tv` is an explicit bounded test, not permanent
activation. Stop the No-root helper first. The command requires the ARM32 input
ABI and the previously observed `LGE M-RCU - Builtin [0]` channel. Input is opened
read-only: no grab, injection or system-library patch.

Three completed Home presses within two seconds request recovery. Each press must
last 40–500 ms; repeats, long holds, another key and invalid sequences reset it.
The observer runs outside the web interface. A separate supervisor monitors its
private heartbeat pipe; input loss, exit or a two-second stall requests verified
rollback. The original independent 60-second guardian remains armed. Failure to
acknowledge observer readiness prevents Home publication. Production helper state
is never changed.

Required supervised tests on the final package:

1. Ordinary Home and navigation still work; triple short Home restores LG Home
   before the deadline without magnification.
2. Suspend only the candidate renderer after verifying its process identity.
   Triple Home must still restore routing. Always resume that exact process in
   cleanup; never suspend WebAppMgr, system UI or the production launcher.
3. Suspend only the diagnostic observer. Its supervisor must restore routing
   before the independent deadline.
4. Confirm the production launcher and explicit helper resumption work afterward.

Local tests exercise the gesture, synthetic input pipe, real stopped/killed child
processes, malformed health messages, startup refusal and transaction-bound
recovery. These tests alone do not establish TV key delivery or frozen-renderer recovery;
see RELEASE-ACCEPTANCE.md for the earlier hardware evidence.
Permanent-mode supervision is a separate path; test it through `enable` or
turning **Change Home** on, using the same emergency and fault matrix. No Keep
confirmation is required by the current normal activation flow.
