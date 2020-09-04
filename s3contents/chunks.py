"""
Utilities for managing chunked file uploads.
See https://jupyter-notebook.readthedocs.io/en/stable/extending/contents.html#chunked-saving
"""

import base64
import contextvars
import time


# Used as a "registry" for uploads.
content_chunks = contextvars.ContextVar("jupyterlab_content_chunks", default={})


def store_content_chunk(path: str, content: str):
    """Store a base64 chunk in the registry as bytes"""

    current_value = content_chunks.get()

    if path not in current_value:
        current_value[path] = {"started_at": time.time(), "chunks": []}

    current_value[path]["chunks"].append(
        base64.b64decode(content.encode("ascii"), validate=True)
    )


def assemble_chunks(path: str) -> str:
    """Assemble the chunk bytes into a single base64 string"""

    current_value = content_chunks.get()

    if path not in current_value:
        raise ValueError(f"No chunk for path {path}")

    return base64.b64encode(b"".join(current_value[path]["chunks"])).decode("ascii")


def delete_chunks(path):
    """Should be called once the upload is complete to free the memory"""

    current_value = content_chunks.get()
    del current_value[path]


def prune_stale_chunks():
    """Called periodically to avoid keeping large objects in memory
    when a chunked upload does not finish"""

    current_value = content_chunks.get()
    now = time.time()
    stale_paths = []

    for path, chunk_info in current_value.items():
        if now - chunk_info["started_at"] > 3600:
            stale_paths.append(path)

    for path in stale_paths:
        del current_value[path]
