"""Verify installed recovery bytes; never claim on-device boot acceptance."""
import hashlib
from pathlib import Path
import device_adapter as d


def verify():
    d.trusted_dir(d.STATE)
    root = Path(__file__).resolve().parent
    d.trusted_dir(root)
    d.python_binding.verify_binding(d.STATE)
    proof = d.safe_json(d.STATE/'recovery-provision.json')
    if proof.get('version') != 1 or proof.get('mode') != 'recovery-only':
        raise ValueError('Recovery provisioning required')
    callback = Path(proof.get('boot_callback', ''))
    if not callback.is_absolute() or callback.parent == root:
        raise ValueError('Independent boot callback required')
    files = proof.get('files', {})
    required = {str(p) for p in root.glob('*.py')} | {str(callback)}
    required.update(str(d.STATE/name) for name in ('python_binding.py','python_boot.js','python-launcher','python-runtime.json') if (d.STATE/name).exists())
    if not required.issubset(files):
        raise ValueError('Incomplete recovery manifest')
    import os, stat
    for name in files:
        if not Path(name).is_absolute() or not Path(name).is_relative_to(d.STATE):
            raise ValueError('Recovery files must remain inside private root state')
        path = Path(name)
        for parent in path.parents:
            d.trusted_dir(parent)
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as f:
            st = os.fstat(f.fileno())
            if not stat.S_ISREG(st.st_mode) or st.st_uid != d.EXPECTED_UID or st.st_mode & 0o022 or st.st_nlink != 1 or st.st_size > 1048576:
                raise ValueError('Unsafe recovery file')
            content = f.read()
        if hashlib.sha256(content).hexdigest() != files[name]:
            raise ValueError('Recovery digest mismatch: '+name)
        if path == callback and (str(root/'cli.py')+' boot').encode() not in content:
            raise ValueError('Callback does not invoke recovery')
    return {'integrity_verified': True, 'hardware_validated': False,
            'persistent_enable_available': False}
