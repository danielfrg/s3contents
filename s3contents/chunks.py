"""Bounded-memory sessions for Jupyter chunked file uploads."""

import base64
import binascii
import threading
import time
from dataclasses import dataclass
from typing import Any

from tornado.web import HTTPError


@dataclass
class UploadSession:
    writer: Any
    format: str
    next_chunk: int
    last_activity: float


class ChunkUploads:
    """Own buffered writers for one contents manager.

    Only the final chunk publishes an object. A first chunk restarts an upload;
    missing or out-of-order chunks are rejected rather than silently corrupting
    the file. Sessions are process-local, matching Jupyter's upload protocol.
    """

    def __init__(self, log, timeout=3600):
        self.log = log
        self.timeout = timeout
        self.sessions = {}
        self._lock = threading.RLock()
        self._timer = None

    def write(self, fs, path, chunk, content, format):
        with self._lock:
            try:
                if type(chunk) is not int or (chunk < 1 and chunk != -1):
                    raise HTTPError(400, "Chunk must be an integer >=1 or -1")
                if format not in ("text", "base64"):
                    raise HTTPError(400, "Chunk format must be text or base64")
                if not isinstance(content, str):
                    raise HTTPError(400, "Chunk content must be a string")
                if chunk == 1:
                    self.abort(path)
                else:
                    session = self.sessions.get(path)
                    if session is None:
                        raise HTTPError(409, "Restart upload with chunk 1")
                    if chunk != -1 and chunk != session.next_chunk:
                        raise HTTPError(409, "Chunks must arrive in order")
                    if format != session.format:
                        raise HTTPError(400, "Chunk format changed")

                try:
                    data = (
                        content.encode("utf8")
                        if format == "text"
                        else base64.b64decode(
                            content.encode("ascii"),
                            validate=True,
                        )
                    )
                except (UnicodeError, binascii.Error) as error:
                    raise HTTPError(400, "Invalid chunk encoding") from error

                if chunk == 1:
                    session = UploadSession(
                        fs.open_upload(path), format, 2, time.monotonic()
                    )
                    self.sessions[path] = session

                # Keep intermediate writes on backend block boundaries. GCS
                # requires nonfinal resumable parts to be 256 KiB aligned, even
                # when incoming Jupyter chunks have arbitrary sizes.
                writer = session.writer
                view = memoryview(data)
                offset = 0
                while offset < len(view):
                    remaining = writer.blocksize - writer.buffer.tell()
                    end = min(len(view), offset + remaining)
                    session.writer.write(view[offset:end])
                    offset = end
                session.last_activity = time.monotonic()
                if chunk == -1:
                    # Only the final request may finalize the remote object.
                    # Send GCS's short tail as a final part, without flushing
                    # with autocommit=False before a separate commit.
                    session.writer.autocommit = True
                    session.writer.close()
                    session.writer.buffer = None
                    del self.sessions[path]
                else:
                    session.next_chunk = chunk + 1
                self._schedule_cleanup()
            except Exception:
                self.abort(path)
                raise

    def abort(self, path, recursive=False):
        """Discard sessions without publishing partial data."""
        with self._lock:
            if recursive:
                cancelled = False
                prefix = path + "/"
                for upload_path in list(self.sessions):
                    if upload_path == path or upload_path.startswith(prefix):
                        cancelled = self.abort(upload_path) or cancelled
                return cancelled
            session = self.sessions.pop(path, None)
            if session is None:
                return False
            writer = session.writer
            # Both backends inherit a destructor that calls close(). Prevent it
            # from flushing even if discard fails or no remote session exists.
            writer.autocommit = False
            writer.closed = True
            try:
                writer.discard()
            except Exception:
                self.log.warning(
                    "Could not discard upload for %s",
                    path,
                    exc_info=True,
                )
            finally:
                writer.buffer = None
                self._schedule_cleanup()
            return True

    def _schedule_cleanup(self):
        if not self.sessions:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
        elif self._timer is None:
            deadline = min(s.last_activity for s in self.sessions.values())
            delay = max(0.001, deadline + self.timeout - time.monotonic())
            self._timer = threading.Timer(delay, self._expire)
            self._timer.daemon = True
            self._timer.start()

    def _expire(self):
        with self._lock:
            # A canceled callback may already be waiting on this lock while a
            # restart installs a new timer. Only that timer owns cleanup.
            if self._timer is not threading.current_thread():
                return
            # Keep _timer set during aborts so they do not schedule another
            # callback until every stale session has been considered.
            now = time.monotonic()
            for path, session in list(self.sessions.items()):
                if now - session.last_activity >= self.timeout:
                    self.abort(path)
            self._timer = None
            self._schedule_cleanup()

    def close(self):
        """Discard unfinished uploads when the owner shuts down."""
        with self._lock:
            for path in list(self.sessions):
                self.abort(path)
