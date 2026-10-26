# Offline candidate bundle

Build on the host with Python 3; the output directory must not exist:

```sh
python3 root-edition/build.py --version 0.2.0 --output /absolute/path/to/new-candidate
```

The bundle contains an isolated `com.cleanyourtv.root.preview` IPK, its public-source file hashes, the recovery runtime, and host/device drivers. `bundle.json` covers every distributed support/runtime file. `SHA256SUMS` covers the IPK. No TV connection occurs during build. This candidate still requires hardware validation.

For the later supervised TV session, use an explicit preconfigured OpenSSH alias with its host key already trusted:

```sh
python3 /path/to/candidate/setup.py install --ssh television --bundle /path/to/candidate
python3 /path/to/candidate/setup.py status --ssh television
python3 /path/to/candidate/setup.py trial --ssh television
python3 /path/to/candidate/setup.py restore --ssh television
python3 /path/to/candidate/setup.py uninstall --ssh television
```

`--identity /path/to/key` is optional. The scripts require strict host-key checking and batch authentication. Device operations require root, suitable Python 3.9+, TV Node.js 8+, Homebrew services,
the webOS Luna tool, the developer-app directory and supported ARM32 remote input.
Manual drivers do not provision Python; cytv can supply the optional pinned ARMv7
runtime on eligible TVs. Retain its verified binding for recovery/removal. Installation does not select this app as Home. Trial uses the runtime's bounded recovery flow. Persistent activation is available
through `setup.py enable` or **Change Home** in Home settings after the checks
pass. For normal setup, use [manual installation](../../docs/MANUAL_INSTALL.md),
including the independent updater step, or [cytv](../../docs/INSTALL.md).

By default the launcher inventory is empty. Explicitly add `--migrate-packaged-home` to **install** to copy `apps.js`, `config.js`, and referenced packaged icons from the fixed installed `com.gathin.tvhome` app. The source is read-only and never modified. Browser/localStorage-only preferences are excluded. Resulting candidate file hashes are retained in `personalization.json`; migration never adds personal data to the offline distribution.

The driver records stages in `/var/lib/clean-your-tv-root/deploy.json` before installation submission. Installation proceeds only after an independent matching terminal backend event and installed-file hash verification. Existing candidate files or state block installation. A timeout, disconnect, or uncertain result requires inspection; do not blindly retry. Remote staging remains available after failure.

Uninstall first requires successful Home recovery, rolls back this candidate's LS2 provisioning, refreshes registration, and requests removal. It requires a terminal removal reply and absence of all candidate app/service/package directories. After matching terminal removal, a fixed empty package metadata directory may be removed with `rmdir`; nonempty or indirect leftovers still stop cleanup. State and recovery evidence remain on disk; the driver never deletes retained state automatically. The production app and legacy helper are never written by these drivers.

Recovery implementation: service code and its fixed runner are copied by verified
hash into root-owned private state. The firmware's immutable Node bootstrap runs
that service; the Homebrew runner and system launcher are not patched. Registration
of the one recovery activity uses the root installer with a fixed bus sender and
checks the complete stored definition and creator before reuse or cancellation.
