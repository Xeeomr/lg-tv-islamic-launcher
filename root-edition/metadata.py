#!/usr/bin/env python3
"""Plan a reversible Home-category change locally. Never writes to the TV."""
import argparse
import base64
import binascii
import hashlib
import json
import os
from pathlib import Path
import sys

APP_ID = 'com.gathin.tvhome'
MAX_BYTES = 65536

class NumberToken:
    # Only constructed by the JSON decoder after validating JSON number syntax.
    def __init__(self, token): self.token = token


def encode(value):
    if isinstance(value,NumberToken): return value.token
    if isinstance(value,dict):
        return '{'+', '.join(json.dumps(k,ensure_ascii=False)+': '+encode(v) for k,v in value.items())+'}'
    if isinstance(value,list): return '['+', '.join(encode(v) for v in value)+']'
    return json.dumps(value,ensure_ascii=False,allow_nan=False)


class Conflict(ValueError):
    """Current metadata belongs to neither side of the planned change."""


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise ValueError('Duplicate JSON key: '+key)
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('Non-finite JSON constant: '+value)


def parse(raw):
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_BYTES:
        raise ValueError('Expected a nonempty manifest of at most 64 KiB')
    try:
        value = json.loads(raw.decode('utf-8'),object_pairs_hook=unique_object,
                           parse_constant=reject_constant,parse_int=NumberToken,parse_float=NumberToken)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError('Invalid UTF-8 JSON manifest') from exc
    if not isinstance(value,dict) or value.get('id') != APP_ID or value.get('type') != 'web':
        raise ValueError('Expected the existing web launcher manifest')
    if not isinstance(value.get('main'),str) or not value['main']:
        raise ValueError('Missing launcher entry point')
    categories = value.get('appCategory',[])
    if not isinstance(categories,list) or any(not isinstance(x,str) or not x for x in categories):
        raise ValueError('Invalid appCategory list')
    return value


def prepare(original):
    value = parse(original)
    required = 'home' not in value.get('appCategory',[])
    if required:
        value['appCategory'] = value.get('appCategory',[]) + ['home']
        candidate = (encode(value)+'\n').encode('utf-8')
        parse(candidate)
    else:
        candidate = original
    return {'version':1,'app_id':APP_ID,'change_required':required,
            'original_b64':base64.b64encode(original).decode('ascii'),
            'candidate_b64':base64.b64encode(candidate).decode('ascii'),
            'original_sha256':digest(original),'candidate_sha256':digest(candidate)}


def validate(journal):
    if not isinstance(journal,dict) or type(journal.get('version')) is not int or journal.get('version') != 1 or type(journal.get('change_required')) is not bool or journal.get('app_id') != APP_ID:
        raise ValueError('Invalid metadata plan')
    decoded = []
    for side in ('original','candidate'):
        value = journal.get(side+'_b64')
        if not isinstance(value,str) or len(value)>4*((MAX_BYTES+2)//3):
            raise ValueError('Invalid or oversized metadata snapshot')
        try: raw = base64.b64decode(value,validate=True)
        except (ValueError,binascii.Error) as exc: raise ValueError('Invalid metadata encoding') from exc
        parse(raw)
        if digest(raw) != journal.get(side+'_sha256'): raise ValueError('Snapshot digest mismatch')
        decoded.append(raw)
    # Hashes alone cannot authorize an unrelated mutation. Recompute the only
    # allowed transformation, including exact no-op representation.
    expected = prepare(decoded[0])
    if any(journal.get(k) != v for k,v in expected.items()):
        raise ValueError('Plan is not the allowed Home-category transformation')
    return tuple(decoded)


def recovery(current, journal):
    original,candidate = validate(journal)
    if current == original: return None
    if current == candidate: return original
    raise Conflict('Metadata changed independently; preserve it for review')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True,help='Local copy of the actual appinfo.json, not getAppInfo output')
    p.add_argument('--output',type=Path,required=True,help='New local plan; existing files are preserved')
    args=p.parse_args()
    try:
        with args.input.open('rb') as f: raw=f.read(MAX_BYTES+1)
        plan=prepare(raw)
        fd=os.open(args.output,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as f:
            json.dump(plan,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        print('Local plan saved. TV metadata, registration cache and profiles were not changed.')
        return 0
    except (OSError,ValueError) as exc:
        print('Metadata plan failed: '+str(exc),file=sys.stderr);return 2

if __name__=='__main__':sys.exit(main())
