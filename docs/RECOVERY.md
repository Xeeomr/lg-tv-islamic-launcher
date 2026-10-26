# No-root controls and recovery

## Interrupted setup or removal in 1.1.0

Run `cytv status` with the same saved TV/profile before retrying. The installer
can offer to finish a previous No-root removal through the retained verified
flow with a separate default-No confirmation, including with `--yes`.
An uncertain removal is not resubmitted automatically. Keep receipts and save
`cytv doctor --report` diagnostics when verification cannot establish a safe step.
Status, restore and removal never download new Python; Root recovery uses its
verified interpreter binding and retains referenced managed runtime slots.
See [CLI interrupted operations](CLI.md#interrupted-operations).

For either edition installed with cytv, use its **Check TV status**, restore and
diagnostics actions first; see [CLI recovery](CLI.md#interrupted-operations). Root
routing recovery uses the [Root controls and restore commands](../root-edition/ROLLOUT.md#controls-and-recovery).
The webOS CLI commands below apply to No-root source installations.

For a **one-script installation**, run CLI commands from the repository folder.
The CLI is local; expose it in your current terminal:

```sh
export PATH="$PWD/build/tools/node_modules/.bin:$PATH"
```

The automatic device name is `clean-your-tv-<IP-with-dashes>` (for example
`clean-your-tv-192-168-1-50`), or the `DEVICE` override you supplied. Replace
`-d lgtv` in the commands below with `-d clean-your-tv-192-168-1-50`, using your
actual device name. Manual installations below use the profile `lgtv`.

- **Arrows / OK:** select and open apps. Hold OK on a tile to reorder it.
- **Short Home:** return to the launcher while the helper is active.
- **Press Home three times within two seconds:** release interception and open LG Home.

Triple Home is an emergency stop, not a factory reset. It preserves preferences but
leaves a persistent stop flag. Automatic startup respects that flag. To resume,
open **Home Helper** manually from LG's app list, or run:

```sh
ares-launch -d lgtv com.local.nativehome
```

Opening the launcher alone does not clear the stop flag. If you trigger triple Home by
accident, manually starting the helper restores interception. The current **Change Home** switch controls ordinary Home routing; **Open LG Home**
only visits LG Home once. Neither replaces checking recovery state after a fault.
Helper versions through 0.6.13 use holding Home for about two seconds instead
of triple Home.

If the helper fails, heartbeat timeouts and process cleanup release the physical
remote. Do not repeatedly clear stop flags after a failure: use LG Home and report
the issue. Keep the launcher assigned to a Quick Access key as another entry point.

If a quick power cycle leaves tiles visible but unresponsive, try triple Home and
check arrows on LG Home. Report the helper version and whether it reproduces with
the helper stopped. Version 0.6.12 avoids a duplicate launch after system restoration.

Opening Home does not start or restart Home Helper. This avoids a native launch
that can cause webOS to close the visible Home on some TVs. The existing boot
activity still starts the helper automatically when permitted. After a helper
exit (including exit code 25 without a stop flag), open **Home Helper** manually
to restore control; merely reopening Home will not restart it.

After standby, Home recovery watches for LG Home for up to 30 seconds. It makes
at most two additional launch attempts, only after LG Home has stayed visible
for 1.5 seconds and the previous launch has settled for at least 5 seconds.
Opening another app, explicitly visiting LG Home, disabling Home control, or
turning the TV off cancels this recovery.
