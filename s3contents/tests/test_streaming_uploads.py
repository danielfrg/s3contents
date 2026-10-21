"""Exercise the real s3fs writer against the MinIO service used in CI."""

import base64
import threading
import tracemalloc
import uuid

import pytest
from botocore.exceptions import ClientError
from s3fs.core import S3File
from tornado.web import HTTPError

from s3contents import S3ContentsManager

pytestmark = pytest.mark.minio


# The old MinIO image in CI does not enumerate multipart uploads reliably.
# Record IDs returned by the real backend and query ListParts for each one.
_created_uploads = []


@pytest.fixture(autouse=True)
def record_upload_ids(monkeypatch):
    original_call = S3File._call_s3

    def call(writer, method, *args, **kwargs):
        result = original_call(writer, method, *args, **kwargs)
        if method == "create_multipart_upload":
            upload = (writer.bucket, writer.key, result["UploadId"])
            _created_uploads.append(upload)
        return result

    monkeypatch.setattr(S3File, "_call_s3", call)
    yield
    _created_uploads.clear()


@pytest.fixture
def manager():
    cm = S3ContentsManager(
        access_key_id="access-key",
        secret_access_key="secret-key",
        endpoint_url="http://127.0.0.1:9000",
        bucket="notebooks",
        prefix="streaming-" + uuid.uuid4().hex,
        signature_version="s3v4",
    )
    yield cm
    if hasattr(cm, "_chunk_uploads"):
        cm._chunk_uploads.close()
    remove_test_files(cm)


def remove_test_files(cm):
    # Old CI MinIO requires Content-MD5 on bulk delete; DeleteObject works with
    # both old and current botocore releases.
    for path in cm.fs.fs.find(cm.fs.prefix_):
        _, key, _ = cm.fs.fs.split_path(path)
        cm.fs.fs.call_s3("delete_object", Bucket=cm.bucket, Key=key)


def save_chunk(cm, chunk, content, format="base64", path="file.bin"):
    return cm.save(
        {"type": "file", "chunk": chunk, "format": format, "content": content},
        path,
    )


def pending(cm):
    uploads = []
    for bucket, key, upload_id in _created_uploads:
        if bucket != cm.bucket or not key.startswith(cm.prefix + "/"):
            continue
        try:
            parts = cm.fs.fs.call_s3(
                "list_parts", Bucket=bucket, Key=key, UploadId=upload_id
            )
        except FileNotFoundError:
            pass
        except ClientError as error:
            if error.response["Error"]["Code"] != "NoSuchUpload":
                raise
        else:
            uploads.append(parts)
    return uploads


@pytest.mark.parametrize(
    "format,first,last,expected",
    [
        ("base64", "YWJj", "ZGVm", b"abcdef"),
        ("text", "hello ", "世界", "hello 世界".encode()),
        ("base64", "", "", b""),
    ],
)
def test_chunks_commit_only_at_end(manager, format, first, last, expected):
    model = save_chunk(manager, 1, first, format)
    assert model["path"] == "file.bin"
    assert not manager.file_exists("file.bin")
    save_chunk(manager, -1, last, format)
    assert manager.fs.fs.cat(manager.fs.path("file.bin")) == expected
    assert pending(manager) == []
    # fsspec's implicit transaction must not retain finished writers.
    assert not manager.fs.fs.transaction.files


def test_restart_discards_previous_chunks(manager):
    save_chunk(manager, 1, "b2xk")
    save_chunk(manager, 1, "bmV3")
    save_chunk(manager, -1, "IQ==")
    assert manager.fs.fs.cat(manager.fs.path("file.bin")) == b"new!"


@pytest.mark.parametrize("chunk", [2, -1])
def test_missing_upload_is_rejected(manager, chunk):
    with pytest.raises(HTTPError) as error:
        save_chunk(manager, chunk, "YWJj")
    assert error.value.status_code == 409
    assert not manager.file_exists("file.bin")


@pytest.mark.parametrize("chunk", [0, 3, 1.5, True])
def test_invalid_chunk_sequence_is_rejected(manager, chunk):
    save_chunk(manager, 1, "YWJj")
    with pytest.raises(HTTPError) as error:
        save_chunk(manager, chunk, "ZGVm")
    assert error.value.status_code in {400, 409}
    assert not manager.file_exists("file.bin")


def test_format_change_aborts_upload(manager):
    save_chunk(manager, 1, "YWJj")
    with pytest.raises(HTTPError) as error:
        save_chunk(manager, -1, "def", "text")
    assert error.value.status_code == 400
    assert not manager.file_exists("file.bin")


def test_malformed_chunk_preserves_existing_file(manager):
    manager.fs.write("file.bin", "original", "text")
    save_chunk(manager, 1, "YWJj")
    with pytest.raises(HTTPError) as error:
        save_chunk(manager, -1, "not base64!")
    assert error.value.status_code == 400
    assert manager.fs.fs.cat(manager.fs.path("file.bin")) == b"original"
    assert pending(manager) == []


def test_same_path_in_different_managers_is_isolated(manager):
    other = S3ContentsManager(
        access_key_id="access-key",
        secret_access_key="secret-key",
        endpoint_url="http://127.0.0.1:9000",
        bucket="notebooks",
        prefix=manager.prefix + "-other",
        signature_version="s3v4",
    )
    try:
        save_chunk(manager, 1, "YWJj")
        save_chunk(other, 1, "eHl6")
        save_chunk(manager, -1, "IQ==")
        save_chunk(other, -1, "Pw==")
        assert manager.fs.fs.cat(manager.fs.path("file.bin")) == b"abc!"
        assert other.fs.fs.cat(other.fs.path("file.bin")) == b"xyz?"
    finally:
        if hasattr(other, "_chunk_uploads"):
            other._chunk_uploads.close()
        remove_test_files(other)


@pytest.mark.parametrize(
    "operation", ["put_object", "upload_part", "complete_multipart_upload"]
)
def test_backend_failure_discards_upload_and_preserves_original(
    manager, monkeypatch, operation
):
    manager.fs.write("file.bin", "original", "text")
    first = b"small" if operation == "put_object" else b"x" * (5 * 1024**2)
    save_chunk(manager, 1, base64.b64encode(first).decode())
    assert bool(pending(manager)) == (operation != "put_object")
    writer = manager._chunk_uploads.sessions["file.bin"].writer
    original_call = writer._call_s3

    def fail_operation(method, *args, **kwargs):
        if method == operation:
            raise OSError("simulated backend failure")
        return original_call(method, *args, **kwargs)

    monkeypatch.setattr(writer, "_call_s3", fail_operation)
    with pytest.raises(HTTPError) as error:
        save_chunk(manager, -1, "ZGVm")
    assert error.value.status_code == 500
    assert writer.closed
    assert manager.fs.fs.cat(manager.fs.path("file.bin")) == b"original"
    assert pending(manager) == []
    # A fresh upload must work after an error.
    save_chunk(manager, 1, "bmV3")
    save_chunk(manager, -1, "IQ==")
    assert manager.fs.fs.cat(manager.fs.path("file.bin")) == b"new!"


def test_delete_cancels_unfinished_upload(manager):
    block = base64.b64encode(b"x" * (5 * 1024**2)).decode()
    save_chunk(manager, 1, block)
    assert pending(manager)
    manager.delete_file("file.bin")
    assert pending(manager) == []
    assert not manager.file_exists("file.bin")


@pytest.mark.parametrize("streamed", [False, True])
def test_idle_upload_expires_without_requests(manager, monkeypatch, streamed):
    manager._chunk_uploads.timeout = 0.2
    first = b"x" * (5 * 1024**2) if streamed else b"abc"
    save_chunk(manager, 1, base64.b64encode(first).decode())
    writer = manager._chunk_uploads.sessions["file.bin"].writer
    discarded = threading.Event()
    original_discard = writer.discard

    def discard():
        try:
            original_discard()
        finally:
            discarded.set()

    monkeypatch.setattr(writer, "discard", discard)
    assert discarded.wait(3), "idle upload was never discarded"
    assert not manager.file_exists("file.bin")
    assert pending(manager) == []


def test_memory_is_bounded_by_buffer_not_file_size(manager):
    # Reuse the request body so the measurement covers server-side storage.
    chunk = base64.b64encode(b"x" * 1024**2).decode()
    tracemalloc.start()
    try:
        for number in range(1, 41):
            save_chunk(manager, number, chunk)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < 24 * 1024**2
    assert pending(manager), "parts were not streamed to S3"
    save_chunk(manager, -1, "IQ==")
    size = manager.fs.fs.info(manager.fs.path("file.bin"))["size"]
    assert size == 40 * 1024**2 + 1
    assert pending(manager) == []


def test_regular_save_cancels_previous_chunked_upload(manager):
    save_chunk(manager, 1, "b2xk")
    manager.save(
        {"type": "file", "format": "text", "content": "new"},
        "file.bin",
    )
    with pytest.raises(HTTPError) as error:
        save_chunk(manager, -1, "IQ==")
    assert error.value.status_code == 409
    assert manager.fs.fs.cat(manager.fs.path("file.bin")) == b"new"


def test_invalid_format_aborts_existing_upload(manager):
    save_chunk(manager, 1, "YWJj")
    with pytest.raises(HTTPError) as error:
        save_chunk(manager, -1, "ZGVm", [])
    assert error.value.status_code == 400
    assert not manager.file_exists("file.bin")


def test_interleaved_uploads_to_different_files(manager):
    save_chunk(manager, 1, "YWJj", path="a.bin")
    save_chunk(manager, 1, "eHl6", path="b.bin")
    save_chunk(manager, -1, "Pw==", path="b.bin")
    save_chunk(manager, -1, "IQ==", path="a.bin")
    assert manager.fs.fs.cat(manager.fs.path("a.bin")) == b"abc!"
    assert manager.fs.fs.cat(manager.fs.path("b.bin")) == b"xyz?"


def test_save_hooks_run_once_and_post_hook_sees_final_object(manager):
    events = []

    def pre_save(model, path, contents_manager):
        events.append(("pre", path))
        model["content"] = "SEk="

    def post_save(s3_path, model, contents_manager):
        fs = contents_manager.fs
        events.append(("post", fs.fs.cat(fs.path(s3_path))))

    manager.pre_save_hook = pre_save
    manager.post_save_hook = post_save
    save_chunk(manager, 1, "YWJj")
    save_chunk(manager, 2, "IQ==")
    assert events == [("pre", "file.bin")]
    save_chunk(manager, -1, "Pw==")
    assert events == [("pre", "file.bin"), ("post", b"HI!?")]


def test_delete_directory_cancels_uploads_beneath_it(manager):
    save_chunk(manager, 1, "YWJj", path="folder/a.bin")
    save_chunk(manager, 1, "ZGVm", path="folder/b.bin")
    save_chunk(manager, 1, "eHl6", path="folder-other/c.bin")
    manager.delete_file("folder")
    for path in ("folder/a.bin", "folder/b.bin"):
        with pytest.raises(HTTPError) as error:
            save_chunk(manager, -1, "IQ==", path=path)
        assert error.value.status_code == 409
    save_chunk(manager, -1, "IQ==", path="folder-other/c.bin")
    assert manager.fs.fs.cat(manager.fs.path("folder-other/c.bin")) == b"xyz!"


def test_cancelled_cleanup_callback_does_not_replace_new_timer(manager):
    uploads = manager._chunk_uploads
    uploads.timeout = 0.1
    save_chunk(manager, 1, "YWJj")
    old_timer = uploads._timer
    callback_started = threading.Event()
    original_callback = old_timer.function

    def callback():
        callback_started.set()
        original_callback()

    with uploads._lock:
        old_timer.function = callback
        assert callback_started.wait(3)
        # The expired callback is waiting for this lock while a restart cancels
        # its timer and installs a new one. It must not replace that new timer.
        uploads.abort("file.bin")
        uploads.timeout = 60
        save_chunk(manager, 1, "bmV3")
        new_timer = uploads._timer
    old_timer.join(3)
    assert not old_timer.is_alive()
    assert uploads._timer is new_timer
    save_chunk(manager, -1, "IQ==")
    assert manager.fs.fs.cat(manager.fs.path("file.bin")) == b"new!"
