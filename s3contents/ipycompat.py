"""
Utilities for managing compat between notebook versions.

Taken from: https://github.com/quantopian/pgcontents/blob/master/pgcontents/utils/ipycompat.py
"""

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

# Pick dependencies from either notebook (notebook version<=6) or jupyter_server (jupyterlab, notebook>=7)
ct_mgr_deps_loaded = False
try:
    from notebook.services.contents.checkpoints import (
      Checkpoints,
      GenericCheckpointsMixin,
    )
    from notebook.services.contents.filecheckpoints import GenericFileCheckpoints
    from notebook.services.contents.filemanager import FileContentsManager
    from notebook.services.contents.manager import ContentsManager
    ct_mgr_deps_loaded = True
except ModuleNotFoundError:
    pass

if not ct_mgr_deps_loaded:
    try:
        from jupyter_server.services.contents.checkpoints import (
          Checkpoints,
          GenericCheckpointsMixin,
        )
        from jupyter_server.services.contents.filecheckpoints import GenericFileCheckpoints
        from jupyter_server.services.contents.filemanager import FileContentsManager
        from jupyter_server.services.contents.manager import ContentsManager
        ct_mgr_deps_loaded = True
    except ModuleNotFoundError:
        pass

if not ct_mgr_deps_loaded:
    raise ImportError(
        "Couldn't import ContentsManager from either nootebook or jupyter_server."
        "Make sure that Jupyter Notebook or JupyterLab package is installed."
    )

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
    "validate",
    "writes",
]
