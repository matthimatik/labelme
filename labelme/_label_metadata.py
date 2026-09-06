from __future__ import annotations

import re

from loguru import logger


def compile_label_metadata(
    *,
    label_metadata: dict[str, dict[str, list[str]]] | None,
) -> dict[re.Pattern[str], dict[str, list[str]]]:
    # The patterns, metadata keys and option values arrive unvalidated from
    # ~/.labelmerc, so a typo like `id_text-(`, a non-str pattern or key (an
    # unquoted `2024` parses as an int), or a non-list / non-str option (an
    # unquoted `null`) must not take the app down. The str checks are what keep
    # a bytes pattern out: it compiles happily, then raises at match time.
    compiled: dict[re.Pattern[str], dict[str, list[str]]] = {}
    for pattern, metadata in (label_metadata or {}).items():
        if not isinstance(pattern, str):
            logger.warning("Non-str label_metadata pattern: {!r}", pattern)
            continue
        try:
            compiled_pattern = re.compile(pattern)
        except re.error as e:
            logger.warning("Invalid label_metadata pattern {!r}: {}", pattern, e)
            continue
        if metadata is None:
            compiled[compiled_pattern] = {}
            continue
        if not isinstance(metadata, dict):
            logger.warning(
                "label_metadata for {!r} must be a mapping of key to options: {!r}",
                pattern,
                metadata,
            )
            continue
        filtered: dict[str, list[str]] = {}
        for key, options in metadata.items():
            if not isinstance(key, str):
                logger.warning(
                    "Non-str label_metadata key for {!r}: {!r}", pattern, key
                )
                continue
            if options is None:
                filtered[key] = []
                continue
            if not isinstance(options, list):
                logger.warning(
                    "label_metadata options for {!r} must be a list: {!r}",
                    f"{pattern}:{key}",
                    options,
                )
                continue
            str_options = [option for option in options if isinstance(option, str)]
            if len(str_options) != len(options):
                logger.warning(
                    "Non-str label_metadata option for {!r}: {!r}",
                    f"{pattern}:{key}",
                    [option for option in options if not isinstance(option, str)],
                )
            filtered[key] = str_options
        compiled[compiled_pattern] = filtered
    return compiled