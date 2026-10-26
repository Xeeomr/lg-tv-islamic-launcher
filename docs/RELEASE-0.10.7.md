# v0.10.7 — Root update readiness repair

Includes cytv **0.2.10**, Home **1.3.3**, Home Helper **0.6.16**,
Root Edition **0.1.7**, and No-root Updater **0.1.5**.

Root update verification incorrectly counted the Add app action as an installed
application. A correctly rendered Home therefore failed readiness checks before
the confirmation prompt appeared, eventually triggering automatic rollback.
The same check could leave a successful rollback in Recovery.

The readiness check now compares actual application tiles only and derives the
expected visible applications from Home’s saved-layout model. Add app and hidden
applications no longer cause false failures. Missing, incorrect or unrendered
tiles still prevent readiness.

The failure was diagnosed on OLED55C3RLA / 43.21.71: 30 restored application
tiles plus Add app were incorrectly compared with 30 applications. The installed
0.1.3 rollback package and live restored profile were independently verified,
then the existing rollback was completed through a fresh readiness check without
reinstalling either package. Automated regressions cover Add app, saved hidden
applications and genuine tile mismatches.

The signed Root feed offers 0.1.7. After the updated Home opens, test it and
confirm the working update within two minutes; otherwise the updater rolls back.
An application update does not replace pinned recovery infrastructure.

Downloads include console/desktop installers for Windows, macOS Apple Silicon,
macOS Intel and Linux, plus complete Root/No-root manual bundles. Existing
No-root SSH compatibility fixes are retained. `BUILD-INFO.json` and `SHA256SUMS`
record provenance and asset hashes. Hardware acceptance beyond the described
recovery and readiness checks remains scoped to the tested installation.
