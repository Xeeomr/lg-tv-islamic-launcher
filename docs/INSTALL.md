# Install Clean Your TV — No-root and Root

**[v1.2.0 stable](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/tag/v1.2.0)** contains cytv **0.3.1**, Home **1.4.1**, Helper **0.6.19**, Root **0.3.0**, both edition Updaters **0.2.1**, Android **0.2.1-preview / code 10** and System Updater **1.0.0 / protocol 1**. The latest-download links follow the published stable release. Hardware evidence is limited to the documented configuration and checks; see [release notes](RELEASE-1.2.0.md) and [compatibility](COMPATIBILITY.md).

No-root and Root are equal options for different TV setups. Choose No-root for LG Developer Mode or Root for existing root SSH access. Compatibility and test coverage remain specific to each edition.

Use **cytv** to install either edition. It includes the runtime and TV packages;
you do not need to build from source. Both editions run on the TV after setup,
so your computer can be switched off during everyday use.

## 1. Choose your edition

| | No-root | Root |
| --- | --- | --- |
| TV access | LG Developer Mode and Key Server | An already rooted TV with working root SSH |
| Setup credentials | Developer Mode passphrase, then separate on-TV control pairing | Root password/key or SSH agent; verify the TV's SSH identity |
| Home control | On-TV Home Helper | System Home routing with independent recovery |
| After setup | Keep Developer Mode active and local networking available for Helper | Keep root access and recovery services available |
| Updates | From your computer; renewal is optional Beta | Compatible signed edition release sets through Settings after supervisor setup |

Root setup **does not obtain root**, flash firmware or enable Developer Mode.
Do not install Developer Mode over an existing rooted setup. Never run Root Home
control and No-root Helper together. See [edition comparison](EDITIONS.md).

Hardware evidence is scoped to documented builds, principally
**LG OLED55C3RLA / firmware 43.21.71**. Installation success does not establish
compatibility with another TV. Read [compatibility](COMPATIBILITY.md) and
[1.1.0 hardware acceptance and remaining checks](RELEASE-1.1.0-ACCEPTANCE.md).

## 2. Prepare your TV and computer

Turn on the TV and connect it and your computer to the same trusted local network.
Guest-network isolation, VPNs and firewalls can prevent discovery or connection.
Allow Local Network access when your computer asks.

**No-root:** install LG's Developer Mode app, sign in, enable Developer Mode and
complete any requested restart. Enable **Key Server** and keep the TV's passphrase
available. SSH pairing and the later on-screen control-pairing request are separate.
The updated Helper requires TV Node.js 0.12.2+; installation checks this before
changing packages. Older published packages do not gain compatibility automatically.
Keep the official session timer active: expiry can remove sideloaded apps.
See [Developer Mode preparation](MANUAL_INSTALL.md#2-no-root-prepare-the-tv).

**Root:** confirm existing root SSH access and retain recovery backups. The TV
needs Python 3.9+, Node.js 8+, luna-send, Homebrew services and a supported ARM32 Magic Remote
input interface. Investigate a changed SSH host key rather than bypassing the
check. See [Root access requirements](MANUAL_INSTALL.md#5-root-prepare-trusted-access).

If the TV has no suitable Python 3, Root setup can automatically download a
separate verified ARMv7 runtime on your computer/Android device and transfer it
over SSH. TVs with a suitable system Python skip this download. See
[optional Python delivery and compatibility limits](OPTIONAL-PYTHON.md).

## 3. Download and start cytv

Download the matching package from the
[latest release](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/latest):

| Computer | Package and launch |
| --- | --- |
| macOS Apple Silicon / Intel | `cytv-macos-arm64.zip` / `cytv-macos-x64.zip`; extract, move `cytv.app` to Applications and open it |
| Ubuntu 22.04+, Debian 12+, Mint 21+ x64 | Install `cytv-linux-x64.deb`, then open Clean Your TV from the applications menu |
| Windows x64 | Extract `cytv-windows-x64-desktop.zip`, then open `cytv-desktop/cytv-desktop.exe` with `_internal` beside it |
| Android ARM64 | Install `cytv-android-arm64.apk`; this is a debug-signed preview |

For Windows, use File Explorer **Extract All** and keep the complete folder.
Windows publisher signing is not configured. See [Windows desktop setup](DESKTOP_INSTALL.md#windows-x64).
Android 0.2.1-preview requirements, APK installation and limitations are covered
in the [Android guide](../android/README.md); physical-TV acceptance remains unverified.
The standalone `cytv-linux-x64` executable is the CLI; install the `.deb` above
for the Linux graphical app.

macOS desktop dependencies require macOS 13+; acceptance on older systems is not
established. Mac builds are not Apple-notarized; follow the documented
[Open Anyway procedure](DESKTOP_INSTALL.md#if-macos-says-cytv-was-not-opened)
if macOS blocks a trusted project download. Linux ARM desktop packages are not included.

See [desktop setup and troubleshooting](DESKTOP_INSTALL.md) for desktop packages,
or the [console guide](CLI.md) for all supported CLI targets.
The installer selects the computer's language automatically. TV language is a
separate preference under **Settings → Language**. [Localized guides](LANGUAGES.md).

## 4. Install No-root or Root

1. Choose **Set up my TV** in the desktop app, or start the console wizard.
2. Select a discovered TV, or enter its IP address.
3. Choose **No-root** or **Root** and review the TV and edition.
4. Complete the appropriate connection step. For No-root, enter the Developer
   Mode passphrase and approve the separate control-pairing request on the TV.
   For Root, use your existing root credentials and verify first-use SSH trust.
5. Continue and keep the TV on until installation and verification finish.

**No-root:** cytv personalizes Home, installs Home and Helper, configures their
pairing and startup, then starts Helper. An unconfirmed early input registration
uses the guarded fallback; it is not proof of early restoration.

**Root:** cytv installs Root Home, independent recovery and Root Updater, prepares
its rollback baseline, verifies setup, then activates Home and opens it.
There is **no trial countdown or Keep confirmation** in this normal setup flow.
The manual Root bundle has a separate updater-setup step; do not substitute a
standalone Root IPK for the complete installation.

For an interrupted operation, use **Check TV status** first. If offered, use
**Finish Root setup** to complete a verified installation. Retain recovery files;
unknown package outcomes must be resolved before retrying. Save a diagnostic
report when the wizard cannot establish a safe next step. [Recovery details](CLI.md#interrupted-operations).

<a id="7-verify-before-daily-use"></a>

## 5. Verify before daily use

Test on your TV after installation:

- Arrows and held arrows, OK, Back/Cancel inside apps, volume, pointer and wheel.
- Open an app, then press short Home to return to Clean Your TV.
- Press Home **three times within two seconds**, releasing between presses:
  LG Home should appear and navigation should work.
- Resume No-root with **Home Helper**; resume Root by turning **Change Home** on
  in Home settings. Opening Home alone does not resume a stopped Helper.
- Test standby/wake and cold boot separately. Record what happens without
  pressing Home. Root cold-power acceptance remains deferred.

**Change Home** selects the persistent Home behavior. **Open LG Home** only opens
LG Home once and preserves that selection. To disable Root routing, turn
**Change Home** off, use the emergency gesture, or restore from cytv.
Older packages can use different labels; No-root Helper through 0.6.13 uses
holding Home for about two seconds instead of the triple-press gesture.

If a check fails, leave LG Home active and use [No-root recovery](RECOVERY.md)
or [Root recovery](../root-edition/ROLLOUT.md#controls-and-recovery).
A successful installer run verifies commands and state, not physical buttons.

## 6. Updates, recovery and removal

Use cytv's status, diagnostics, restore and uninstall actions with the saved TV
connection. Removing cytv from your computer does not remove the TV installation.
Root uninstall through cytv removes project packages, including System Updater, Root Updater and
installed No-root components; retained inactive recovery evidence is intentional.
See [desktop maintenance](DESKTOP_INSTALL.md#remove-the-project-from-a-rooted-tv),
[CLI maintenance](CLI.md), and [manual maintenance](MAINTENANCE.md).

No-root Developer Mode renewal is optional and **off by default**. In Home
settings, select **Turn on auto-renewal** only after reading the
[Beta guide](DEVELOPER-MODE-BETA.md). Real renewal on unrooted TVs remains unverified;
keep checking the official timer. Root does not use this feature.

## Source installation without cytv

For either edition, use [manual installation](MANUAL_INSTALL.md): it covers
requirements, app inventory, build, pairing, activation, updater setup and recovery.
Use a new output directory for Root bundles and retain all support files.

For **No-root only**, `install.sh` automates source setup on macOS/Linux with
Node.js 20.19+ and npm, Python 3.9+ with pip/venv, and Git:

```sh
git clone https://github.com/Razdva122/clean-your-tv-lg-webos.git
cd clean-your-tv-lg-webos
./install.sh 192.168.1.50
```

Replace the IP. This prepares local dependencies, Zig 0.14.1 and webOS CLI 3.2.6,
pairs, syncs your apps, builds and installs Home and Helper. No global install or
sudo is needed. Internet access is required for tool downloads. The script creates
`clean-your-tv-<IP-with-dashes>` as its CLI profile; `DEVICE=another-name` selects
another profile without retargeting an existing TV connection.

Rerunning resyncs and rebuilds the current checkout while preserving
`launcher/config.js`; update the checkout first to obtain new source changes.
A failed run does not roll back installed packages. Keep `.lgtv-key.json` and CLI
keys private and do not use `bash -x`. Native Windows is not supported by this
Bash script; WSL installation is unvalidated. The Windows cytv console wizard
is distributed separately.

### Termux / Android

Supply a working **Zig 0.14.1** executable before running `install.sh`:

```sh
export ZIG=/absolute/path/to/zig
"$ZIG" version  # must print 0.14.1
./install.sh 192.168.1.50
```

A matching `zig` on PATH is also accepted. Android has no compatible
`ziglang==0.14.1` Python distribution; an explicit compiler skips that dependency.
Without one, setup stops before pairing or changing the TV. The compiler must
run in your actual Termux/container environment; CPU architecture alone does not
prove Android compatibility. Node.js, Python and CLI requirements still apply.
End-to-end Termux and C5/webOS 26 compatibility remain unverified.

## Root GUI after supervisor setup

If Root immediately shows `Denied methods call status` after supervisor bootstrap, close and reopen the **Home Root** app once to restart its GUI, then check Software updates again. If the error persists, retain diagnostics and inspect status; do not delete supervisor or recovery state.
