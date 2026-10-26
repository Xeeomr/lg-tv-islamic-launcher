"""Prepare the staged Home app for a webOS 22+ TV (Chromium 87): drop the ES5-era polyfill bundle, keep
only the English UI catalog next to the Arabic one (both cut parse time on every cold launch), and list
the adhan recordings that are actually present in audio/."""
import json
import re
import subprocess
import sys
from pathlib import Path

app = Path(sys.argv[1] if len(sys.argv) > 1 else 'build/home-app')
index = app / 'index.html'
html = index.read_text(encoding='utf-8')
html = re.sub(r'\s*<script src="compat-polyfills\.js"></script>', '', html)
index.write_text(html, encoding='utf-8')
(app / 'compat-polyfills.js').unlink(missing_ok=True)

catalogs = app / 'catalogs.js'
script = ("const C={};global.HomeI18n={add:v=>{for(const l in v)C[l]=Object.assign(C[l]||{},v[l]);}};"
          "require(process.argv[1]);process.stdout.write(JSON.stringify({en:C.en||{}}));")
kept = subprocess.run(['node', '-e', script, str(catalogs.resolve())], capture_output=True, text=True, check=True).stdout
catalogs.write_text('HomeI18n.add(' + kept + ');\n', encoding='utf-8')
print('slimmed', app, 'catalogs', len(kept) // 1024, 'KB')

audio = app / 'audio'
meta = json.loads((audio / 'voices.json').read_text(encoding='utf-8')) if (audio / 'voices.json').exists() else {}
files = sorted(p.name for p in audio.iterdir() if p.suffix.lower() in ('.mp3', '.ogg', '.m4a')) if audio.exists() else []
order = [f for f in meta.get('order', []) if f in files] + [f for f in files if f not in meta.get('order', [])]
voices = [{'file': f, 'name': meta.get('names', {}).get(f, Path(f).stem)} for f in order]
(app / 'voices.js').write_text('window.PRAYER_VOICES=' + json.dumps(voices, ensure_ascii=False) + ';\n', encoding='utf-8')
print('voices:', ', '.join(v['name'] for v in voices) or 'none')
