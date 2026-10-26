"""Small root-owned JSON store. All operations are anchored to a checked dir fd."""
from contextlib import contextmanager
import fcntl
import json
import os
import re
import stat
import uuid

MAX_BYTES = 4 * 1024 * 1024


def encode(value):
    try:
        return json.dumps(value, ensure_ascii=False, allow_nan=False,
                          separators=(',', ':'), sort_keys=True).encode('utf-8')
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise ValueError('invalid JSON value') from error


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise ValueError('duplicate JSON key')
        result[key] = value
    return result


class Store:
    def __init__(self, root, uid=0):
        self.root = os.path.abspath(root)
        self.uid = uid
        if self.root == '/': raise ValueError('invalid store directory')
        parent = self._walk(os.path.dirname(self.root))
        try:
            try: os.mkdir(os.path.basename(self.root), 0o700, dir_fd=parent)
            except FileExistsError: pass
        finally:
            os.close(parent)
        os.close(self._directory())

    def _walk(self, path):
        fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            for part in path.strip('/').split('/'):
                if not part: continue
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = child
                info = os.fstat(fd)
                if (info.st_uid not in (0, self.uid)
                        or (info.st_mode & 0o022 and not info.st_mode & stat.S_ISVTX)):
                    raise ValueError('unsafe store ancestor')
            return fd
        except (OSError, ValueError) as error:
            os.close(fd)
            raise ValueError('unsafe store path') from error

    def _directory(self):
        fd = self._walk(self.root)
        try:
            info = os.fstat(fd)
            if info.st_uid != self.uid or info.st_mode & 0o022:
                raise ValueError('unsafe store ownership or permissions')
            return fd
        except (OSError, ValueError) as error:
            os.close(fd)
            raise ValueError('unsafe store directory') from error

    @staticmethod
    def _name(name):
        if not isinstance(name, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,127}(?:\.json)?', name):
            raise ValueError('unsafe store name')
        return name if name.endswith('.json') else name + '.json'

    def _check(self, info):
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != self.uid
                or info.st_mode & 0o022 or info.st_nlink != 1):
            raise ValueError('unsafe store file')
        if info.st_size > MAX_BYTES: raise ValueError('store file too large')

    def read(self, name):
        name = self._name(name)
        directory = self._directory()
        try:
            try:
                fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
            except FileNotFoundError:
                return None
            except OSError as error:
                raise ValueError('unsafe store file') from error
            with os.fdopen(fd, 'rb') as source:
                self._check(os.fstat(source.fileno()))
                raw = source.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES: raise ValueError('store file too large')
            try:
                value = json.loads(raw.decode('utf-8'), object_pairs_hook=_unique,
                                   parse_constant=lambda value: (_ for _ in ()).throw(ValueError('invalid number')))
                if value is None: raise ValueError('null is not a stored record')
                return value
            except (ValueError, UnicodeError, RecursionError) as error:
                raise ValueError('corrupt store JSON') from error
        finally:
            os.close(directory)

    def write(self, name, value):
        name = self._name(name)
        if value is None: raise ValueError('null is not a stored record')
        raw = encode(value)
        if len(raw) > MAX_BYTES: raise ValueError('store value too large')
        directory = self._directory()
        temporary = '.write-' + uuid.uuid4().hex
        try:
            try:
                self._check(os.stat(name, dir_fd=directory, follow_symlinks=False))
                if name.startswith('profile-'): raise ValueError('immutable profile exists')
            except FileNotFoundError:
                pass
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=directory)
            with os.fdopen(fd, 'wb') as target:
                target.write(raw)
                target.flush()
                os.fsync(target.fileno())
            if name.startswith('profile-'):
                os.link(temporary, name, src_dir_fd=directory, dst_dir_fd=directory,
                        follow_symlinks=False)
                os.unlink(temporary, dir_fd=directory)
            else:
                os.replace(temporary, name, src_dir_fd=directory, dst_dir_fd=directory)
            os.fsync(directory)
        finally:
            try: os.unlink(temporary, dir_fd=directory)
            except FileNotFoundError: pass
            os.close(directory)
        return value

    @contextmanager
    def lock(self):
        directory = self._directory()
        fd = None
        try:
            try:
                fd = os.open('worker.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                             0o600, dir_fd=directory)
                self._check(os.fstat(fd))
            except OSError as error:
                raise ValueError('unsafe worker lock') from error
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            if fd is not None:
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
            os.close(directory)
