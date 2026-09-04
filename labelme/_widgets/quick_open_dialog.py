from __future__ import annotations

from PySide6 import QtCore
from PySide6 import QtWidgets


class QuickOpenDialog(QtWidgets.QDialog):
    """Single-line dialog for the jump-to-file-and-shape shortcut."""

    def __init__(self, *, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        dialog_name = self.tr("Jump to file and shape")
        self.setWindowTitle(dialog_name)
        self.setAccessibleName(dialog_name)

        self.edit = QtWidgets.QLineEdit()
        self.edit.setPlaceholderText(self.tr("file_name#shape_index"))
        self.edit.setAccessibleName(dialog_name)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.edit)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def popup(self) -> str | None:
        # Select what the previous popup left behind so typing replaces it,
        # exactly like the shape-label dialog.
        self.edit.selectAll()
        self.edit.setFocus(QtCore.Qt.FocusReason.PopupFocusReason)
        if self.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return None
        return self.edit.text().strip()