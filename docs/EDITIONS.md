# Choose your edition

No-root and Root are equal options for different TV setups. Choose No-root for LG Developer Mode or Root for existing root SSH access. Compatibility and test coverage remain specific to each edition.

Both editions share the Home interface and run on the TV after setup. Root
Stable is separate from the stable No-root release; installing it does not
upgrade or remove your ordinary launcher.

| | No-root Edition | Root Stable |
| --- | --- | --- |
| 1.2.0 | Home 1.4.1 + Helper 0.6.19; original-device feedback remains open | Root 0.3.0; see the [acceptance scope](RELEASE-1.2.0-ACCEPTANCE.md) |
| Root required | No | Existing root required; installer does not obtain it |
| Everyday external device | None | None |
| Setup | Computer, LG Developer Mode and local pairing | Computer, verified root SSH, compatibility and recovery checks |
| Short Home | On-TV helper redirects it | System Home routing; old helper must be stopped |
| Confirmed Back exit | Preserves navigation; LG can briefly flash | No LG flash observed in tested Kinopoisk exits |
| Emergency exit | Three short Home presses within two seconds | Three short Home presses within two seconds |
| Enable again | Home Helper | Turn Change Home on in Home settings; stays on until disabled |
| Normal exit | Turn Change Home off, or use the emergency gesture | Turn Change Home off; Open LG Home only visits once |
| Startup evidence | Standby and cold boot on tested setup | Software reboot, quick standby and failsafe have scoped evidence; cold-power testing deferred |
| Developer Mode | Session must remain active; auto-renewal is opt-in Beta | Not used by Root installer; do not install Developer Mode over root |
| Updates | Computer-assisted on unrooted TVs; the separate Home Updater requires root ([details](UPDATES.md)) | Signed whole-edition updates with independent supervisor, saved profile and rollback; one-time root/Homebrew computer bootstrap required ([guide](../root-edition/UPDATES.md)) |
| Early black screen | Known limitation | Not solved |

## Get started

Download [v1.1.0 stable](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/tag/v1.1.0). Current component versions are recorded in [`release-versions.json`](../release-versions.json); hardware evidence remains specific to the artifacts and scenarios recorded in [compatibility](COMPATIBILITY.md).

- **Without cytv:** [Manual installation of No-root and Root](MANUAL_INSTALL.md), including requirements for each edition and recovery commands.

- **Both editions:** [Install with cytv](INSTALL.md).
- **No-root:** [recover](RECOVERY.md), [compatibility](COMPATIBILITY.md).
- **Root Stable:** [Overview](../root-edition/README.md), [install and activate](../root-edition/ROLLOUT.md), [evidence and gates](../root-edition/RELEASE-ACCEPTANCE.md).

The Root hardware evidence is from **LG OLED55C3RLA, firmware 43.21.71** with a
Magic Remote. Other hardware is unvalidated. Keep your working installation and
private backups; never publish credentials, pairing data or device inventories.

The current C3 check passed triple-Home emergency exit and explicit resume. True cold boot and a complete signed system upgrade/rollback remain untested. See [current hardware scope](COMPATIBILITY.md#current-110-hardware-evidence); [earlier Root release observations](../root-edition/ROOT-0.1.1.md) retain their original scope.
