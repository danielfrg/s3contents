try:
    # only available in notebook < 7
    from notebook.services.contents.tests.test_manager import TestContentsManager
    from notebook.services.contents.tests.test_largefilemanager import (
        TestLargeFileManager,
    )
except ImportError:
    class TestContentsManager(object):
        pass


    class TestLargeFileManager(object):
        pass
