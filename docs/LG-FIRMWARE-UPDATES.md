# LG firmware update blocking (since 1.2.0)

This optional Root Edition control is included in 1.2.0 (Root 0.3.0). Open **Home settings → LG firmware updates**. It controls LG's TV
firmware updates, including firmware security updates. Clean Your TV's own
**Software updates** screen remains separate.

## Use and limitations

- Homebrew Channel must be installed, running with root access, and expose its
  configuration API to Home. If unavailable or denied, the switch is disabled;
  check Homebrew Channel and use **Check status**. No permission escalation or
  alternate system-file modification is attempted.
- The switch shows Homebrew's saved `blockUpdates` preference. A fresh read
  verifies each change. It does **not** certify that update servers are blocked
  now, that an update was not downloaded, or that root will survive an update.
- Changes take effect when Homebrew's startup script runs on a real TV restart.
  Use Homebrew Channel's restart action; ordinary standby/wake may not run it.
  Turning the setting off also needs a restart to remove Homebrew's existing
  boot-time overlay. Other tools/router rules can still block updates.
- Some root startup methods run after LG's first update check. Notifications can
  therefore remain even with the preference on. Network blocking on your router
  may be necessary. Existing downloaded updates and notifications are not deleted.
- Homebrew owns the setting. Changing it here changes the same preference shown
  in Homebrew Channel. It remains after removing or rolling back Clean Your TV;
  use either interface to turn it off and restart. No previous Homebrew setting
  is silently restored on uninstall.
- After an error, timeout or concurrent change, check status before retrying.
  A command may have succeeded even if its reply did not arrive. The UI does not
  automatically repeat a failed write. A stale view is re-read before writing;
  Homebrew does not provide a cross-client compare-and-swap transaction.

This control uses the existing public
`org.webosbrew.hbchannel.service/getConfiguration` and `setConfiguration` APIs.
Only `{blockUpdates: boolean}` is written; SSH, telnet and failsafe flags are
never sent. There is no new private recovery-service API, persistent CYTV flag,
daemon or mount. Compatible app updates can deliver the UI without changing the
pinned recovery-service contract; a denied/unsupported Homebrew API stays
unavailable. The TV's own auto-update setting is distinct and is not modified.

Upstream evidence: [configuration API](https://github.com/webosbrew/webos-homebrew-channel/blob/main/services/service.ts),
[startup implementation](https://github.com/webosbrew/webos-homebrew-channel/blob/main/services/startup.sh),
and [early update-check limitation](https://github.com/webosbrew/webos-homebrew-channel/issues/96).

## Acceptance and further device checks

Automated tests cover strict boolean values, partial configuration writes,
missing/non-root/denied API, rejected/malformed replies, stale preference,
concurrent operations, uncertain write outcomes and readback. UI checks cover
remote navigation, focus return, delayed replies and ten translated catalogs.
These do not establish physical TV compatibility.

On a rooted TV, record model, firmware, Homebrew version and startup method.
Compare Homebrew's preference before/after each direction. Confirm SSH, telnet,
failsafe, Home routing, emergency exit and volume/mute are unchanged. Test a
real restart separately from standby, inspect effective update blocking without
starting a firmware installation, and record any remaining update prompt.
Test preference changes from Homebrew while this screen is open. Verify a
supported Home update/rollback and that the preference remains Homebrew-owned.
See the [1.2.0 acceptance record](RELEASE-1.2.0-ACCEPTANCE.md) for the
maintainer confirmation and its evidence limits. Original-device checks remain
separate.
