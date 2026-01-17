from __future__ import annotations

import unittest

from testweave.core.tcid import (
	extract_tc_id,
	extract_all_tc_ids,
	find_tc_ids,
	is_valid_tc_id,
)


class TestTcId(unittest.TestCase):
    def test_extract_long_form_tc_nnn(self) -> None:
        self.assertEqual(extract_tc_id("Scenario: TC-007 - login"), "TC-007")
        self.assertEqual(extract_tc_id("TC-34 something"), "TC-34")
        self.assertEqual(extract_tc_id("TC-100"), "TC-100")

    def test_extract_long_form_tc_seg_nnn(self) -> None:
        self.assertEqual(extract_tc_id("Scenario: TC-TS10-100 - title"), "TC-TS10-100")
        self.assertEqual(extract_tc_id("Scenario: TC-TS1-1 - title"), "TC-TS1-1")
        self.assertEqual(extract_tc_id("Scenario: TC-TS02-001 - title"), "TC-TS02-001")

    def test_extract_short_form_prefix_digits(self) -> None:
        self.assertEqual(extract_tc_id("C1 그런데 말입니다"), "C1")
        self.assertEqual(extract_tc_id("C02 case"), "C02")
        self.assertEqual(extract_tc_id("C123 case"), "C123")
        self.assertEqual(extract_tc_id("A12 case"), "A12")
        self.assertEqual(extract_tc_id("B034 case"), "B034")
        self.assertEqual(extract_tc_id("AB12 case"), "AB12")
        self.assertEqual(extract_tc_id("R03 regression"), "R03")

    def test_no_match_tc_without_hyphen(self) -> None:
        self.assertIsNone(extract_tc_id("E2E-TC131 - not used"))
        self.assertIsNone(extract_tc_id("TC131 is not accepted"))
        self.assertEqual(extract_tc_id("TC-131 is accepted"), "TC-131")

    def test_word_boundaries(self) -> None:
        self.assertIsNone(extract_tc_id("XTC-001Y"))
        self.assertIsNone(extract_tc_id("preC02post"))
        self.assertEqual(extract_tc_id("pre C02 post"), "C02")

    def test_extract_all(self) -> None:
        text = "Run TC-001 then C02 then TC-TS02-003 then AB12"
        self.assertEqual(extract_all_tc_ids(text), ["TC-001", "C02", "TC-TS02-003", "AB12"])

    def test_find_with_positions(self) -> None:
        text = "Hello TC-007 world"
        matches = find_tc_ids(text)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].tc_id, "TC-007")
        self.assertEqual(text[matches[0].start : matches[0].end], "TC-007")

    def test_is_valid(self) -> None:
        ok = [
            "TC-0",
            "TC-007",
            "TC-999",
            "TC-TS02-001",
            "TC-TS1-1",
            "C1",
            "C02",
            "C123",
            "AB12",
            "R03",
        ]
        bad = [
            "",
            "TC131",
            "tc-001",
            "C",
            "C1234",
            "ABCDE1",
            "TC-TS-001",
            "TC--001",
        ]
        for v in ok:
            self.assertTrue(is_valid_tc_id(v), f"expected valid: {v}")
        for v in bad:
            self.assertFalse(is_valid_tc_id(v), f"expected invalid: {v}")


if __name__ == "__main__":
    unittest.main()