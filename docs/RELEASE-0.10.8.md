# v0.10.8 — Current No-root updates and stable update controls

Includes cytv **0.2.11**, Home **1.3.4**, Helper **0.6.16**,
Root **0.1.8**, and No-root Updater **0.1.5**.

The installer also includes the ARM32 compatibility repair for issue #15: it
checks the `/bin/sh` ELF userspace ABI instead of rejecting an ARM64 kernel
from `uname` alone. Diagnostics report `tv.kernel_arch`, `userland_abi` and
`arm32_supported`. This avoids misclassifying compatible No-root TVs while
retaining explicit checks for the Helper’s required ARM32 execution support.

No-root Home reads its installed `appinfo.json` version when reporting startup
health. It no longer reports the obsolete hardcoded 1.2.2. Invalid, unreadable
or foreign manifests do not produce a health acknowledgement.

The signed No-root feed offers Home 1.3.4 with Helper 0.6.16. The signed rollback
package is the exact Home 1.3.3 package from v0.10.7. In-app installation requires
root, Homebrew Channel, scoped updater permissions, Helper 0.6.16 and the matching
1.3.3 baseline. Other baselines and TVs without root use computer-assisted setup.
The version bump lets existing Home 1.3.3 users receive the repair as an update.

Root now acknowledges successful startup automatically after restoring the
profile and checking the rendered application tiles. The pre-install confirmation
remains; the post-install Confirm working update button is removed. Readiness
failures still trigger the independent updater’s rollback safeguards. Background
status polling no longer disables controls or changes the selected button.
Status text has reserved space so its updates do not move the actions.

Publication checks now validate both edition feeds, Home/Root versions, Helper
requirements, signatures, candidate packages and the signed No-root rollback
package. CI repeats the checks after publication.

Automated regressions cover manifest versions across releases, false health
signals, automatic Root acknowledgement, real tile mismatches and stable focus
during delayed polling. These exact packages have not completed a new on-TV
installation/rollback cycle; earlier C3 records retain their original scope.

Downloads include installers for Windows, Linux, macOS Apple Silicon and Intel,
complete manual bundles, signed feeds and standalone update/rollback IPKs.
See `BUILD-INFO.json` and `SHA256SUMS` for provenance and package hashes.
