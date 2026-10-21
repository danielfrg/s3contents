"""Exercise real GCS buffered writers without credentials or network access."""

import base64
import hashlib
import json
import logging

import gcsfs
import pytest
from gcsfs.core import GCSFile

from s3contents.chunks import ChunkUploads
from s3contents.gcs.gcs_fs import GCSFS
from s3contents.genericfs import GenericFS

BLOCK_SIZE = 5 * 1024**2
GCS_GRANULARITY = 256 * 1024
OBJECT_KEY = "prefix/file.bin"
ORIGINAL = b"previous complete object"


class ResumableTransport:
    """Implement GCS's resumable HTTP contract beneath the real gcsfs code."""

    def __init__(self):
        self.objects = {OBJECT_KEY: ORIGINAL}
        self.sessions = {}
        self.requests = []
        self.finalized = []
        self.cancelled = []
        self.fail_finalization = False
        self._next_session = 0

    async def request(self, method, path, *args, **kwargs):
        if kwargs.get("uploadType") == "resumable":
            assert method == "POST"
            assert "/upload/storage/v1/b/test-bucket/o" in path
            self._next_session += 1
            location = (
                "https://storage.googleapis.com/resumable-upload/"
                f"{self._next_session}"
            )
            self.sessions[location] = {
                "key": kwargs["json"]["name"],
                "data": bytearray(),
            }
            return 200, {"Location": location}, None, b""

        assert path in self.sessions, f"Unknown resumable session: {path}"
        if method == "DELETE":
            self.cancelled.append(path)
            del self.sessions[path]
            return 204, {}, None, b""

        assert method == "POST"
        session = self.sessions[path]
        data = bytes(kwargs.get("data") or b"")
        headers = kwargs["headers"]
        content_range = headers["Content-Range"]
        assert int(headers["Content-Length"]) == len(data)
        self.requests.append((content_range, len(data)))
        interval, total = content_range.removeprefix("bytes ").split("/")
        final = total != "*"
        if interval == "*":
            assert final and not data
        else:
            start, end = map(int, interval.split("-"))
            assert start == len(session["data"])
            assert end == start + len(data) - 1

        # The real API rejects unaligned nonfinal chunks. Keep this validation
        # at the HTTP boundary, rather than replacing any GCSFile methods.
        if not final and len(data) % GCS_GRANULARITY:
            raise ValueError("GCS intermediate chunk must align to 256 KiB")
        if final and self.fail_finalization:
            self.fail_finalization = False
            raise OSError("simulated GCS finalization failure")

        session["data"].extend(data)
        if not final:
            assert session["data"]
            return (
                308,
                {"Range": f"bytes=0-{len(session['data']) - 1}"},
                None,
                b"",
            )

        assert int(total) == len(session["data"])
        complete = bytes(session["data"])
        self.objects[session["key"]] = complete
        self.finalized.append(session["key"])
        del self.sessions[path]
        checksum = base64.b64encode(hashlib.md5(complete).digest()).decode()
        metadata = {
            "size": str(len(complete)),
            "generation": str(len(self.finalized)),
            "md5Hash": checksum,
        }
        return 200, {}, None, json.dumps(metadata).encode()


@pytest.fixture
def gcs_upload(monkeypatch):
    backend = gcsfs.GCSFileSystem(
        project="streaming-tests",
        token="anon",
        consistency="md5",
        skip_instance_cache=True,
    )
    transport = ResumableTransport()
    monkeypatch.setattr(backend, "_request", transport.request)
    # Bypass only the adapter's startup directory probes; upload creation and
    # all buffering, checksums, flushes, completion and discard stay real.
    adapter = GCSFS.__new__(GCSFS)
    GenericFS.__init__(adapter, bucket="test-bucket", prefix="prefix")
    adapter.fs = backend
    adapter.log = logging.getLogger(__name__)
    uploads = ChunkUploads(adapter.log)
    yield uploads, adapter, transport
    uploads.close()
    assert not uploads.sessions
    assert not transport.sessions
    assert not backend.transaction.files


def write_chunk(gcs_upload, number, data):
    uploads, adapter, _ = gcs_upload
    uploads.write(
        adapter, "file.bin", number, base64.b64encode(data).decode(), "base64"
    )


@pytest.mark.parametrize(
    "first,last,expected",
    [
        (b"small ", b"object", b"small object"),
        (b"", b"", b""),
        (b"\x00\xff", b"\x80\x01", b"\x00\xff\x80\x01"),
    ],
    ids=["small", "empty", "binary"],
)
def test_gcs_publishes_complete_object_only_on_final_chunk(
    gcs_upload, first, last, expected
):
    uploads, adapter, transport = gcs_upload
    write_chunk(gcs_upload, 1, first)
    writer = uploads.sessions["file.bin"].writer
    assert isinstance(writer, GCSFile)
    assert writer.mode == "wb"
    assert writer.blocksize == BLOCK_SIZE
    assert writer.autocommit is False
    assert writer.path == "test-bucket/" + OBJECT_KEY
    assert transport.objects[OBJECT_KEY] == ORIGINAL
    assert not transport.finalized
    assert not adapter.fs.transaction.files

    write_chunk(gcs_upload, -1, last)
    assert transport.objects[OBJECT_KEY] == expected
    assert transport.finalized == [OBJECT_KEY]
    assert not uploads.sessions
    assert not transport.sessions
    assert writer.closed
    assert writer.buffer is None


def test_gcs_unaligned_client_chunks_obey_resumable_block_requirements(
    gcs_upload,
):
    uploads, _, transport = gcs_upload
    first = b"x" * (BLOCK_SIZE + 23)
    middle = b"y" * (GCS_GRANULARITY + 7)
    last = b"final"
    write_chunk(gcs_upload, 1, first)
    writer = uploads.sessions["file.bin"].writer
    assert transport.objects[OBJECT_KEY] == ORIGINAL
    uploaded = sum(len(s["data"]) for s in transport.sessions.values())
    assert uploaded == BLOCK_SIZE
    assert writer.buffer.tell() == 23

    write_chunk(gcs_upload, 2, middle)
    assert transport.objects[OBJECT_KEY] == ORIGINAL
    assert not transport.finalized
    # This unaligned tail exceeds GCS's minimum chunk size. It must stay
    # buffered until completion, which sends a final request with total size.
    assert writer.buffer.tell() == 23 + len(middle)
    write_chunk(gcs_upload, -1, last)
    assert transport.objects[OBJECT_KEY] == first + middle + last
    assert transport.finalized == [OBJECT_KEY]
    assert transport.requests[0] == (f"bytes 0-{BLOCK_SIZE - 1}/*", BLOCK_SIZE)
    assert not transport.requests[-1][0].endswith("/*")
    assert writer.closed
    assert writer.buffer is None


@pytest.mark.parametrize(
    "flushed",
    [False, True],
    ids=["buffered", "streamed"],
)
def test_gcs_abort_preserves_original_and_never_finalizes(gcs_upload, flushed):
    uploads, _, transport = gcs_upload
    data = b"unfinished" if not flushed else b"x" * BLOCK_SIZE + b"tail"
    write_chunk(gcs_upload, 1, data)
    writer = uploads.sessions["file.bin"].writer
    assert bool(transport.sessions) == flushed
    assert uploads.abort("file.bin") is True
    assert not uploads.sessions
    assert not transport.sessions
    assert transport.objects[OBJECT_KEY] == ORIGINAL
    assert not transport.finalized
    assert bool(transport.cancelled) == flushed
    assert writer.closed
    assert writer.buffer is None
    # Destruction or an owner calling close again must never publish a tail.
    writer.close()
    assert transport.objects[OBJECT_KEY] == ORIGINAL
    assert not transport.finalized


@pytest.mark.parametrize("flushed", [False, True], ids=["small", "streamed"])
def test_gcs_finalize_failure_cleans_up_and_allows_retry(gcs_upload, flushed):
    uploads, _, transport = gcs_upload
    first = b"new" if not flushed else b"x" * BLOCK_SIZE + b"tail"
    write_chunk(gcs_upload, 1, first)
    writer = uploads.sessions["file.bin"].writer
    transport.fail_finalization = True
    with pytest.raises(OSError, match="simulated GCS finalization failure"):
        write_chunk(gcs_upload, -1, b"end")
    assert transport.objects[OBJECT_KEY] == ORIGINAL
    assert not transport.finalized
    assert not transport.sessions
    assert not uploads.sessions
    assert transport.cancelled
    assert writer.closed
    assert writer.buffer is None

    write_chunk(gcs_upload, 1, b"replacement")
    write_chunk(gcs_upload, -1, b"!")
    assert transport.objects[OBJECT_KEY] == b"replacement!"
    assert transport.finalized == [OBJECT_KEY]
