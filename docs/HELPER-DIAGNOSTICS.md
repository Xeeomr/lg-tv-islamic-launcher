# Home Helper diagnostics

## User workflow

In the desktop installer, open Maintenance and select **Home button diagnostics**.
In the Android installer, open Tools and select **Home button diagnostics**.
Choose the TV and No-root connection using the existing connection flow.

1. Open an app on the TV and continue when ready to record.
2. When prompted, press physical Home once, then leave the remote untouched.
   Keep the installer open for one minute.
3. Select **Save report** (desktop: **Save diagnostic report…**) and attach the
   resulting single JSON file to the issue. Say which app stayed visible.

No terminal commands, manual log collection or separate C5 Helper are required.

## Release handoff

[v1.1.0 stable](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/tag/v1.1.0) contains Helper 0.6.19 and cytv 0.3.0 with this diagnostic workflow. Download the stable installer for new feedback. Helper 0.6.19 still needs physical-TV acceptance; diagnostic capture alone does not establish that C5 or another model is fixed. The earlier v1.0.3 diagnostic baseline was Helper 0.6.18 / cytv 0.2.16.

Send the reply below only after a normal release candidate contains both the
updated Helper and installer. Published Helper 0.6.17 does not contain this mode.
The normal release process selects a new Helper version and builds it from source;
the build deliberately reuses the immutable published IPK for pinned 0.6.17.
Do not overwrite or relabel that baseline. Check the actual RC export on a TV
before sending the reply and link that RC in the comment.

## Implementation and report meaning

The ordinary Helper has an opt-in 60-second observation window. It adds no
launches, retries, input grabs or second foreground watcher. The existing control
channel handles `diagnostics-start` and `diagnostics-stop`; the installer handles
these automatically. A random session ID separates each capture from old logs.

Records include recognized Home presses, correlated launch requests and replies,
foreground observations, periodic samples, monitor status, and routing state.
The controller start record advertises `diagnosticsSchema: 1`.

Foreground samples use the existing subscription cache and carry its age; they
are not new queries. A blank app ID is a transition, while null means unknown.
A successful launch reply is only an acknowledgement. Unavailable monitoring is
reported explicitly. Neither an old observation nor a successful launch reply
proves which app became visible after Home.

The installer waits for confirmation that recording started, stops on cancellation,
and requests a stop after collection. Helper also expires the window independently.
It exports only allowlisted fields from the matching session into one private
JSON file. No credentials, addresses, full app inventory, raw logs or arbitrary
error text are copied. The report does include the observed application IDs and
timing. `complete` means the window expired, not that Home worked; check for an
actual Home event and usable foreground observations before drawing conclusions.
A missing start acknowledgement tells the user to update/start Helper.

## Draft reply for #12 — send only after the RC is available

Thanks for the logs. They show Home events reaching the Helper and successful
launch acknowledgements. We need to see which app actually becomes visible next.

The linked release or release candidate includes a simple diagnostic tool in the normal
installer. Please update both the installer and TV components using the RC linked
in this reply, then:

1. Open **Tools → Home button diagnostics** in the Android app (on a computer:
   **Maintenance → Home button diagnostics**), connect to your TV, and follow the
   prompts to start recording.
2. When prompted, press **Home once**, then leave the remote untouched and keep
   the installer open for one minute. Note what stays on screen.
3. Tap **Save report** and attach that single JSON file here. Tell us whether you
   saw Clean Your TV, LG Home, the original app, or a black screen.

No terminal commands or manual log collection are needed. The report contains
app IDs and timing, but no pairing keys or private connection details.
