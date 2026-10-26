#!/usr/bin/env python3
"""Read-only diagnosis. No root exploits or firmware compatibility guesses."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

FIELDS = {'uid', 'kernel_arch', 'kernel_release', 'userspace_bits',
          'webos_release', 'webos_build', 'starfish_release', 'starfish_build',
          'effective_capabilities', 'no_new_privileges', 'mount_namespace',
          'luna-send_present', 'systemctl_present'}

def destination(value):
    if not re.fullmatch(r'(?:[A-Za-z0-9_][A-Za-z0-9_.-]*@)?[A-Za-z0-9][A-Za-z0-9_.-]*', value):
        raise ValueError('Use a hostname or IPv4 address, optionally preceded by user@.')
    return value

def parse(text):
    observations = {}
    for line in text.splitlines():
        key, sep, value = line.partition('=')
        if not sep or key not in FIELDS:
            continue
        if not value or len(value) > 200 or any(ord(c) < 32 or ord(c) > 126 for c in value):
            continue
        if key in observations:
            raise ValueError('Ambiguous duplicate field: ' + key)
        observations[key] = value.strip('"')
    uid = observations.get('uid', '')
    root = 'UNKNOWN'
    if uid.isdecimal():
        root = 'UID_ZERO_CONTEXT_UNVERIFIED' if int(uid) == 0 else 'NOT_ROOT_IN_THIS_SESSION'
    return {'schema_version': 1, 'observations': observations, 'root_status': root,
            'rootability': 'NOT_DETERMINED_BY_PROBE',
            'integration_status': 'NO_VALIDATED_ADAPTER',
            'limitations': ['UID and capabilities do not prove host-root access or persistence.',
                            'A non-root session does not prove root is absent elsewhere.',
                            'No exploit, write test, mount, service start or settings change is performed.',
                            'Kernel architecture and userspace bitness are separate observations.']}

def add_system_info(report, raw):
    info = json.loads(raw)
    if not isinstance(info, dict) or info.get('returnValue') is not True:
        raise ValueError('System information query did not succeed.')
    for key in ('modelName', 'firmwareVersion', 'sdkVersion'):
        value = info.get(key)
        if isinstance(value, str) and 0 < len(value) <= 100 and all(32 <= ord(c) < 127 for c in value):
            report['observations'][key] = value

def add_app_info(report, raw):
    reply = json.loads(raw)
    if not isinstance(reply,dict) or reply.get('returnValue') is not True:
        raise ValueError('App information query did not succeed.')
    info = reply.get('appInfo')
    if not isinstance(info,dict) or info.get('id') != 'com.gathin.tvhome' or info.get('type') != 'web':
        raise ValueError('Expected the registered web launcher.')
    categories = info.get('appCategory',[])
    if not isinstance(categories,list) or any(not isinstance(x,str) for x in categories):
        raise ValueError('Malformed app category data.')
    report['launcher'] = {'id':'com.gathin.tvhome',
                          'home_category':'REGISTERED' if 'home' in categories else 'MISSING'}
    version = info.get('version')
    if isinstance(version,str) and re.fullmatch(r'[0-9]+(?:\.[0-9]+){1,3}',version):
        report['launcher']['version'] = version
    report['limitations'].append('Home category registration alone does not validate native routing or rollback.')

def main():
    p = argparse.ArgumentParser(description=__doc__)
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument('--ssh', type=destination, help='Existing OpenSSH host alias or user@IPv4')
    source.add_argument('--input', type=Path, help='Parse saved collector output locally')
    p.add_argument('--port', type=int, default=22)
    p.add_argument('--system-info', type=Path, help='Optional locally saved getSystemInfo JSON')
    p.add_argument('--app-info', type=Path, help='Optional locally saved getAppInfo response for the launcher')
    p.add_argument('--output', type=Path, help='New local JSON file; refuses to overwrite')
    args = p.parse_args()
    if not 1 <= args.port <= 65535:
        p.error('Port must be between 1 and 65535.')
    try:
        if args.ssh:
            probe = Path(__file__).with_name('collect.sh').read_text()
            result = subprocess.run(['ssh', '-T', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                                     '-o', 'ConnectTimeout=10', '-p', str(args.port), args.ssh, 'sh -s'],
                                    input=probe, text=True, capture_output=True, timeout=25)
            if result.returncode:
                raise RuntimeError('SSH probe failed; check the existing SSH configuration and TV connectivity.')
            raw = result.stdout
        else:
            raw = args.input.read_text()
        report = parse(raw)
        if args.system_info:
            add_system_info(report, args.system_info.read_text())
        if args.app_info:
            add_app_info(report, args.app_info.read_text())
        payload = json.dumps(report, indent=2) + '\n'
        if args.output:
            with args.output.open('x') as f:
                f.write(payload)
        else:
            print(payload, end='')
        return 0 if report['root_status'] != 'UNKNOWN' else 2
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as e:
        print('Doctor failed: ' + str(e), file=sys.stderr)
        return 2

if __name__ == '__main__':
    sys.exit(main())
