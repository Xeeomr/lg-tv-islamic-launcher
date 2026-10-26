#!/usr/bin/env bash
# Publish a signed release that TVs running Xee Launcher install by themselves.
#   scripts/publish-update.sh            build, check, sign and create the GitHub release
#   scripts/publish-update.sh --dry-run  everything except the upload
# Needs: gh (signed in), Zig (see install.sh), and the signing key at ~/.config/xee-launcher/update-ed25519.pem.
set -euo pipefail
cd "$(dirname "$0")/.."
DRY=${1:-}
KEY="${XEE_UPDATE_KEY:-$HOME/.config/xee-launcher/update-ed25519.pem}"
[[ -f "$KEY" ]] || { echo "Signing key not found: $KEY"; exit 1; }
[[ "$DRY" == --dry-run || -z "$(git status --porcelain)" ]] || { echo 'Commit your changes first: a release is built from a clean checkout.'; exit 1; }
export PATH="$PWD/build/tools/node_modules/.bin:$PWD/.venv/bin:$PATH"
: "${ZIG:=$(python3 -c 'from pathlib import Path; import ziglang; print(Path(ziglang.__file__).parent / "zig")')}"
export ZIG

HOME_V=$(python3 -c 'import json;print(json.load(open("launcher/appinfo.json"))["version"])')
HELPER_V=$(python3 -c 'import json;print(json.load(open("native/app/appinfo.json"))["version"])')
TAG="v$HOME_V"
rm -rf dist && XEE_RELEASE=1 bash scripts/build.sh >/dev/null
HOME_IPK="dist/com.gathin.tvhome_${HOME_V}_all.ipk"; HELPER_IPK="dist/com.local.nativehome_${HELPER_V}_arm.ipk"

# Nothing personal may leave this computer: no pairing key, no private fonts or adhans.
python3 - "$HOME_IPK" "$HELPER_IPK" <<'PYCHECK'
import io, subprocess, sys, tarfile
bad = ('ssap-key.json', 'thmanyah', 'adhan-makkah', 'adhan-madinah', '.lgtv-key', 'remote-tokens', 'xee-remote-token')
private = subprocess.run(['git', 'ls-files', '--others', '--ignored', '--exclude-standard', 'launcher'], capture_output=True, text=True).stdout.split()
for ipk in sys.argv[1:]:
    data = open(ipk, 'rb').read()
    pos = 8
    while pos < len(data):
        name = data[pos:pos + 16].decode().strip().rstrip('/'); size = int(data[pos + 48:pos + 58].decode().strip())
        body = data[pos + 60:pos + 60 + size]; pos += 60 + size + (size % 2)
        if not name.startswith('data.tar'): continue
        with tarfile.open(fileobj=io.BytesIO(body)) as t:
            for m in t.getnames():
                low = m.lower()
                if any(b in low for b in bad) or any(low.endswith('/' + p.split('/')[-1].lower()) for p in private):
                    sys.exit(f'{ipk} contains a private file: {m}')
    print('clean:', ipk)
PYCHECK

node - "$KEY" "$HOME_V" "$HOME_IPK" "$HELPER_IPK" <<'NODE'
const crypto = require('crypto'), fs = require('fs'), path = require('path');
const [key, version, ...ipks] = process.argv.slice(2);
const apps = ipks.map(f => {
  const name = path.basename(f), m = /^(.+?)_([0-9.]+)_[a-z]+\.ipk$/.exec(name);
  return {id: m[1], version: m[2], file: name, sha256: crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex')};
});
// Must match signedText() in native/app/updater.js.
const text = JSON.stringify({version, apps: apps.map(a => ({id: a.id, version: a.version, file: a.file, sha256: a.sha256}))});
const signature = crypto.sign(null, Buffer.from(text), fs.readFileSync(key)).toString('base64');
fs.writeFileSync('dist/update.json', JSON.stringify({version, apps, signature}, null, 2) + '\n');
console.log('signed update.json for', version);
NODE

NOTES=$(mktemp)
python3 - "$HOME_V" > "$NOTES" <<'PYNOTES'
import re, sys
v = sys.argv[1]
text = open('CHANGELOG.md', encoding='utf-8').read() if __import__('os').path.exists('CHANGELOG.md') else ''
m = re.search(r'^## ' + re.escape(v) + r'\b.*?$(.*?)(?=^## |\Z)', text, re.S | re.M)
print((m.group(1).strip() if m else 'Xee Launcher ' + v) + '\n\nTVs with automatic updates on install this release by themselves.')
PYNOTES
if [[ "$DRY" == --dry-run ]]; then echo "dry run: would publish $TAG"; cat dist/update.json; exit 0; fi
gh release create "$TAG" "$HOME_IPK" "$HELPER_IPK" dist/update.json --title "Xee Launcher $HOME_V" --notes-file "$NOTES"
rm -f "$NOTES"
echo "published $TAG"
