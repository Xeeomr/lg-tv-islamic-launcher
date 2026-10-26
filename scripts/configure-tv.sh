#!/usr/bin/env bash
# Run AFTER installing both packages and pairing with sync-apps.py.
set -euo pipefail
cd "$(dirname "$0")/.."
: "${TV_HOST:?Set TV_HOST to your TV address}"
DEVICE="${DEVICE:-lgtv}"
mkdir -p build/setup
python3 - <<'PY'
import json,os
from pathlib import Path
host=os.environ['TV_HOST'];keys=json.loads(Path('.lgtv-key.json').read_text());key=keys.get(host)
if not key:raise SystemExit('Run sync-apps.py and accept the pairing request first.')
s=Path('launcher/apps.js').read_text();apps=json.loads(s[s.index('{'):].rstrip().rstrip(';'))['apps']
p=Path('build/setup/ssap-key.json');p.write_text(json.dumps({'key':key}));p.chmod(0o600)
Path('build/setup/apps.json').write_text(json.dumps([a['id'] for a in apps if a['id'] not in ['com.gathin.tvhome','com.local.nativehome','com.webos.app.home']]))
PY
STATE=/media/developer/apps/usr/palm/applications/com.local.nativehome/state
# CLI 3.x TV profiles do not offer ares-push or stream stdin over --run.
# Never print CLI output from a command containing the encoded pairing key:
# transport failures may echo the entire command, even if remote exit is zero.
push() {
  local payload digest reply command
  payload=$(base64 < "$1" | tr -d '\n')
  digest=$(python3 -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$1")
  # Stage in the same directory: failed decode, chmod or verification must leave
  # the current file intact. mktemp starts private; inspect actual mode as well
  # as chmod's status before publishing with an atomic rename.
  command="umask 077
  tmp=\$(mktemp '$STATE/.upload.XXXXXX') || exit 0
  trap 'rm -f \"\$tmp\"' EXIT
  if printf '%s' '$payload' | base64 -d > \"\$tmp\" &&
     chmod '$3' \"\$tmp\" &&
     [ \"\$(stat -c %a \"\$tmp\")\" = '$3' ] &&
     [ \"\$(sha256sum \"\$tmp\" | cut -d ' ' -f 1)\" = '$digest' ] &&
     mv -f \"\$tmp\" '$STATE/$2'; then
    printf '%s\\n' 'CYTV_TRANSFER_OK'
  fi
  exit 0"
  if ! reply=$(ares-novacom -d "$DEVICE" --run "$command" 2>&1); then
    echo "Copying $2 to the TV failed (connection or command error)." >&2
    return 1
  fi
  if ! printf '%s\n' "$reply" | tr -d '\r' | grep -qx 'CYTV_TRANSFER_OK'; then
    echo "Copying $2 to the TV failed (content or permissions not verified)." >&2
    return 1
  fi
}
push build/setup/ssap-key.json ssap-key.json 640
push build/setup/apps.json apps.json 644
eim_status=0
EIM=$(ares-novacom -d "$DEVICE" --run "luna-send-pub -n 1 luna://com.webos.service.eim/addDevice '{\"appId\":\"com.gathin.tvhome\",\"pigImage\":\"\",\"mvpdIcon\":\"\"}'" 2>&1) || eim_status=$?
EIM=$(printf '%s\n' "$EIM" | grep -v '^\[Info\]' || true)
eim_result=$(printf '%s' "$EIM" | python3 -c '
import json,sys
raw=sys.stdin.read().strip()
try:
    value=json.loads(raw)
except ValueError:
    value=None
result=value.get("returnValue") if isinstance(value,dict) else None
print("empty" if not raw else "success" if result is True else "denied" if result is False else "unknown")
')
if [ "$eim_status" -ne 0 ]; then
  echo 'WARNING: EIM command failed; registration not confirmed. The guarded startup fallback remains available.'
else
  case "$eim_result" in
    success) echo 'Early input restoration registered.' ;;
    denied) echo 'WARNING: EIM registration rejected. The guarded startup fallback remains available.' ;;
    empty) echo 'WARNING: EIM registration not confirmed (no reply from the dev shell). This does not prove rejection; the guarded startup fallback remains available.' ;;
    *) echo 'WARNING: EIM registration not confirmed (unrecognized reply). The guarded startup fallback remains available.' ;;
  esac
fi
echo 'Now launch Home Helper explicitly.'
