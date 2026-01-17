from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class TcIdMatch:
    tc_id: str
    start: int
    end: int


# -----------------------------------------------------------------------------
# TC ID Rules (TestWeave)
# -----------------------------------------------------------------------------
# 1) Long form:
#    - TC-NNN
#    - TC-<SEG>-NNN
#    where <SEG> is 1..6 alnum chars and MUST contain at least one digit
#    (e.g., TS02, TS10, TS1, A1B2)
#
# 2) Short form:
#    - [A-Z]{1,4}\d{1,3}  (e.g., C1, C02, C123, A12, B034, AB12, R03)
#    but explicitly exclude "TC" prefix to avoid matching "TC131" (no hyphen).
#
# Notes:
# - Leading zeros are allowed
# - Numeric range is syntactically 0..999 via \d{1,3}

# Segment that contains at least one digit, length 1..6, chars A-Z0-9
_SEG_WITH_DIGIT_RE = r"(?=[A-Z0-9]{1,6}\d)[A-Z0-9]{1,6}"

_LONG_FORM_RE = rf"TC-(?:{_SEG_WITH_DIGIT_RE}-)?\d{{1,3}}"
_SHORT_FORM_RE = r"(?!TC)[A-Z]{1,4}\d{1,3}"

TC_ID_REGEX = re.compile(rf"\b({_LONG_FORM_RE}|{_SHORT_FORM_RE})\b")


def extract_tc_id(text: str) -> str | None:
    m = TC_ID_REGEX.search(text)
    return m.group(1) if m else None


def extract_all_tc_ids(text: str) -> list[str]:
    return [m.group(1) for m in TC_ID_REGEX.finditer(text)]


def find_tc_ids(text: str) -> list[TcIdMatch]:
    out: list[TcIdMatch] = []
    for m in TC_ID_REGEX.finditer(text):
        out.append(TcIdMatch(tc_id=m.group(1), start=m.start(1), end=m.end(1)))
    return out


def is_valid_tc_id(tc_id: str) -> bool:
    return TC_ID_REGEX.fullmatch(tc_id) is not None


def filter_valid_tc_ids(values: Iterable[str]) -> list[str]:
    return [v for v in values if is_valid_tc_id(v)]


def normalize_tc_id(tc_id: str) -> str:
    return tc_id.strip()