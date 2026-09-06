from __future__ import annotations

import json
from functools import partial
from pathlib import Path
from typing import Final

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox
from pytestqt.qtbot import QtBot

from labelme._widgets.label_dialog import LabelDialog

from ..conftest import close_or_pause
from .conftest import MainWinFactory
from .conftest import click_canvas_fraction
from .conftest import draw_triangle
from .conftest import schedule_on_dialog
from .conftest import show_window_and_wait_for_imagedata

_RAW_FILE: Final[str] = "raw/2011_000003.jpg"
_LABEL_METADATA: Final[dict[str, dict[str, list[str]]]] = {
    "^id_text$": {"type": ["id_iso6346", "unknown"]}
}
_VERTICES: Final = ((0.3, 0.3), (0.6, 0.3), (0.6, 0.6))
_CLOSE_POLYGON_CLICK: Final = _VERTICES[0]
_draw_triangle = partial(draw_triangle, vertices=_VERTICES)


def _combo(*, label_dialog: LabelDialog, name: str) -> QComboBox:
    matches = [
        combo
        for combo in label_dialog.findChildren(QComboBox)
        if combo.accessibleName() == name
    ]
    assert matches, f"no metadata combo named {name!r}"
    return matches[0]


def _enter_label(
    *,
    qtbot: QtBot,
    label_dialog: LabelDialog,
    name: str,
    metadata_value: str | None,
) -> None:
    label_dialog.edit.clear()
    qtbot.keyClicks(label_dialog.edit, name)
    qtbot.wait(100)
    if metadata_value is not None:
        combo = _combo(label_dialog=label_dialog, name="type")
        combo.setCurrentIndex(combo.findData(metadata_value))
    qtbot.keyClick(label_dialog.edit, Qt.Key.Key_Enter)


@pytest.mark.gui
def test_label_metadata_applied_to_shape(
    *,
    main_win: MainWinFactory,
    qtbot: QtBot,
    data_path: Path,
    pause: bool,
) -> None:
    win = main_win(
        file_or_dir=str(data_path / _RAW_FILE),
        config_overrides={"label_metadata": _LABEL_METADATA},
    )
    show_window_and_wait_for_imagedata(qtbot=qtbot, win=win)
    canvas = win._canvas_widgets.canvas
    label_dialog = win._label_dialog
    num_shapes_before = len(canvas.shapes)

    _draw_triangle(qtbot=qtbot, win=win)

    schedule_on_dialog(
        label_dialog=label_dialog,
        action=partial(
            _enter_label,
            qtbot=qtbot,
            label_dialog=label_dialog,
            name="id_text",
            metadata_value="id_iso6346",
        ),
    )
    click_canvas_fraction(qtbot=qtbot, canvas=canvas, xy=_CLOSE_POLYGON_CLICK)

    qtbot.waitUntil(lambda: len(canvas.shapes) == num_shapes_before + 1, timeout=3000)

    shape = canvas.shapes[-1]
    assert shape.label == "id_text"
    assert shape.metadata == {"type": "id_iso6346"}

    close_or_pause(qtbot=qtbot, widget=win, pause=pause)


@pytest.mark.gui
def test_metadata_not_shown_in_label_list(
    *,
    main_win: MainWinFactory,
    qtbot: QtBot,
    data_path: Path,
    pause: bool,
) -> None:
    win = main_win(
        file_or_dir=str(data_path / _RAW_FILE),
        config_overrides={"label_metadata": _LABEL_METADATA},
    )
    show_window_and_wait_for_imagedata(qtbot=qtbot, win=win)
    canvas = win._canvas_widgets.canvas
    label_dialog = win._label_dialog
    label_list = win._docks.label_list
    num_shapes_before = len(canvas.shapes)

    _draw_triangle(qtbot=qtbot, win=win)

    schedule_on_dialog(
        label_dialog=label_dialog,
        action=partial(
            _enter_label,
            qtbot=qtbot,
            label_dialog=label_dialog,
            name="id_text",
            metadata_value="unknown",
        ),
    )
    click_canvas_fraction(qtbot=qtbot, canvas=canvas, xy=_CLOSE_POLYGON_CLICK)

    qtbot.waitUntil(lambda: len(canvas.shapes) == num_shapes_before + 1, timeout=3000)

    item = next(
        it
        for it in label_list
        if (s := it.shape()) is not None and s.label == "id_text"
    )
    assert item.text() == "id_text"
    assert "unknown" not in item.text()

    close_or_pause(qtbot=qtbot, widget=win, pause=pause)


@pytest.mark.gui
def test_metadata_survives_save_reload_roundtrip(
    *,
    main_win: MainWinFactory,
    qtbot: QtBot,
    data_path: Path,
    tmp_path: Path,
    pause: bool,
) -> None:
    win = main_win(
        file_or_dir=str(data_path / _RAW_FILE),
        config_overrides={"label_metadata": _LABEL_METADATA, "auto_save": False},
        output_dir=str(tmp_path),
    )
    show_window_and_wait_for_imagedata(qtbot=qtbot, win=win)
    canvas = win._canvas_widgets.canvas
    label_dialog = win._label_dialog
    num_shapes_before = len(canvas.shapes)

    _draw_triangle(qtbot=qtbot, win=win)

    schedule_on_dialog(
        label_dialog=label_dialog,
        action=partial(
            _enter_label,
            qtbot=qtbot,
            label_dialog=label_dialog,
            name="id_text",
            metadata_value="id_iso6346",
        ),
    )
    click_canvas_fraction(qtbot=qtbot, canvas=canvas, xy=_CLOSE_POLYGON_CLICK)

    qtbot.waitUntil(lambda: len(canvas.shapes) == num_shapes_before + 1, timeout=3000)
    assert canvas.shapes[-1].metadata == {"type": "id_iso6346"}

    label_path = str(tmp_path / "2011_000003.json")
    assert win.save_labels(label_path=label_path)

    with open(label_path) as f:
        disk_data = json.load(f)
    id_text_shapes = [s for s in disk_data["shapes"] if s["label"] == "id_text"]
    assert len(id_text_shapes) == 1
    assert id_text_shapes[0]["metadata"] == {"type": "id_iso6346"}

    win._load_file(image_or_label_path=label_path)
    qtbot.waitUntil(
        lambda: any(s.label == "id_text" for s in canvas.shapes), timeout=3000
    )

    reloaded_shape = next(s for s in canvas.shapes if s.label == "id_text")
    assert reloaded_shape.metadata == {"type": "id_iso6346"}

    close_or_pause(qtbot=qtbot, widget=win, pause=pause)