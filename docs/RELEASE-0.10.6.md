# v0.10.6 — No-root SSH authentication compatibility

Includes cytv **0.2.9**, Home **1.3.3**, Home Helper **0.6.16**,
Root Edition **0.1.6**, and No-root Updater **0.1.5**.

This installer patch fixes RSA public-key authentication for No-root Developer
Mode SSH servers that accept `ssh-rsa` signatures but do not advertise
`server-sig-algs`. Paramiko previously attempted an RSA SHA-2 signature, which
such servers reject with `AuthenticationException` before installation begins.
The compatibility setting is limited to No-root; Root retains RSA SHA-2 support.

A real local SSH regression covers the first connection and reuse of the saved
Developer Mode key. Root regression tests require RSA SHA-2 signatures.
This addresses a likely cause of issue #15; the reporter's LG OLED48C3LA on
webOS26 / 11.2.0-3701 has not yet been retested. No additional hardware
compatibility is claimed.

## Downloads and retry

Windows x64 users should close the old installer, download
`cytv-windows-x64.exe` from this release, and confirm cytv **0.2.9** is shown.
Choose **No-root**, keep Developer Mode and Key Server enabled, and enter the
currently displayed passphrase exactly when prompted.

macOS Apple Silicon and Intel ZIPs, the Linux x64 Debian package, console
executables, and the complete manual Root/No-root bundles remain available.
TV component versions and signed automatic-update feeds are unchanged from
v0.10.5. Existing hardware, startup and recovery limitations still apply; see
[the previous release notes](RELEASE-0.10.5.md).

`BUILD-INFO.json` records source and build provenance; `SHA256SUMS` covers the
release assets. macOS builds are ad-hoc signed, not Apple-notarized.
