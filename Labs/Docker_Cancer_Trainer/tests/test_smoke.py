def test_imports():
    import sklearn, joblib
    assert hasattr(sklearn, "__version__")
