"""
Utilities for managing compat between notebook versions.

Taken from: https://github.com/quantopian/pgcontents/blob/master/pgcontents/utils/ipycompat.py
"""

import notebook
from ipython_genutils.importstring import import_item
from ipython_genutils.py3compat import string_types
from nbformat import from_dict, reads, writes
from nbformat.v4.nbbase import (
    new_code_cell,
    new_markdown_cell,
    new_notebook,
    new_raw_cell,
)
from nbformat.v4.rwbase import strip_transient
from notebook.services.contents.checkpoints import (
    Checkpoints,
    GenericCheckpointsMixin,
)

# Ref. https://github.com/jupyter/nbdime/blob/c82362344e596efdc4f54c927d90338940e0fa41/nbdime/webapp/nb_server_extension.py#L16-L33
# This allows solving conflicts between the class import from either notebook or jupyter_server
try:
    from notebook.services.contents.filecheckpoints import GenericFileCheckpoints
    from notebook.services.contents.filemanager import FileContentsManager
    from notebook.services.contents.manager import ContentsManager
except ModuleNotFoundError:
    pass

try:
    from jupyter_server.services.contents.filecheckpoints import GenericFileCheckpoints
    from jupyter_server.services.contents.filemanager import FileContentsManager
    from jupyter_server.services.contents.manager import ContentsManager
except ModuleNotFoundError:
    pass

from notebook.utils import to_os_path
from traitlets import (
    Any,
    Bool,
    Dict,
    HasTraits,
    Instance,
    Integer,
    TraitError,
    Unicode,
    validate,
)
from traitlets.config import Config

if notebook.version_info[0] >= 7:  # noqa
    raise ImportError("Jupyter Notebook versions 6 and up are not supported.")


__all__ = [
    "Any",
    "Bool",
    "Checkpoints",
    "Config",
    "ContentsManager",
    "Dict",
    "FileContentsManager",
    "GenericCheckpointsMixin",
    "GenericFileCheckpoints",
    "HasTraits",
    "Instance",
    "Integer",
    "TraitError",
    "Unicode",
    "from_dict",
    "import_item",
    "new_code_cell",
    "new_markdown_cell",
    "new_notebook",
    "new_raw_cell",
    "reads",
    "string_types",
    "strip_transient",
    "to_os_path",
    "validate",
    "writes",
]
