# Preparing the next metadata-registration test

Historical development record. Pending steps and version claims below describe
that investigation, not the current release. Use the [installation guide](../docs/INSTALL.md)
for current setup; retain these notes as evidence.

The current blocker is not writing a JSON field. It is making SAM register the
category and reliably undoing that registration without affecting the working
launcher and startup behavior.

## Evidence already available

- Current Home 1.1.0 has no `appCategory` in registered app info.
- `setDefaultApp` and profile readback can accept its ID while `launchDefaultApp`
  still fails. Verify the consumer operation, not only the configuration source.
- The diagnostic app declared `home` before installation and was successfully
  launched through the native category route.
- A local plan generated from the actual manifest changes only `appCategory` and
  can return the exact original bytes. No changed manifest has been installed.

## Candidate refresh routes

1. **Package update through the installer.** Homebrew Channel's installer uses
   `com.webos.appInstallService/dev/install` and waits for final installation
   status. This is an existing package-registration route, but an update can stop
   the app/services. It requires a matching rollback package and verification of
   personal app inventory and data preservation. Do not build an empty generic
   inventory over a personalized TV installation.
2. **Narrow app-registry refresh.** Investigate whether this firmware exposes a
   supported per-app refresh. No such live procedure has been validated here.
   Do not confuse an LS2 service scan with application registration.
3. **Restarting broad system services.** Not part of the bounded test design:
   it can affect windows, focus, startup and other apps.

Source reviewed locally: [Homebrew Channel installer implementation, pinned revision](https://github.com/webosbrew/webos-homebrew-channel/blob/92fcf9fef7ce08dbeae3b0616df8d0c75c11f0b3/services/service.ts).
Its service-permission refresh is a different operation:
[service elevation implementation](https://github.com/webosbrew/webos-homebrew-channel/blob/92fcf9fef7ce08dbeae3b0616df8d0c75c11f0b3/services/elevate-service.ts).
These are source observations, not evidence that either action is harmless on
all TVs or that a metadata-only update has passed this project's rollback tests.

## Before the next user-present trial

- Choose and validate the registration route on a separate diagnostic package.
- Save exact production manifest, package/data inventory and registered category.
- Include metadata and cache restoration in the independent recovery transaction.
- Verify the original route is restored after a deliberate failure before switching
  system Home to the production candidate.
- Keep the production helper and launcher versions fixed; ask the user to test
  short Home and Back separately once the bounded trial is ready.
