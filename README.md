# Specification
## Overview

**TestWeave** is a **local‑first** test management engine designed to transform written specifications into executable test cycles. The goal is to give testers and developers a consistent way to manage and execute manual tests directly within the tools they already use.

## Key Features

TestWeave focuses on weaving together test specifications and execution history. The core features include:

1. **Scanning** – Reads test cases from various file formats and converts them into executable test items. Planned file types include:

- ```.feature files``` (e.g., Gherkin syntax)
- ```.md Markdown``` documents
- ```.csv``` and ```.xlsx``` spreadsheets
- And Etc...

2. **Test Cycle Management** – Allows users to group test cases into cycles, track progress, and record execution outcomes directly in their repository. Execution history is stored locally so that teams can review past runs without depending on external services.

3. **Manual Test Execution** – Enables testers to run manual test cases and record results within the TestWeave environment.

4. **Report Exporting** – Provides options to export test results in human‑readable formats. HTML and CSV report outputs are planned, enabling easy sharing of test outcomes with stakeholders.

## Current Status

TestWeave is in early development with a Python core skeleton. The current focus is on building the underlying engine and APIs that will eventually power the extensions and plugins. Contributors can expect active changes to the codebase as the architecture and features stabilize.

## Usage

Detailed usage instructions are to be determined (TBU) as the project matures. In future releases, instructions will cover how to:

Configure your project to recognize spec files and scan them into TestWeave.

Create and manage test cycles directly within your editor.

Execute manual test runs and record results locally.

Export reports for distribution or archival.

Until the first public release, testers and developers interested in TestWeave can explore the repository and follow development updates.

## License

© 2026 Willow. All rights reserved.