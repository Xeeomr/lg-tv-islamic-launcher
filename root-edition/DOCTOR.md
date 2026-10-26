# Root Edition doctor

## cytv requirement diagnostics (1.1.0)

`cytv doctor --report` uses the shared installer's saved connection and writes a
private issue-ready report. Root checks include UID, Python executable/modules
and version/features, Luna, developer/service directories and TV Node.js 8+.
`tv.root_requirements` records each result as `pass`, `fail` or `unknown`;
`ssh_command.exit_status` can record a safe numeric remote exit status without raw
output or credentials. Review reports before sharing. A failed Python check is
not a complete compatibility diagnosis.

Doctor is read-only and never downloads Python. Eligible setup can separately
provision pinned ARMv7 Python; maintenance uses retained verified bindings.
[Runtime compatibility](../docs/OPTIONAL-PYTHON.md) and other Root prerequisites
remain independent. The standalone probe below has its own conservative report
schema; it is not the cytv requirements report and does not certify compatibility.

Read-only diagnostics for Root Edition. The doctor itself does not install
software or obtain root. Use the [shared installation guide](../docs/INSTALL.md)
for cytv or [manual Root setup](ROLLOUT.md). No-root remains a separate edition.

## Run locally

Requires Python 3 and an existing OpenSSH connection. Configure the key and verify the host key beforehand; doctor never accepts a new host key automatically. It does not provision SSH or obtain root.

```sh
python3 root-edition/doctor.py --ssh my-tv --output doctor-report.json
# Developer Mode connections commonly use port 9922:
python3 root-edition/doctor.py --ssh prisoner@TV_ADDRESS --port 9922 --output doctor-report.json
```

The fixed collector is streamed to `sh -s`; no script is installed on the TV. It reads identity, kernel, userspace bitness, selected release-file fields, process capabilities and namespace identity, and command availability. It does not open input or kernel devices, start services, test writes, mount filesystems, run exploits, or change settings. SSH has a 25-second overall timeout. The TV may log the SSH session normally.

Model and firmware can optionally be supplied from a separately saved, read-only query using an already configured TV connection:

```sh
ssh my-tv "luna-send-pub -n 1 luna://com.webos.service.tv.systemproperty/getSystemInfo '{\"keys\":[\"modelName\",\"firmwareVersion\",\"sdkVersion\"]}'" > system-info.json
python3 root-edition/doctor.py --ssh my-tv --system-info system-info.json --output doctor-report.json
```

Use information from the same TV and session. Only the three requested fields enter the report. If the API is unavailable, omit this option and record the versions separately; the doctor does not guess them. All redirects above write locally.

Offline parsing:

```sh
python3 root-edition/doctor.py --input saved-probe.txt --system-info system-info.json
python3 -m unittest discover -s root-edition/tests
```

## Interpret the result

- `NOT_ROOT_IN_THIS_SESSION`: this connection has a nonzero UID. Other contexts may differ.
- `UID_ZERO_CONTEXT_UNVERIFIED`: UID 0 was observed, but host access and persistence are not established.
- `UNKNOWN`: insufficient identity information.
- `NOT_DETERMINED_BY_PROBE`: rootability requires separate, current upstream evidence for the exact model and firmware.
- `NO_VALIDATED_ADAPTER`: this conservative doctor probe has not validated an installation adapter. This is not the status of the separately implemented Root installer.

Exit code 0 means a report with a recognized UID was collected, **not** that installation or rooting is supported. Exit code 2 means failure or unknown UID. Existing output files are never overwritten. Reports omit addresses, credentials and serial numbers; review any report before sharing.

A 64-bit kernel does not imply a 64-bit userspace. Presence of `systemctl` or `luna-send` does not prove permission to use privileged operations.

## Inspect saved launcher registration

Supply a local copy of the successful `getAppInfo` response for `com.gathin.tvhome`:

```sh
python3 root-edition/doctor.py --input saved-probe.txt --app-info app-info.json --output report.json
```

`launcher.home_category` is `MISSING` or `REGISTERED`. A missing category blocked
native Home in the production-launcher trial. A registered category is only a
prerequisite; it does not change the `NO_VALIDATED_ADAPTER` installation status.
Only app ID, category status and a numeric version are included from this input;
paths and other arbitrary fields are omitted.
