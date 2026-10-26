# Manage apps on Home

Hold OK on an app for 0.6 seconds to pick it up. Use the arrows to move it,
press OK to place it, or Back to cancel. With a pointer, hold the tile,
release, point at its new position and click to place it.

The **+ / Add app** tile always stays last. It lists installed apps which
are not on Home, including apps previously hidden here. Selecting one adds
it at the end, before +. This does not install software.

To hide an app, pick it up and move down beyond the last row of apps to
**Hide from Home**, then press OK. The pointer can select this button directly.
The app remains installed on the TV. **Undo** receives focus immediately;
press OK to restore the original layout, or Back/an arrow to dismiss Undo.
You can also restore the app later through +. Hiding every app leaves + available.

## Inventory and persistence

The launcher asks its edition's service for a fresh inventory whenever + opens.
No-root uses the helper's existing SSAP pairing key and the TV's local network
addresses. Root uses a fixed, read-only Application Manager query. Both requests
are bounded. A missing pairing key, denied request or timeout falls back to the
saved inventory with an explicit message. No pairing dialog is intentionally
started, and no uninstall endpoint is called.

The new UI requires the corresponding updated service package for fresh discovery.
With an older service it can still manage the saved inventory. A live television
check is required before claiming compatibility with a specific firmware.

`tvhome.layout` stores order, hidden IDs and the known app catalog in localStorage.
Existing `tvhome.order` and configured hidden apps migrate on first use. Discovery
never automatically adds tiles. The no-root profile backup includes the new key,
so the updater can restore it along with the existing settings. Root retains the
layout in its application storage across in-place updates.

## Local verification

Run `bash scripts/test.sh` in a Python environment containing the project dependencies.
The model, service transport and profile tests are in `tests/apps/`.
Run the browser scenarios separately:

```sh
PLAYWRIGHT_MODULE=/absolute/path/to/playwright node tests/apps/ui.cjs
```

The browser test uses simulated TV replies and an isolated Chrome profile; it
checks remote/pointer hold, movement/cancellation, hide/undo, multirow navigation,
empty screen, addition, offline fallback and restart persistence.
