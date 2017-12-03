import os
import pytest


def mark_class(marker):
    '''Workaround for https://github.com/pytest-dev/pytest/issues/568'''
    import types
    def copy_func(f):
        try:
            return types.FunctionType(f.__code__, f.__globals__,
                                      name=f.__name__, argdefs=f.__defaults__,
                                      closure=f.__closure__)
        except AttributeError:
            return types.FunctionType(f.func_code, f.func_globals,
                                      name=f.func_name,
                                      argdefs=f.func_defaults,
                                      closure=f.func_closure)

    def mark(cls):
        for method in dir(cls):
            if method.startswith('test_'):
                f = copy_func(getattr(cls, method))
                setattr(cls, method, marker(f))
        return cls
    return mark

RUN_GCSFS_TESTS = "RUN_GCSFS_TESTS" not in os.environ
GCS_TEST = mark_class(pytest.mark.skipif(RUN_GCSFS_TESTS, reason="Only run GCS if tell to"))
