import os
import pytest
import importlib

def test_max_content_length_default():
    # Clear env var to test default
    if 'MAX_CONTENT_LENGTH' in os.environ:
        del os.environ['MAX_CONTENT_LENGTH']
    import app.config as config_module
    importlib.reload(config_module)
    config = config_module.Config()
    assert config.MAX_CONTENT_LENGTH == 16777216

def test_max_content_length_env_var():
    os.environ['MAX_CONTENT_LENGTH'] = '12345678  # comment'
    import app.config as config_module
    importlib.reload(config_module)
    config = config_module.Config()
    assert config.MAX_CONTENT_LENGTH == 12345678

def test_app_starts_without_error():
    import app.config as config_module
    importlib.reload(config_module)
    config = config_module.Config()
    assert config is not None
