def test_import():
    import s3contents

    assert s3contents.__version__ is not None
    assert len(s3contents.__version__) > 0
