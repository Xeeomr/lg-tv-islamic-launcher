#!/usr/bin/env python3
"""Execute the pinned ARM32 interpreter under Linux QEMU; never contact a TV."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cytv.python_runtime import prime_cache, normalize_to_file

SMOKE = r'''
import fcntl, hashlib, json, math, os, pathlib, select, socket, ssl, struct
import subprocess, sys, tarfile, tempfile, threading, time, zlib
assert sys.version_info[:2] == (3, 13)
assert struct.calcsize('P') == 4
assert zlib.decompress(zlib.compress(b'cytv')) == b'cytv'
assert hashlib.sha256(b'cytv').hexdigest()
assert ssl.OPENSSL_VERSION
assert time.monotonic() <= time.monotonic()
with tempfile.TemporaryDirectory() as directory:
    root = pathlib.Path(directory)
    with (root/'lock').open('wb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(lock, fcntl.LOCK_UN)
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        (root/'before').write_bytes(b'cytv')
        os.replace(root/'before', root/'after')
        assert (root/'after').read_bytes() == b'cytv'
        os.fsync(fd)
    finally:
        os.close(fd)
assert subprocess.check_output(['/bin/sh', '-c', 'printf CYTV_CHILD'], timeout=20) == b'CYTV_CHILD'
print(json.dumps({'arm32': True, 'python': sys.version.split()[0], 'smoke': 'passed'}))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir', type=Path, default=ROOT/'build/python-runtime-cache')
    parser.add_argument('--qemu', default='qemu-arm')
    parser.add_argument('--sysroot', default='/usr/arm-linux-gnueabi')
    args = parser.parse_args()
    archive = prime_cache(args.cache_dir, print)
    with tempfile.TemporaryDirectory(prefix='cytv-arm-python-') as tmp:
        directory = Path(tmp)
        normalized = directory/'runtime.tar.gz'
        inventory = normalize_to_file(archive.read_bytes(), normalized)
        tree = directory/'tree'
        tree.mkdir()
        # Production normalization admits only regular files/directories. Keep
        # the same restriction here before writing any host files.
        with tarfile.open(normalized, 'r:gz') as contents:
            for item in contents:
                path = Path(item.name)
                if path.is_absolute() or '..' in path.parts or not (item.isfile() or item.isdir()):
                    raise ValueError('Unexpected normalized runtime entry')
                target = tree/path
                if item.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with contents.extractfile(item) as source, target.open('xb') as output:
                        import shutil
                        shutil.copyfileobj(source, output, 256*1024)
                    target.chmod(item.mode)
        result = subprocess.run([args.qemu, '-L', args.sysroot, str(tree/'bin/python3.13'),
                                 '-I', '-B', '-c', SMOKE], text=True,
                                capture_output=True, timeout=120)
        if result.returncode:
            print(result.stderr, file=sys.stderr)
            result.check_returncode()
        print(result.stdout.strip())
        print('Verified normalized runtime files:', len(inventory['files']))
        print('QEMU smoke is not physical-TV, boot or rollback acceptance.')


if __name__ == '__main__':
    main()
