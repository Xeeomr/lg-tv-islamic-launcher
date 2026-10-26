# v1.0.1 — Legacy TV rendering and compatible web builds

Fixes the empty app grid reported in issue #20. Older webOS engines ignore
`inset`, collapsing the app viewport to 0×0 and clipping loaded icons. Home and
dialogs now use physical offsets; settings/language layouts and spacing work
without CSS Grid or flex gap. Two unsupported JS calls were removed for older
engines. A community report confirmed the CSS correction on an LG 49NANO80PNA,
webOS SDK 5.6.2 / firmware 04.64.00 / Chromium 68. The original webOS 3.5 device
still needs final hardware confirmation.

## Components

- cytv 0.2.15
- Home 1.3.7
- Home Helper 0.6.17 (unchanged)
- Root 0.1.11
- No-root Updater 0.1.6
- Root Updater web package 0.1.1
- Android 0.1.6-preview (version code 7)

All TV web packages are compiled through Babel/core-js and PostCSS for a
Chromium 38 frontend target. Emitted scripts are checked as ES5; unsupported CSS
left after conversion fails packaging. CSS files, inline styles and HTML script
blocks are included. This build target does not certify every TV, native Helper
runtime, firmware service or remote. webOS 1.x/2.x are outside this engine target.

cytv also reconciles interrupted Root removal using the installed recovery
journal, checks for an operation still running, and gives clearer next steps.
Ambiguous package outcomes remain blocked; recovery records are retained.
Updater entry screens explain their purpose and require confirmation before
restoring an application. The exact published Helper 0.6.17 binary is retained
to preserve the existing signed rollback contract; later native entrypoint
changes in main are deferred to a separately versioned native release.

## Update No-root

1. Download the v1.0.1 cytv installer matching your computer (Android users can
   update the preview APK). Keep the TV awake and Developer Mode active.
2. Stop the current Helper with three short Home presses within two seconds;
   older Helpers through 0.6.13 use a long Home press instead.
3. Open cytv, select your saved TV and **No-root**, then run setup again. Review
   Home 1.3.7 / Helper 0.6.17 before confirming. A pending operation must be
   checked with status before continuing.
4. Open Home and check the app tiles, arrows/OK and app launching. If Helper was
   left stopped, open Home Helper to resume it.

No uninstall or factory reset is needed. An unrooted TV cannot install this
update through the rooted Home Updater service. Existing settings/order should
be reviewed after setup; keep a private configuration backup where available.

## Update Root

With a working Root Updater and accessible settings, open **Home → Settings →
Software updates**, check for **Root 0.1.11**, and confirm installation. The signed
application update preserves the profile and uses independent recovery.

If the old interface prevents using settings, or Root Updater is unavailable,
use the new cytv installer on your computer. Select your saved TV and **Root**,
check status first, then follow the existing-Root reinstall confirmation. Keep
your root SSH credentials and recovery records. Reinstallation may reset Home
preferences. Do not enable Developer Mode or select No-root on a rooted TV.
Root application OTA does not replace a pinned Root Updater runtime; updating
that infrastructure remains a separate computer-assisted maintenance operation.

## Validation and limits

The full automated suite, web compiler/linter tests, compiled legacy-limit
browser regression, settings/app interaction tests and public TV-payload build
passed locally before publication. CI rebuilds the platform installers, verifies
embedded versions/hashes and Android signing, runs tests, then signs and verifies
Root and No-root feeds. Release provenance is recorded in BUILD-INFO.json.

The browser regression models missing `inset`/JS APIs in a current browser; it
is not a complete old-TV emulator. No new physical-TV acceptance is claimed.
Developer Mode renewal remains opt-in Beta; existing startup, power-loss and
firmware-specific limitations remain in [compatibility](COMPATIBILITY.md).

See [installation](INSTALL.md), [TV web build](TV-WEB-BUILD.md) and
[issue #20](https://github.com/Razdva122/clean-your-tv-lg-webos/issues/20).
