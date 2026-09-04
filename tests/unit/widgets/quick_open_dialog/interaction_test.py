from __future__ import annotations

from PySide6 import QtWidgets
from pytestqt.qtbot import QtBot

from labelme._widgets.quick_open_dialog import QuickOpenDialog

# Black-box characterization of QuickOpenDialog: behavior is exercised only
# through the public surface (popup(), the public edit widget, and observable
# Qt state), with exec() stubbed so tests run without showing the modal window.


def _popup(
    *,
    dialog: QuickOpenDialog,
    accept: bool,
    text: str,
) -> str | None:
    def fake_exec() -> int:
        dialog.edit.setText(text)
        dialog.edit.selectAll()
        return (
            QtWidgets.QDialog.DialogCode.Accepted
            if accept
            else QtWidgets.QDialog.DialogCode.Rejected
        )

    dialog.exec = fake_exec  # ty: ignore[invalid-assignment]
    return dialog.popup()


def test_default_edit_exists(qtbot: QtBot) -> None:
    dialog = QuickOpenDialog()
    qtbot.addWidget(dialog)
    assert isinstance(dialog.edit, QtWidgets.QLineEdit)


def test_popup_returns_none_when_rejected(qtbot: QtBot) -> None:
    dialog = QuickOpenDialog()
    qtbot.addWidget(dialog)
    assert _popup(dialog=dialog, accept=False, text="a.png#1") is None


def test_popup_returns_trimmed_text_when_accepted(qtbot: QtBot) -> None:
    dialog = QuickOpenDialog()
    qtbot.addWidget(dialog)
    assert (
        _popup(dialog=dialog, accept=True, text="  a.png#1  ")
        == "a.png#1"
    )