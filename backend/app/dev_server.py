"""Development server runner with memory-overload protection for Uvicorn's file reloader."""
from __future__ import annotations

import errno
import logging
import uvicorn

import os
from pathlib import Path

logger = logging.getLogger("uvicorn.error")

try:
    from uvicorn.supervisors.statreload import StatReload

    _orig_should_restart = StatReload.should_restart
    _orig_iter_py_files = StatReload.iter_py_files

    def _safe_iter_py_files(self):
        try:
            yield from _orig_iter_py_files(self)
        except OSError as exc:
            if getattr(exc, "errno", None) in (errno.ENOMEM, 12) or "Cannot allocate memory" in str(exc):
                logger.warning("[DEV NOTICE] System memory low; skipped reload file scan.")
                return
            raise

    def _safe_should_restart(self):
        # 1. Process liveness check: if the worker process terminated (OOM, crash, signal),
        # trigger an immediate restart so the server never hangs.
        if getattr(self, "process", None) is not None and not self.process.is_alive():
            logger.error(
                "Uvicorn worker process [%s] exited unexpectedly with exitcode %s. Restarting worker...",
                getattr(self.process, "pid", "unknown"),
                getattr(self.process, "exitcode", "unknown"),
            )
            return [Path("worker_process_died")]

        # 2. As PID 1 in container, reap any reparented zombie child processes.
        try:
            while True:
                pid, _ = os.waitpid(-1, os.WNOHANG)
                if pid <= 0:
                    break
        except (ChildProcessError, OSError):
            pass

        # 3. Safe file change detection with memory error protection.
        try:
            return _orig_should_restart(self)
        except OSError as exc:
            if getattr(exc, "errno", None) in (errno.ENOMEM, 12) or "Cannot allocate memory" in str(exc):
                logger.warning("[DEV NOTICE] System memory low; skipped reload check.")
                return None
            raise

    StatReload.iter_py_files = _safe_iter_py_files
    StatReload.should_restart = _safe_should_restart
except ImportError:
    pass


def main() -> None:
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["app"],
    )


if __name__ == "__main__":
    main()
