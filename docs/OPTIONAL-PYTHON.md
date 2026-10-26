# Automatic Python runtime for Root Edition

Available in [v1.1.0 stable](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/tag/v1.1.0); download the complete installer for your platform.

Root Edition needs Python 3.9 or newer on the TV, including the modules and
filesystem/process operations used by installation and recovery. The installer
keeps a suitable existing interpreter. A working system installation does not
download another Python, and ordinary desktop/Android installer packages do not
contain the ARM runtime archive.

If Root setup finds no suitable Python, it can download a separate, pinned ARMv7
runtime on the computer or Android device and transfer it through the existing
trusted SSH connection. The TV does not need Internet access for this step. The
download is about 26.3 MB. The normalized distribution materializes internal
archive links as independent regular files: about 119.3 MB installed and 51.5 MB
compressed for SSH transfer in the inspected artifact. Initial staging requires
**320 MiB free** on the TV; the installer checks this before provisioning.
Actual runtime compatibility is tested before
Root activation, not inferred from a TV model name.

## Scope and compatibility

The first managed target is CPython 3.13.17, python-build-standalone 20261021,
`armv7-unknown-linux-gnueabi-install_only_stripped`. Its source artifact is pinned
by URL, byte size and SHA-256 in installer source. There is no remotely mutable
`latest` manifest or arbitrary download URL. The installer verifies the archive
before processing or executing it; a corrupt download/cache is never trusted.

The binary depends on a compatible ARM EABI Linux loader and system libraries.
`armv7l` alone does not prove compatibility. This does not replace system libc,
install Python 2 compatibility, or make every older webOS API compatible.
LG UK6540PTD / firmware 05.50.70 from issue #37 is the motivating case, not a
hardware-validated model for this feature. No boot, rollback or remote-input
acceptance is claimed for that model until the actual runtime has been tested on the TV.

## Installation and recovery

Managed Python lives in an immutable version slot under
`/var/lib/clean-your-tv-python/`, separate from system Python and TV application
packages. No `/usr/bin` symlink or global PATH change is made. Root and the
independent updaters persist private launchers and binding evidence so background
workers, boot recovery and subprocesses keep using their selected interpreter.
Installations without managed bindings retain their existing system-Python path.

Missing Python does not cause automatic downloads during status, doctor, restore
or removal. Only setup operations may provision a new runtime. Existing managed
bindings remain usable by maintenance commands without an Internet connection.
An incompatible target or failed smoke test stops setup with diagnostics before
Home is activated.

Runtime slots are retained when removing TV applications because recovery records
or another installed updater may still require them. Do not delete these files
while Root, an updater, rollback data or unfinished recovery references them.
An interrupted or foreign slot is not silently overwritten.

## Prepare the download for an offline setup

On a computer with Internet access, run:

```sh
cytv --prepare-python-runtime
```

This verifies and caches the optional archive without discovering or contacting a
TV. Use the same installer data directory for the subsequent setup. For a portable
cache, use `--data-dir /path/to/private-data` with both commands and transfer that
directory privately to the installation computer if necessary. Do not share a
data directory containing your normal SSH identities, pairing keys or profiles.
Prepare a fresh directory dedicated to the cache when moving it between devices.

## Development validation

Linux CI executes the pinned ARM32 interpreter under QEMU using
`python scripts/test-python-runtime.py`, in addition to offline unit tests. This
checks actual executable startup, native modules, locks, filesystem operations
and subprocess execution. It does not validate the TV's loader/libc, old kernel,
boot timing, webOS APIs or rollback; physical-TV feedback is still required.

## Provenance and licensing

Upstream: [python-build-standalone release 20261021](https://github.com/astral-sh/python-build-standalone/releases/tag/20261021).
Artifact SHA-256:
`4a71641c8d5536175e404a961624e8656eba30e97b5026f6bd7dc31e4bbeaaea`.
The upstream license files accompany the optional runtime. Installing this
component adds a separately versioned dependency whose security updates require
a reviewed artifact-pin update and fresh validation.
