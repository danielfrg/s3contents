import pytest

import s3contents

pytestmark = [pytest.mark.pkg]


def test_import():

    assert s3contents.__version__ is not None
    assert s3contents.__version__ != "0.0.0"
    assert len(s3contents.__version__) > 0
