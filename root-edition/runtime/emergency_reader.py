"""Read-only observer for the validated ARM32 Magic Remote channel.

No EVIOCGRAB, input writes, reinjection, system library patches or key filtering.
"""
import errno
import fcntl
import os
import select
import stat
import struct
import sys
import time
from pathlib import Path
from emergency_gesture import TripleHome, LongBack
EVENT = struct.Struct('<IIHHi')
NAME = b'LGE M-RCU - Builtin [0]'


def query(fd, nr, size):
    value = bytearray(size)
    fcntl.ioctl(fd, 0x80000000 | (size << 16) | (ord('E') << 8) | nr, value, True)
    return value


def open_remote():
    if sys.byteorder != 'little' or struct.calcsize('@llHHi') != 16 or struct.calcsize('P') != 4:
        raise ValueError('Only the validated ARM32 input ABI is supported')
    found = []
    try:
        for path in sorted(Path('/dev/input').glob('event*')):
            try:
                fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC | os.O_NOFOLLOW)
            except OSError as exc:
                if exc.errno in (errno.ENXIO, errno.ENODEV, errno.ENOENT): continue
                raise
            try:
                if not stat.S_ISCHR(os.fstat(fd).st_mode): raise ValueError('Not an input device')
                if bytes(query(fd, 6, 256)).split(b'\0')[0] != NAME: continue
                found.append(fd); fd = None
            finally:
                if fd is not None: os.close(fd)
        if len(found) != 1: raise ValueError('Validated input channel missing or ambiguous')
        return found.pop()
    finally:
        for fd in found: os.close(fd)


def observe(fd, health, keys_released):
    os.set_blocking(fd, False)
    def send(message):
        data = message + b'\n'
        if os.write(health, data) != len(data): raise RuntimeError('Short health write')
    # Drain historical events before checking keys; never count a held startup key.
    for _ in range(64):
        try: data = os.read(fd, EVENT.size * 64)
        except BlockingIOError: break
        if not data: send(b'LOST'); return
    else: send(b'LOST'); return
    if not keys_released(): send(b'LOST'); return
    policy = TripleHome(); back = LongBack(); send(b'READY')
    while True:
        select.select([fd], [], [], .1)
        for _ in range(64):
            try: data = os.read(fd, EVENT.size * 64)
            except BlockingIOError: break
            if not data or len(data) % EVENT.size: send(b'LOST'); return
            for offset in range(0, len(data), EVENT.size):
                sec, usec, kind, code, value = EVENT.unpack_from(data, offset)
                if usec >= 1000000: send(b'LOST'); return
                try: fired = policy.event(kind, code, value, sec * 1000 + usec / 1000)
                except ValueError: send(b'LOST'); return
                back.event(kind, code, value, time.monotonic() * 1000)
                if fired: send(b'ESCAPE'); return
        else: send(b'LOST'); return
        if back.tick(time.monotonic() * 1000): send(b'LGHOME')
        send(b'PING')


if __name__ == '__main__':
    if os.geteuid() != 0 or len(sys.argv) != 2: raise SystemExit('Root and private health fd required')
    health = int(sys.argv[1]); fd = open_remote()
    try: observe(fd, health, lambda: not any(query(fd, 0x18, 256)))
    finally: os.close(fd); os.close(health)
