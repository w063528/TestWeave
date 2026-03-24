from app.core.parser_rules import parse_feature_file, parse_markdown_file, parse_spec_file


def test_parse_feature_file_returns_structured_scenarios(tmp_path):
    feature_file = tmp_path / "sample.feature"
    feature_file.write_text(
        "\n".join(
            [
                "Feature: Personal Settings",
                "",
                "  Background:",
                "    Given logged in user",
                "    And selected input file",
                "",
                "  Scenario: TC-040 - Open settings",
                "    When user clicks settings",
                "    Then settings modal opens",
            ]
        ),
        encoding="utf-8",
    )

    parsed = parse_feature_file(feature_file)

    assert parsed["source_format"] == "feature"
    assert parsed["suite_name"] == "Personal Settings"
    assert parsed["background_steps"] == [
        {"keyword": "Given", "text": "logged in user"},
        {"keyword": "And", "text": "selected input file"},
    ]
    assert len(parsed["testcase_blocks"]) == 1
    assert parsed["testcase_blocks"][0]["testcase_marker"] == "TC-040"
    assert parsed["testcase_blocks"][0]["title"] == "TC-040 - Open settings"
    assert parsed["testcase_blocks"][0]["steps"] == [
        {"keyword": "When", "text": "user clicks settings"},
        {"keyword": "Then", "text": "settings modal opens"},
    ]


def test_parse_markdown_file_returns_structured_testcase_blocks(tmp_path):
    markdown_file = tmp_path / "history.md"
    markdown_file.write_text(
        "\n".join(
            [
                "# Phase 7 History Management",
                "",
                "### TC-100",
                "**Scenario** Open history tab",
                "**Given (전제조건)**",
                "- TC-089",
                "**When1 (실행 단계 1)**",
                "- Click history tab",
                "**Then1 (예상 결과 1)**",
                "- History list is visible",
            ]
        ),
        encoding="utf-8",
    )

    parsed = parse_markdown_file(markdown_file)

    assert parsed["source_format"] == "markdown"
    assert parsed["suite_name"] == "Phase 7 History Management"
    assert len(parsed["testcase_blocks"]) == 1
    block = parsed["testcase_blocks"][0]
    assert block["testcase_marker"] == "TC-100"
    assert block["scenario"] == "Open history tab"
    assert block["preconditions"] == ["TC-089"]
    assert block["action_expected_pairs"] == [
        {
            "action_key": "When1",
            "action": "Click history tab",
            "expected_key": "Then1",
            "expected": "History list is visible",
        }
    ]


def test_parse_spec_file_dispatches_by_extension(tmp_path):
    feature_file = tmp_path / "a.feature"
    feature_file.write_text("Feature: A", encoding="utf-8")
    markdown_file = tmp_path / "a.md"
    markdown_file.write_text("# A", encoding="utf-8")

    feature_parsed = parse_spec_file(feature_file)
    markdown_parsed = parse_spec_file(markdown_file)

    assert feature_parsed["source_format"] == "feature"
    assert markdown_parsed["source_format"] == "markdown"
