"""Own exactly one normal-boot marker hook; never edit Homebrew startup code."""
import json
import os
from pathlib import Path
import stat
from python_binding import command as python_command

HOOK = Path('/var/lib/webosbrew/init.d/50-clean-your-tv-root')
STATE = Path('/var/lib/clean-your-tv-root')
CONTENT = b'#!/bin/sh\nexec /usr/bin/python3 /var/lib/clean-your-tv-root/runtime/boot_gate.py mark\n'


def managed_content():
    return ('#!/bin/sh\nexec /bin/sh '+str(STATE/'service/boot-recover.sh')+' mark\n').encode()


def previous_managed_content():
    return ('#!/bin/sh\nexec '+str(STATE/'python-launcher')+' /var/lib/clean-your-tv-root/runtime/boot_gate.py mark\n').encode()


def owned(saved):
    if (saved.get('version') != 1 or saved.get('path') != str(HOOK)
            or set(saved) != {'version','path','content'}
            or saved.get('content') not in (CONTENT.decode(),managed_content().decode(),previous_managed_content().decode())):
        raise ValueError('Unexpected startup hook receipt')
    return saved['content'].encode()


def trusted_hook_directory():
    for parent in (HOOK.parent, *HOOK.parent.parents):
        info=parent.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
            raise ValueError('Unsafe startup hook directory')


def install(secure, write):
    receipt=STATE/'startup-hook.json'
    trusted_hook_directory()
    # Existing receipts retain their interpreter identity for rollback.
    if os.path.lexists(receipt):
        content=owned(json.loads(secure(receipt)))
        if content == previous_managed_content():
            raise ValueError('Unvalidated managed startup hook requires recovery and reprovisioning')
        if os.path.lexists(HOOK):
            if secure(HOOK) != content or stat.S_IMODE(HOOK.stat().st_mode) != 0o700:
                raise ValueError('Startup hook drift')
            return
    else:
        if os.path.lexists(HOOK): raise ValueError('Startup hook name collision')
        content = CONTENT if python_command(STATE) == '/usr/bin/python3' else managed_content()
        write(receipt,json.dumps({'version':1,'path':str(HOOK),'content':content.decode()}))
    write(HOOK,content,0o700)


def remove(secure):
    receipt=STATE/'startup-hook.json'
    if not os.path.lexists(receipt): return
    content=owned(json.loads(secure(receipt)))
    if os.path.lexists(HOOK):
        if secure(HOOK) != content: raise ValueError('Startup hook drift')
        HOOK.unlink()
    # Retain ownership evidence for interrupted/repeated uninstall.
