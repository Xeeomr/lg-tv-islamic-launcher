# Update, disable, rollback and uninstall

## Whole-edition updates in 1.1.0

The stable release adds signed complete edition release sets through an
independent System Updater supervisor. On-TV updates need existing root/Homebrew
services, TV Node.js 8+, suitable Python and an explicit computer bootstrap with
`cytv enable-system-updates --edition root` for Root, or the manual supervisor
bootstrap with a root SSH alias for No-root on a rooted TV. Unrooted TVs continue
computer-assisted updates. See [update setup](../root-edition/UPDATES.md).
Legacy app-only OTA does not install the new infrastructure. Unknown outcomes,
conflicting installers and downgrades are refused. Keep recovery evidence and
referenced managed Python slots; maintenance commands never download a runtime.

For cytv installations of either edition, use its saved connection and maintenance
actions: [desktop maintenance](DESKTOP_INSTALL.md), [CLI reference](CLI.md).
For manual Root setup, follow [Root removal and replacement](../root-edition/ROLLOUT.md#remove-or-replace-root-edition)
and [Root updates](../root-edition/UPDATES.md). Root recovery/updater state is
retained intentionally; never delete it to force reinstallation.

The webOS CLI procedure below applies to **No-root source installations**.
Stop Helper with triple Home in current builds, or hold Home for about two
seconds in Helper versions through 0.6.13.

For a **one-script installation**, run CLI commands from the repository folder.
The CLI is local; expose it in your current terminal:

```sh
export PATH="$PWD/build/tools/node_modules/.bin:$PATH"
```

The automatic device name is `clean-your-tv-<IP-with-dashes>` (for example
`clean-your-tv-192-168-1-50`), or the `DEVICE` override you supplied. Replace
`-d lgtv` in the commands below with `-d clean-your-tv-192-168-1-50`, using your
actual device name. Manual installations below use the profile `lgtv`.

## Update

Read the release notes. Pause interception with triple Home before updating. Keep
known-working packages locally. Do not uninstall first: that can remove app data.

Build the new version, then install helper followed by launcher. Refresh app inventory
and rerun `scripts/configure-tv.sh` to restore pairing/watch configuration if the
installer has replaced state. Manually open Home Helper only when ready.
State preservation across every firmware/installer version is not guaranteed.

## Remove input restoration

Run on your computer with the configured `lgtv` device:

```sh
ares-novacom -d lgtv --run "luna-send-pub -n 1 luna://com.webos.service.eim/deleteDevice '{\"appId\":\"com.gathin.tvhome\"}'"
```

Check for `returnValue: true`. This removes the input registration; it does not
uninstall the applications. First press Home three times within two seconds to stop interception.

## Uninstall

1. Press Home three times within two seconds to stop interception.
2. Remove input restoration using the command above.
3. Remove the startup task if the service is still installed:

```sh
ares-novacom -d lgtv --run "luna-send-pub -n 1 luna://com.local.nativehome.service/disable '{}'"
ares-install -d lgtv --remove com.local.nativehome
ares-install -d lgtv --remove com.gathin.tvhome
```

Remove any Quick Access assignment manually. Uninstalling the launcher can delete
its saved tile ordering. Keep your local configuration if you want to reinstall.
Revoke the SSAP pairing through TV device/connection settings if desired; erase
`.lgtv-key.json` and `build/setup/ssap-key.json` on the computer when no longer needed.

## Rollback

If the independent System Updater is installed, use its edition Updater's
Recovery flow for the verified previous component set. Do not manually replace
packages around its captured baseline. The manual procedure below applies to
source installations without that supervisor.

Pause first, then reinstall your saved previous packages. Reconfigure pairing/input
registration if necessary. Previous helper versions have different recovery behavior;
read their instructions before manually starting the helper. This repository does
not silently downgrade or reset your TV.
