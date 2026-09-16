import errno
from pathlib import Path
from unittest.mock import MagicMock
import pytest


def test_dev_server_statreload_handles_memory_error(monkeypatch):
    import app.dev_server as dev_server
    from uvicorn.supervisors.statreload import StatReload

    # Verify StatReload methods are wrapped
    assert StatReload.should_restart == dev_server._safe_should_restart
    assert StatReload.iter_py_files == dev_server._safe_iter_py_files

    # Test 1: iter_py_files suppresses ENOMEM / Cannot allocate memory
    def mock_iter_enomem(self):
        raise OSError(errno.ENOMEM, "Cannot allocate memory")

    dummy = MagicMock(spec=StatReload)
    monkeypatch.setattr(dev_server, "_orig_iter_py_files", mock_iter_enomem)

    # Calling _safe_iter_py_files should not raise OSError
    results = list(dev_server._safe_iter_py_files(dummy))
    assert results == []

    # Test 2: should_restart suppresses ENOMEM and returns None
    def mock_should_restart_enomem(self):
        raise OSError(12, "Cannot allocate memory: '/workspace/backend/app/__pycache__'")

    monkeypatch.setattr(dev_server, "_orig_should_restart", mock_should_restart_enomem)

    res = dev_server._safe_should_restart(dummy)
    assert res is None

    # Test 3: Other unexpected OSErrors are raised as normal
    def mock_other_oserror(self):
        raise OSError(errno.EACCES, "Permission denied")

    monkeypatch.setattr(dev_server, "_orig_should_restart", mock_other_oserror)

    with pytest.raises(OSError) as exc_info:
        dev_server._safe_should_restart(dummy)
    assert exc_info.value.errno == errno.EACCES
