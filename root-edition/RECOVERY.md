# Root Edition recovery contract

## 1.1.0 runtime and update recovery

Current setup can use a separately provisioned pinned ARMv7 Python when eligible
TVs lack suitable Python 3.9+. Root, boot recovery and independent updaters retain
verified interpreter bindings; status/restore/removal do not download replacements.
Keep referenced `/var/lib/clean-your-tv-python/` slots even after app removal.
Node.js 8+, root/Homebrew services, loader/libc and input requirements remain.
See [runtime limits](../docs/OPTIONAL-PYTHON.md).

The independent System Updater restores whole-edition release sets and profiles;
it needs explicit computer bootstrap. Unknown installer outcomes or interrupted
removals retain evidence and stop unsafe replay. Use `cytv status`, then the saved
connection's recovery/removal flow. New physical-TV acceptance is pending;
see [current updates](UPDATES.md). The design notes below do not extend historical
hardware claims to the current release.

Historical metadata-recovery design. References to a future installer and open
implementation gates below describe the original investigation. Current Root
uses a separate package and implemented recovery runtime; it does not patch the
ordinary launcher manifest as an installation step. For current operations use
[Root controls and recovery](ROLLOUT.md#controls-and-recovery),
[release acceptance](RELEASE-ACCEPTANCE.md), or the [shared installation guide](../docs/INSTALL.md).
Keep this document as design history, not a manual TV modification procedure.

## One transaction, four things to restore

1. **Launcher manifest:** exact saved bytes, file owner, mode and identity. Only
   `appCategory` may be changed to add `home`; entry point, app ID, version, startup
   flags and settings remain intact.
2. **Registration cache:** SAM must report the original category state again.
   Restoring `appinfo.json` alone is insufficient proof.
3. **System profiles:** remove only the owned trial override, rescan through the
   validated route, and read back `defaultApps` and `idleApp`, preserving unrelated
   fields such as AOD.
4. **Explicit default Home:** restore the saved supported SAM destination and
   verify it independently of profile readback.

Restore routing to a known available destination before reverting or removing the
candidate's registration. If recovery encounters an independently modified file,
preserve it and report a conflict. Never restore a whole old system directory over
newer data or delete a file based only on its name.

## Before activation

- Capture and validate the baseline, installed app registration and conflicting
  profile layers. Keep backups off the TV as well as in the recovery journal.
- Validate the recovery path in the exact root environment. UID 0 alone is not
  proof that the service survives reboot or runs in Homebrew failsafe.
- Save the transaction and file identities durably before publishing a change.
- Start an independent bounded guardian and require its transaction-specific
  readiness acknowledgement. Stale timers must not act on a newer transaction.
- Keep the existing helper stopped only during a bounded routing test, with a
  separately verified path to resume it after recovery. Never run two interceptors.

## Recovery triggers

Deadline expiry, failed readback, activation failure and a new boot must restore
the baseline. Failsafe must recover even if ordinary startup scripts are skipped.
Repeated activity callbacks in the same boot must not accidentally cancel a valid
trial; any deferral must be tied to a live matching guardian and short deadline.

A watchdog or long-button escape must not silently re-enable itself after the user
stops it. A permanent Root Edition needs its own escape design; the existing
No-root helper stopping does not automatically reverse a system profile.

## Offline metadata preparation

From a **local copy of the actual manifest**, not a `getAppInfo` response:

```sh
python3 root-edition/metadata.py --input appinfo-copy.json --output metadata-plan.json
python3 -m unittest discover -s root-edition/tests
```

The plan contains exact original/candidate bytes and SHA-256 hashes. It is a local
backup artifact; keep it private. The planner refuses existing output files.
`metadata.recovery(current_bytes, plan)` returns exact original bytes for the known
candidate, returns `None` if already original, and raises a conflict for any other
contents. It never writes a TV file or refreshes a registration cache.

A valid local plan is **not permission to apply it** and is not a complete recovery
system. The live metadata/cache transaction remains a release gate.
