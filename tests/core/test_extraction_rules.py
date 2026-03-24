from app.core.extraction_rules import extract_test_cases, extract_test_suites
from app.core.parser_rules import parse_feature_file, parse_markdown_file


def test_extract_test_suites_builds_deterministic_suite_id(tmp_path):
    parsed = {
        "suite_name": "  Personal   Settings  ",
        "source_file_path": str(tmp_path / "settings.md"),
        "testcase_blocks": [],
    }

    first = extract_test_suites(parsed)[0]
    second = extract_test_suites(parsed)[0]

    assert first.suite_name == "Personal Settings"
    assert first.source_file_path == str(tmp_path / "settings.md")
    assert first.suite_id == second.suite_id


def test_extract_test_cases_transforms_feature_and_markdown_without_format_branching(tmp_path):
    feature_file = tmp_path / "settings.feature"
    feature_file.write_text(
        "\n".join(
            [
                "Feature: Personal Settings",
                "",
                "Scenario: TC-040 - Open settings",
                "  When user clicks settings",
                "  Then settings modal opens",
            ]
        ),
        encoding="utf-8",
    )
    markdown_file = tmp_path / "history.md"
    markdown_file.write_text(
        "\n".join(
            [
                "# Phase 7 History Management",
                "",
                "### TC-100",
                "**Scenario** Open history tab",
            ]
        ),
        encoding="utf-8",
    )

    parsed_feature = parse_feature_file(feature_file)
    parsed_markdown = parse_markdown_file(markdown_file)

    extracted_cases = extract_test_cases([parsed_feature, parsed_markdown])
    extracted_suites = extract_test_suites([parsed_feature, parsed_markdown])

    assert [suite.suite_name for suite in extracted_suites] == [
        "Personal Settings",
        "Phase 7 History Management",
    ]
    assert [case.testcase_id for case in extracted_cases] == ["TC-040", "TC-100"]
    assert extracted_cases[0].testcase_name == "TC-040 - Open settings"
    assert extracted_cases[1].testcase_name == "Open history tab"
    assert extracted_cases[0].suite_id == extracted_suites[0].suite_id
    assert extracted_cases[1].suite_id == extracted_suites[1].suite_id


def test_extract_test_cases_raises_on_duplicate_testcase_ids_in_one_suite(tmp_path):
    parsed = {
        "suite_name": "Duplicate ID Suite",
        "source_file_path": str(tmp_path / "dup.md"),
        "testcase_blocks": [
            {"testcase_marker": "TC-001", "scenario": "a"},
            {"testcase_marker": "TC-001", "scenario": "b"},
        ],
    }

    try:
        extract_test_cases(parsed)
    except ValueError as exc:
        assert "Duplicate testcase_id in suite" in str(exc)
        assert str(exc).endswith(": TC-001")
    else:
        raise AssertionError("Expected duplicate testcase_id conflict to raise ValueError")


def test_extract_test_cases_skips_unsupported_block_without_testcase_id(tmp_path):
    parsed = {
        "suite_name": "Skip Unsupported",
        "source_file_path": str(tmp_path / "skip.md"),
        "testcase_blocks": [
            {"scenario": "No testcase marker"},
            {"testcase_marker": "TC-555", "scenario": "Valid block"},
        ],
    }

    extracted_cases = extract_test_cases(parsed)

    assert [case.testcase_id for case in extracted_cases] == ["TC-555"]
    assert [case.testcase_name for case in extracted_cases] == ["Valid block"]
