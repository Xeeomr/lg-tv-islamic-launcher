#!/usr/bin/env python3
"""Explicit SSH host controller for an offline Root candidate bundle."""
import argparse
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
import uuid


def ssh_options(alias, identity=None):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', alias):
        raise ValueError('Use a single explicit OpenSSH host alias')
    options = ['-o', 'StrictHostKeyChecking=yes', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10']
    if identity is not None:
        options += ['-i', str(Path(identity).expanduser().resolve())]
    return options + [alias]


def execute(action, alias, bundle=None, identity=None, run=subprocess.run, migrate=False, transaction=None, python=None):
    if action not in ('install', 'status', 'trial', 'emergency-trial', 'intent-trial', 'enable', 'confirm', 'restore', 'uninstall'):
        raise ValueError('Unsupported action')
    if migrate and action != 'install':
        raise ValueError('Migration is only available with install')
    if action == 'confirm' and (not transaction or not re.fullmatch(r'[0-9a-f-]{36}',transaction)):
        raise ValueError('confirm requires the trial transaction ID')
    from python_binding import launcher_bytes
    selected = '/usr/bin/python3' if python is None else python
    launcher_bytes(selected)  # Whitelist before any SSH or staging mutation.
    options = ssh_options(alias, identity)
    remote_driver = '/var/lib/clean-your-tv-root/deploy.py'
    if action == 'install':
        from deploy import verify_bundle, checked_file
        if bundle is None: raise ValueError('install requires --bundle')
        bundle = Path(bundle).resolve()
        manifest = verify_bundle(bundle)
        staging = '/tmp/clean-your-tv-root-' + uuid.uuid4().hex
        # An exclusive, root-owned remote staging directory. No remote shell input
        # is derived from an application ID, profile, or unvalidated alias.
        remote = 'umask 077; test "$(id -u)" = 0 && mkdir ' + shlex.quote(staging)
        run(['ssh', *options, remote], check=True, stdin=subprocess.DEVNULL)
        with tempfile.TemporaryDirectory(prefix='root-bundle-') as temporary:
            local = Path(temporary)
            for name in (*manifest['files'], 'bundle.json'):
                target = local / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(checked_file(bundle, name))
            run(['scp', '-O', *options[:-1], '-r', *[str(p) for p in sorted(local.iterdir())], alias + ':' + staging + '/'],
                check=True, stdin=subprocess.DEVNULL)
        remote_driver = staging + '/deploy.py'
        argv = [selected, remote_driver, 'install', '--bundle', staging]
        if migrate:
            argv.append('--migrate-packaged-home')
        command = shlex.join(argv)
    else:
        argv = [selected, remote_driver, action]
        if action == 'confirm': argv += ['--transaction',transaction]
        command = shlex.join(argv)
    if selected != '/usr/bin/python3':
        command = 'unset PYTHONHOME PYTHONPATH; export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1; exec '+command
    return run(['ssh', *options, command], check=True, stdin=subprocess.DEVNULL)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('install', 'status', 'trial', 'emergency-trial', 'intent-trial', 'enable', 'confirm', 'restore', 'uninstall'))
    parser.add_argument('--ssh', required=True, help='Explicit, preconfigured OpenSSH alias')
    parser.add_argument('--transaction')
    parser.add_argument('--python', help='Already-provisioned, pinned TV interpreter path')
    parser.add_argument('--identity', type=Path)
    parser.add_argument('--bundle', type=Path)
    parser.add_argument('--migrate-packaged-home', action='store_true', help='Copy installed Home packaged preferences only; excludes browser storage')
    args = parser.parse_args()
    execute(args.command, args.ssh, args.bundle, args.identity, migrate=args.migrate_packaged_home,transaction=args.transaction,python=args.python)


if __name__ == '__main__':
    main()
