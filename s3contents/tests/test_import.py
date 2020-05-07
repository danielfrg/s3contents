def test_import():
    import s3contents

    assert s3contents.__version__ is not None
    assert s3contents.__version__ != "0.0.0"
    assert len(s3contents.__version__) > 0
