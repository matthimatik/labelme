from __future__ import annotations

from collections.abc import Callable

from PySide6 import QtWidgets
from pytestqt.qtbot import QtBot

from labelme._widgets.label_dialog import LabelDialog
from labelme._widgets.label_dialog import LabelDialogEntry
from labelme._widgets.label_dialog import LabelDialogField

_METADATA: dict[str, dict[str, list[str]]] = {
    "^id_text$": {
        "text_orientation": ["horizontal", "vertical"],
        "type": ["id_iso6346", "unknown"],
    },
    "^registration_plate$": {"country": ["germany", "uk"]},
}


def _add_dialog(qtbot: QtBot, /, *, dialog: LabelDialog) -> LabelDialog:
    qtbot.addWidget(dialog)
    return dialog


def _combo(*, dialog: LabelDialog, name: str) -> QtWidgets.QComboBox:
    matches = [
        combo
        for combo in dialog.findChildren(QtWidgets.QComboBox)
        if combo.accessibleName() == name
    ]
    assert matches, f"no metadata combo named {name!r}"
    return matches[0]


def _run_popup(
    *,
    dialog: LabelDialog,
    accept: bool,
    at_show: Callable[[LabelDialog], None] | None,
    text: str | None,
    flags: dict[str, bool] | None,
    metadata: dict[str, object] | None,
    group_id: int | None,
    description: str | None,
    locked: tuple[LabelDialogField, ...],
) -> LabelDialogEntry | None:
    code = (
        QtWidgets.QDialog.DialogCode.Accepted
        if accept
        else QtWidgets.QDialog.DialogCode.Rejected
    )

    def fake_exec() -> int:
        if at_show is not None:
            at_show(dialog)
        return code

    dialog.exec = fake_exec  # ty: ignore[invalid-assignment]
    return dialog.popup(
        text=text,
        move=False,
        flags=flags,
        metadata=metadata,
        group_id=group_id,
        description=description,
        locked=locked,
    )


def test_update_metadata_builds_a_combo_per_matching_key(*, qtbot: QtBot) -> None:
    dialog = _add_dialog(qtbot, dialog=LabelDialog(metadata=_METADATA))

    dialog._update_metadata("id_text")

    assert list(dialog._metadata_combos) == ["text_orientation", "type"]
    combo = dialog._metadata_combos["type"]
    assert [combo.itemText(i) for i in range(combo.count())] == [
        "(unset)",
        "id_iso6346",
        "unknown",
    ]
    assert combo.currentData() is None


def test_update_metadata_builds_no_combo_for_an_unmatched_label(
    *, qtbot: QtBot
) -> None:
    dialog = _add_dialog(qtbot, dialog=LabelDialog(metadata=_METADATA))

    dialog._update_metadata("logo")

    assert dialog._metadata_combos == {}


def test_set_metadata_combos_preselects_the_provided_value(*, qtbot: QtBot) -> None:
    dialog = _add_dialog(qtbot, dialog=LabelDialog(metadata=_METADATA))

    dialog._set_metadata_combos(
        text="id_text", metadata={"text_orientation": "vertical"}
    )

    combo = dialog._metadata_combos["text_orientation"]
    assert combo.currentData() == "vertical"


def test_collect_metadata_keeps_provided_keys_without_a_combo(*, qtbot: QtBot) -> None:
    dialog = _add_dialog(qtbot, dialog=LabelDialog(metadata=_METADATA))
    dialog._provided_metadata = {"type": "id_iso6346", "extra": 7}

    with_choice = dialog._collect_metadata()

    dialog._set_metadata_combos(text="logo", metadata={})
    without_combo = dialog._collect_metadata()

    assert with_choice == {"type": "id_iso6346", "extra": 7}
    assert without_combo == {"type": "id_iso6346", "extra": 7}


def test_popup_accepts_a_new_shape_with_chosen_metadata(*, qtbot: QtBot) -> None:
    dialog = _add_dialog(
        qtbot,
        dialog=LabelDialog(
            labels=["id_text"], metadata={"^id_text$": {"type": ["id_iso6346"]}}
        ),
    )

    def choose_type(d: LabelDialog) -> None:
        _combo(dialog=d, name="type").setCurrentIndex(
            _combo(dialog=d, name="type").findData("id_iso6346")
        )

    entry = _run_popup(
        dialog=dialog,
        accept=True,
        at_show=choose_type,
        text="id_text",
        flags=None,
        metadata=None,
        group_id=None,
        description=None,
        locked=(),
    )

    assert entry is not None
    assert entry.metadata == {"type": "id_iso6346"}


def test_popup_accepts_unset_metadata_as_none(*, qtbot: QtBot) -> None:
    dialog = _add_dialog(
        qtbot,
        dialog=LabelDialog(
            labels=["id_text"], metadata={"^id_text$": {"type": ["id_iso6346"]}}
        ),
    )

    entry = _run_popup(
        dialog=dialog,
        accept=True,
        at_show=None,
        text="id_text",
        flags=None,
        metadata=None,
        group_id=None,
        description=None,
        locked=(),
    )

    assert entry is not None
    assert entry.metadata == {"type": None}


def test_popup_edit_preserves_metadata_keys_without_a_combo(*, qtbot: QtBot) -> None:
    dialog = _add_dialog(
        qtbot,
        dialog=LabelDialog(
            labels=["id_text"], metadata={"^id_text$": {"type": ["id_iso6346"]}}
        ),
    )

    entry = _run_popup(
        dialog=dialog,
        accept=True,
        at_show=None,
        text="id_text",
        flags=None,
        metadata={"type": "id_iso6346", "extra": "kept"},
        group_id=None,
        description=None,
        locked=(),
    )

    assert entry is not None
    assert entry.metadata == {"type": "id_iso6346", "extra": "kept"}


def test_popup_locked_metadata_disables_the_combo(*, qtbot: QtBot) -> None:
    observed: dict[str, bool] = {}
    dialog = _add_dialog(
        qtbot,
        dialog=LabelDialog(
            labels=["id_text"], metadata={"^id_text$": {"type": ["id_iso6346"]}}
        ),
    )

    def check_disabled(d: LabelDialog) -> None:
        observed["enabled"] = _combo(dialog=d, name="type").isEnabled()

    _run_popup(
        dialog=dialog,
        accept=True,
        at_show=check_disabled,
        text="id_text",
        flags=None,
        metadata=None,
        group_id=None,
        description=None,
        locked=("metadata",),
    )

    assert observed["enabled"] is False


def test_metadata_field_is_part_of_the_get_field_widgets_contract(
    *, qtbot: QtBot
) -> None:
    dialog = _add_dialog(qtbot, dialog=LabelDialog(metadata=_METADATA))

    assert "metadata" in dialog._get_field_widgets()


def test_metadata_combos_are_rebuilt_with_matching_label_change(
    *, qtbot: QtBot
) -> None:
    dialog = _add_dialog(qtbot, dialog=LabelDialog(metadata=_METADATA))

    dialog._update_metadata("id_text")
    type_combo = dialog._metadata_combos["type"]
    type_combo.setCurrentIndex(type_combo.findData("unknown"))

    dialog._update_metadata("registration_plate")

    assert list(dialog._metadata_combos) == ["country"]
    # The choice made for an id_text key must not leak into the plate popup.
    plate_combo = dialog._metadata_combos["country"]
    assert plate_combo.currentData() is None