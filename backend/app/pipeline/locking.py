"""Nonblocking cross-process locks for the local SQLite deployment."""
import hashlib
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from ..config import settings

class JobBusy(RuntimeError):
    pass

@contextmanager
def exclusive_job(name: str):
    # Stable across CLI and API processes sharing one database; no credential data.
    digest = hashlib.sha256(settings.database_url.encode()).hexdigest()[:20]
    path = Path(tempfile.gettempdir()) / f"risk-radar-{digest}-{name}.lock"
    with path.open("a+b") as handle:
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise JobBusy(f"{name} is already running") from exc
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)
