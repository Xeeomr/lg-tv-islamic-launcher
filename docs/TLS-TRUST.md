# Outbound HTTPS trust on the TV

Developer Mode renewal and both update downloaders use a bundled Mozilla CA store,
with certificate and hostname verification enabled. This avoids relying on the
firmware's old Node/OpenSSL CA store. The WSS connection to the TV's own SSAP
endpoint is separate from these outbound HTTPS clients.

The unmodified bundle was downloaded over verified HTTPS from
[curl's Mozilla CA conversion](https://curl.se/docs/caextract.html).
Mozilla snapshot: **2026-10-20**. Download URL:
[`cacert.pem`](https://curl.se/ca/cacert.pem). The file SHA-256 was checked against
[`cacert.pem.sha256`](https://curl.se/ca/cacert.pem.sha256):

```text
796f1389bfea13c0ed78f663b765baaff54a508e5483786bd6ece73c5e3e3cbe
```

Three isolated service packages carry identical copies of `ca-bundle.crt` and the
Mozilla Public License 2.0 in `ca-LICENSE.txt`:

- `renewal-service/`
- `updater-service/`
- `root-edition/updater/`

These copies let source runs and installed services use the same local paths,
without reaching outside the service sandbox. Packagers include the bundle and
license; Root Updater also pins their hashes in its infrastructure inventory.

To refresh the store, download the new snapshot and its published SHA-256 over
verified HTTPS, compare the file digest, replace all three copies, update this
record and run `node tests/tls-ca.cjs` plus the packaging tests. Do not fetch trust
material dynamically on the TV or fall back to disabling certificate checks.
The curl conversion does not include all browser-specific CA name constraints;
see the source page for that limitation.

Existing on-TV services need their package/infrastructure updated explicitly.
Root Updater's independently provisioned code is deliberately immutable during
ordinary Home updates; those updates alone will not refresh an older CA store.
Use the existing host recovery/migration workflow for that infrastructure.
After the 1.1.0 supervisor is explicitly provisioned, a compatible signed
whole-edition update can replace its allowlisted Root Updater infrastructure,
including the CA store, with verified rollback. This does not update the fixed
supervisor itself or turn a legacy Home-only update into an infrastructure update.
See [transition and recovery](UPDATES.md).

Wrong TV time, expired leaf certificates, a proxy's private CA and unsupported TLS
protocols still cause a safe failure. The bundled roots do not bypass those checks.
