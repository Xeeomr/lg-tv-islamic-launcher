# Root Edition 0.1.1 — Settings updates and recovery

Distributed in repository release **v0.8.2**. Root package identity remains
`com.cleanyourtv.root.preview`; its installed version is now **0.1.1**.
The separate **Root Updater 0.1.0** owns installation, cached rollback packages,
saved profiles and recovery independently of the launcher package.

## Install

Download the complete `clean-your-tv-root-0.1.1.tar.gz`, verify `SHA256SUMS`,
extract it and follow [installation and activation](ROLLOUT.md). It includes the
public source and instructions, `build/root-candidate` and `build/root-updater`.
Existing root, verified root SSH and the documented compatibility checks are
required; this does not root the TV. Do not install the launcher IPK alone.

Install the launcher with LG Home selected, then perform the
[one-time Root Updater setup](UPDATES.md) using that exact Root bundle as the
rollback baseline. Subsequent compatible application releases can update from
Settings → Software updates. Recovery and updater infrastructure stay pinned.
After installation, use Try Home control and confirm Keep using Home within the
protected trial; Return to LG Home restores routing. Three short Home presses
within two seconds remain the independent emergency exit.

**Existing Root Stable 0.1.0:** its launcher package version was 0.0.1, without
this updater-compatible infrastructure. The first migration needs a computer
and maintainer review. Restore LG Home and retain all private recovery evidence.
Neither IPK-only installation nor deletion of retained state is a supported
migration. Setup refuses to overwrite a live recovery runtime.

## Data and rollback

The updater saves the validated application inventory, embedded icons, inputs,
configuration and tile order before replacement. After verified installation,
the new launcher restores its profile before rendering and asks for confirmation
within two minutes. If launch confirmation is absent, one automatic rollback
restores the verified cached prior package and waits for restored UI readiness.
An unknown installer outcome remains blocked for inspection rather than retrying.
Other applications and the ordinary Home profile are not replaced.

## Artifact identity

| Artifact | SHA-256 |
| --- | --- |
| Root `bundle.json` | `ab33e736af34d6cf676617520b9d8354d1782543079b9d15026b0611ad834cc6` |
| Root 0.1.1 IPK | `c8500e636c13ca9d2cb181d71eef778e387c358277d3401427c3c364aff1ac40` |
| Root Updater 0.1.0 IPK | `df4df14d92a86dbc80c60e352a71ded21e7865fb6ee0d80f54902e6c0bc3e935` |

The release asset `SHA256SUMS` also covers the complete archives and signed
metadata. Builds were repeated and all bundle file hashes matched.

## Evidence and limits

On **OLED55C3RLA / firmware 43.21.71**, real Settings installation from 0.1.0 to
0.1.1 and automatic timeout rollback from 0.1.2 to 0.1.1 passed under isolated lab
identities. The complete 30-application/five-input profile and rendered order
matched after both operations; the user confirmed the physical remote and
application launch. All 27 pre-existing application manifests, the ordinary
profile and LG Home routing were unchanged. See the
[hardware record](../docs/development/ROOT-UPDATES-TV-VALIDATION.md).

The lab used an ephemeral verification key and loopback transport. The published
production identities/key, final merged settings layout, public GitHub delivery,
updates starting from active Root routing and interrupted installation/power-loss
recovery have not had another full TV cycle. Terminal installer failures without
validated firmware evidence remain unknown outcomes. Compatibility on other
models/firmware is not established.

Earlier Root Stable 0.1.0 routing and lifecycle evidence is preserved in its
[historical release record](ROOT-STABLE-0.1.0.md). Cold-power behavior and the
unexplained initial second-attempt emergency gesture are still limitations.
Generic build flags remain `hardware_validated: false` and
`public_release_ready: false`; no blanket hardware certification is claimed.

No-root packages and signed metadata in v0.8.2 are unchanged from v0.8.1. Both
updaters use the shared latest repository release with separate signed metadata
files, `update.json` and `root-update.json`.
