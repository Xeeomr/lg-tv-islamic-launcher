"""Refuse overlapping input ownership; never alter the existing helper's latch.

The legacy helper's Q command sets blocked, and manual relaunch clears blocked.
It has no reversible pause protocol, so using stop/relaunch loses user intent.
"""
import os
from pathlib import Path

APP = Path('/media/developer/apps/usr/palm/applications/com.local.nativehome')
STATE = APP/'state'
PROC = Path('/proc')


def status():
    # Presence includes a symlink or stale PID: ambiguity must never permit overlap.
    controller = os.path.lexists(STATE/'controller.pid')
    blocked = os.path.lexists(STATE/'blocked')
    relay = False
    try:
        for process in PROC.iterdir():
            if not process.name.isdigit():
                continue
            try:
                args = (process/'cmdline').read_bytes().split(b'\0')
            except FileNotFoundError:
                continue  # Exited while enumerating.
            except PermissionError as exc:
                raise ValueError('Cannot verify exclusive input ownership') from exc
            if str(APP/'relay').encode() in args:
                relay = True
                break
    except OSError as exc:
        raise ValueError('Cannot inspect helper processes') from exc
    return {'controller_present':controller, 'relay_present':relay, 'blocked':blocked,
            'reversible_pause_supported':False}


def require_idle():
    current = status()
    if current['controller_present'] or current['relay_present']:
        raise ValueError('no-root-helper-active: legacy helper has no intent-preserving pause protocol; stop it explicitly before a Root trial')
    return current
