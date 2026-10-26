"""Copy private files (Thmanyah fonts, adhan recordings you may not redistribute) to the TV's Home Helper.

They are kept in Helper's data folder, which survives updates from GitHub, and served to Home on the TV only.
Usage: python3 scripts/push-private.py TV_IP [CODE]
The first run pairs this computer: type the 4-digit code shown on the TV.
"""
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOKEN = ROOT / '.xee-remote-token'


def api(host, route, body=None, token=None, raw=None):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(f'http://{host}:8090/api/{route}', data=data, method='POST' if data is not None else 'GET')
    req.add_header('Content-Type', 'application/octet-stream' if raw is not None else 'application/json')
    if token:
        req.add_header('X-Xee-Token', token)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read() or b'{}')
    except urllib.error.HTTPError as e:
        return json.loads(e.read() or b'{}')


def token_for(host, code=None):
    saved = json.loads(TOKEN.read_text()) if TOKEN.exists() else {}
    if saved.get(host) and api(host, 'status', token=saved[host]).get('returnValue'):
        return saved[host]
    # A code given on the command line answers a pairing request already shown on the TV.
    if not code:
        if not api(host, 'pair', {}).get('returnValue'):
            sys.exit('Could not reach Home Helper on the TV (port 8090).')
        code = input('Code shown on the TV: ').strip()
    r = api(host, 'pair/confirm', {'code': code, 'name': 'computer'})
    if not r.get('token'):
        sys.exit('Pairing failed: ' + str(r.get('errorText')))
    saved[host] = r['token']
    TOKEN.write_text(json.dumps(saved))
    TOKEN.chmod(0o600)
    return r['token']


def private_files():
    tracked = set(subprocess.run(['git', 'ls-files', 'launcher'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split())
    out = []
    for p in sorted((ROOT / 'launcher' / 'fonts').glob('thmanyah*.woff2')):
        out.append(('fonts/' + p.name, p))
    for p in sorted((ROOT / 'launcher' / 'audio').iterdir()):
        if p.suffix.lower() in ('.mp3', '.ogg', '.m4a') and p.relative_to(ROOT).as_posix() not in tracked:
            out.append(('audio/' + p.name, p))
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    host, code = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else None)
    token = token_for(host, code)
    files = private_files()
    audio = [name.split('/', 1)[1] for name, _ in files if name.startswith('audio/')]
    meta = json.loads((ROOT / 'launcher/audio/voices.json').read_text(encoding='utf-8'))
    voices = {'order': [f for f in meta.get('order', []) if f in audio] + [f for f in audio if f not in meta.get('order', [])],
              'names': {f: meta.get('names', {}).get(f, Path(f).stem) for f in audio}}
    for name, path in files:
        r = api(host, 'asset?path=' + name, token=token, raw=path.read_bytes())
        print(('copied ' if r.get('returnValue') else 'FAILED ') + name)
    if audio:
        r = api(host, 'asset?path=audio/voices.json', token=token, raw=json.dumps(voices, ensure_ascii=False).encode())
        print('voices:', ', '.join(voices['names'][f] for f in voices['order']) if r.get('returnValue') else 'FAILED voices.json')
    if not files:
        print('No private files found in launcher/fonts or launcher/audio.')


if __name__ == '__main__':
    main()
