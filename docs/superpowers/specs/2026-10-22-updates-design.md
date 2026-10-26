# In-app updates

Approved scope: check releases from Settings, preserve user data, offer root installation through an independent updater package, and retain manual installation guidance without root.

The updater package is separate from Home and Home Helper so installing Home does not kill the transaction owner. It never updates itself or the helper automatically. A signed release manifest pins Home version, helper compatibility, package hash and URL. Unknown formats, unsigned releases, incompatible helper versions and downgrades are refused. Root capability is checked through Homebrew Channel, never inferred from model or Developer Mode.

Home migrates its inventory and icon bytes into a versioned local snapshot before using generic packages. Before installation, the independent service must persist this snapshot. Existing localStorage settings and ordering are included. The new Home restores before rendering. An unreadable saved snapshot is not silently overwritten.

Transactions persist before installation, reject duplicates and retain a verified prior package descriptor. Failed installation attempts get one rollback attempt; ambiguous timeout/interruption never starts a concurrent install. A recovery action reconciles the installed version before retrying. Installation success is distinct from a healthy first launch. Recovery remains available from the independent updater app.

Initial implementation is local and opt-in. Hardware installation, service permissions, reboot persistence and recovery must be validated on an isolated test app before shipping or modifying the working TV. No automatic updates, helper changes, renewal enabling or profile changes.
