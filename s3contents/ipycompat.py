"""
Utilities for managing compat between notebook versions.

Taken from: https://github.com/quantopian/pgcontents/blob/master/pgcontents/utils/ipycompat.py
"""
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
    from notebook.base.handlers import AuthenticatedFileHandler
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
        from jupyter_server.base.handlers import AuthenticatedFileHandler
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
    default,
)
from traitlets.config import Config


def import_item(name):
    """Import and return ``bar`` given the string ``foo.bar``.

    Calling ``bar = import_item("foo.bar")`` is the functional equivalent of
    executing the code ``from foo import bar``.

    Parameters
    ----------
    name : string
      The fully qualified name of the module/package being imported.

    Returns
    -------
    mod : module object
       The module that was imported.
    """

    parts = name.rsplit('.', 1)
    if len(parts) == 2:
        # called with 'foo.bar....'
        package, obj = parts
        module = __import__(package, fromlist=[obj])
        try:
            pak = getattr(module, obj)
        except AttributeError:
            raise ImportError('No module named %s' % obj)
        return pak
    else:
        # called with un-dotted string
        return __import__(parts[0])

string_types = (str,)

__all__ = [
    "Any",
    "Bool",
    "Checkpoints",
    "Config",
    "ContentsManager",
    "AuthenticatedFileHandler",
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
    "default",
    "writes",
]
