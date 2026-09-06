from __future__ import annotations

import re
from typing import cast

from labelme._label_metadata import compile_label_metadata


def test_compile_label_metadata_none_is_empty() -> None:
    assert compile_label_metadata(label_metadata=None) == {}


def test_compile_label_metadata_keeps_the_options_of_a_valid_pattern() -> None:
    compiled = compile_label_metadata(
        label_metadata={"^id_text$": {"type": ["id_iso6346", "unknown"]}}
    )
    (pattern,) = compiled
    assert pattern.pattern == "^id_text$"
    assert compiled[pattern] == {"type": ["id_iso6346", "unknown"]}


def test_compile_label_metadata_drops_an_uncompilable_pattern() -> None:
    assert (
        compile_label_metadata(
            label_metadata={"id_text(": {"type": ["unknown"]}}
        )
        == {}
    )


def test_compile_label_metadata_drops_a_non_str_pattern() -> None:
    # An unquoted numeric key in ~/.labelmerc reaches us as an int.
    label_metadata = cast(
        dict[str, dict[str, list[str]]], {2024: {"type": ["unknown"]}}
    )
    assert compile_label_metadata(label_metadata=label_metadata) == {}


def test_compile_label_metadata_drops_a_bytes_pattern() -> None:
    label_metadata = cast(
        dict[str, dict[str, list[str]]], {b"id_text": {"type": ["unknown"]}}
    )
    assert compile_label_metadata(label_metadata=label_metadata) == {}


def test_compile_label_metadata_keeps_the_valid_patterns_of_a_mixed_spec() -> None:
    compiled = compile_label_metadata(
        label_metadata={
            "id_text(": {"type": ["unknown"]},
            "^id_text$": {"type": ["id_iso6346"]},
        }
    )
    assert [pattern.pattern for pattern in compiled] == ["^id_text$"]


def test_compile_label_metadata_allows_an_empty_options_dict() -> None:
    assert (
        compile_label_metadata(label_metadata={"^id_text$": {}})
        == {re.compile("^id_text$"): {}}
    )


def test_compile_label_metadata_drops_a_non_dict_metadata() -> None:
    label_metadata = cast(
        dict[str, dict[str, list[str]]], {"^id_text$": ["type"]}
    )
    assert compile_label_metadata(label_metadata=label_metadata) == {}


def test_compile_label_metadata_drops_a_non_str_key() -> None:
    label_metadata = cast(
        dict[str, dict[str, list[str]]],
        {"^id_text$": {2024: ["unknown"]}},
    )
    assert compile_label_metadata(label_metadata=label_metadata) == {
        re.compile("^id_text$"): {}
    }


def test_compile_label_metadata_drops_non_str_options_with_a_warning() -> None:
    # An unquoted `null` in a ~/.labelmerc options list reaches us as None.
    label_metadata = cast(
        dict[str, dict[str, list[str]]],
        {"^id_text$": {"type": ["id_iso6346", None]}},
    )
    assert compile_label_metadata(label_metadata=label_metadata) == {
        re.compile("^id_text$"): {"type": ["id_iso6346"]}
    }