# v0.9.0 — One installer for both editions

This release contains cytv 0.1.10, Root 0.1.2, Home 1.3.0, Home Helper 0.6.14
and the separate No-root Home Updater 0.1.3.

## Install

Download the cytv executable for your computer from the release assets:

- Windows x64: `cytv-windows-x64.exe`
- macOS Apple Silicon: `cytv-macos-arm64`
- macOS Intel: `cytv-macos-x64`
- Linux x64: `cytv-linux-x64`

On macOS/Linux, make the downloaded file executable with
`chmod +x ./cytv-macos-arm64` (substitute your filename), then run it from a terminal.
On Windows, run the downloaded executable. Keep the TV on and use the same home
network. Follow the [installer guide](CLI.md) for discovery, SSH and pairing.

Root requires an already rooted TV with working SSH. No-root requires LG Developer
Mode. cytv does not obtain root or remove Developer Mode requirements.

## Root activates immediately

The wizard installs and verifies recovery, stops the old Helper, enables persistent
Root Home control and opens Home. There is no trial, countdown or Keep confirmation.
If the old Helper cannot stop automatically, the wizard explains how to stop it
with the remote and retries that step. Recovery checks remain mandatory.

Use **Return to LG Home**, `cytv restore`, or three short Home presses within two
seconds to exit. Interrupted operations retain diagnostic and recovery information;
use `cytv status` instead of blindly reinstalling.

Root retains Software updates, profile recovery and the update lock from 0.1.1.
The separate Root Updater still requires its documented one-time setup. Application
updates cannot replace recovery infrastructure: use the complete installation bundle
for a migration that changes private service code or permissions.

## App management and controls

Both editions support moving and hiding tiles, adding installed apps with the final
**+** tile, and saving layout changes. Hiding a tile does not uninstall its app.
Home 1.3.0 requires Helper 0.6.14 for the new inventory service. The updated Helper
uses three short Home presses within two seconds to exit; older Helper versions
through 0.6.13 use a two-second hold.

## Manual installation and limits

The complete Root archive contains public source, `build/root-candidate` and
`build/root-updater`. The No-root archive contains public IPKs and English guides.
See [manual installation](MANUAL_INSTALL.md) and [Root rollout](../root-edition/ROLLOUT.md).
Direct `deploy.py install` installs recovery first; follow the separate activation
step in that guide. Internal diagnostic trial commands are not part of the wizard.

Hardware evidence remains scoped to LG C3; other models are unverified. Existing
Root compatibility and emergency-gesture limitations remain documented in
[release acceptance](../root-edition/RELEASE-ACCEPTANCE.md). This GitHub release keeps
the previous signed update feeds unchanged so existing updaters remain reachable.
The new packages are installed with cytv or the complete manual bundles; they are
not offered as an infrastructure-changing automatic update.

Builds assert application/service versions against `release-versions.json` and
verify embedded hashes. `SHA256SUMS` covers downloadable assets; it is not a code
signature. macOS binaries are not Apple-notarized.
