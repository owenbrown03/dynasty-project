import importlib

import pytest

from app.core import broker as broker_module


def test_iter_task_module_names_uses_package_prefix(
    monkeypatch,
):
    captured: dict[str, object] = {}

    def fake_iter_modules(path, prefix):
        captured["path"] = path
        captured["prefix"] = prefix
        return [
            (None, "app.tasks.alpha", False),
            (None, "app.tasks.beta", False),
        ]

    monkeypatch.setattr(
        broker_module.pkgutil,
        "iter_modules",
        fake_iter_modules,
    )

    package = type(
        "FakePackage",
        (),
        {
            "__path__": ["fake/tasks"],
            "__name__": "app.tasks",
        },
    )()

    assert broker_module.iter_task_module_names(package) == [
        "app.tasks.alpha",
        "app.tasks.beta",
    ]
    assert captured == {
        "path": ["fake/tasks"],
        "prefix": "app.tasks.",
    }


def test_load_task_modules_imports_each_name(
    monkeypatch,
):
    imported: list[str] = []

    monkeypatch.setattr(
        broker_module,
        "iter_task_module_names",
        lambda package: [
            "app.tasks.alpha",
            "app.tasks.beta",
        ],
    )
    monkeypatch.setattr(
        importlib,
        "import_module",
        lambda name: imported.append(name),
    )

    broker_module.load_task_modules(object())

    assert imported == [
        "app.tasks.alpha",
        "app.tasks.beta",
    ]


def test_load_task_modules_reraises_import_errors(
    monkeypatch,
):
    monkeypatch.setattr(
        broker_module,
        "iter_task_module_names",
        lambda package: ["app.tasks.alpha"],
    )

    def fake_import_module(name):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        importlib,
        "import_module",
        fake_import_module,
    )

    with pytest.raises(
        RuntimeError,
        match="boom",
    ):
        broker_module.load_task_modules(object())
