---
적용: 항상
---

# TestWeave Project Rules

This file defines the repository-level working rules for AI coding assistants operating inside the TestWeave repository.

It is written for multi-agent collaboration using:

- Codex
- Junie
- pytest
- the user as final approver

TestWeave is a local-first, browser-driven Manual Test Management Engine.

---

## 1. Source of Truth

Repository documentation is the source of truth.

Before generating or modifying code, AI assistants must read and follow:

1. docs/README.md
2. docs/AI_CONTEXT.md
3. docs/99_ai_rules/ai_rules.md
4. docs/99_ai_rules/definition_of_done.md
5. docs/99_ai_rules/mvp_completion_contract.md
6. docs/99_ai_rules/ai_execution_loop.md
7. docs/05_project_process/mvp_tasks.md
8. docs/04_engine/code_structure.md
9. docs/04_engine/testing_strategy.md

If any conflict exists between code and documentation, documentation takes priority.

If two docs conflict and priority is unclear, stop and report the blocker.

---

## 2. AI Collaboration Model

TestWeave uses the following collaboration model.

Codex builds.  
Junie doubts.  
pytest decides.  
The user approves.

### Codex

Responsibilities:

- read documentation and select the next MVP task
- implement one coherent feature slice
- write minimum required tests
- update docs/05_project_process/mvp_tasks.md
- open or update pull requests

### Junie

Responsibilities:

- review Codex changes against documentation
- identify architecture violations
- strengthen tests
- propose regression and edge-case tests
- question assumptions or incomplete implementations
- check that modified documentation files update the footer timestamp

### pytest

Responsibilities:

- act as the automated verification gate
- determine whether the implementation passes test validation

### User

Responsibilities:

- approve final merge
- decide scope changes when necessary

---

## 3. Task Selection Rule

The canonical backlog is:

docs/05_project_process/mvp_tasks.md

Rules:

- choose the highest priority unfinished MVP task
- do not skip earlier tasks
- implement one feature slice at a time
- update task status when work progresses

Codex must not invent new roadmap items.

---

## 4. Repository Structure Rule

Follow the structure defined in:

docs/04_engine/code_structure.md

Expected structure:

app/
  main.py
  web/
    routes/
    templates/
    static/
  core/
  models/
  services/
  storage/
  report/

tests/

Layer rules:

- core contains deterministic business rules
- models contain domain entities
- services contain workflows
- storage contains SQLite persistence
- web contains FastAPI routes and templates
- report contains aggregation logic

---

## 5. Approved MVP Stack

The TestWeave MVP stack:

- Python
- FastAPI
- Uvicorn
- Jinja2
- HTMX
- Alpine.js
- SQLite
- pytest

Do not introduce additional frameworks unless documentation explicitly changes.

---

## 6. Git Workflow

Rules:

- never commit directly to main
- always work on branch codex_working/<feature>
- open pull requests to main
- follow .github/pull_request_template.md
- merge strategy: merge commit only

---

## 7. Commit Messages

Use Conventional Commits.

Allowed types:

feat  
fix  
docs  
test  
refactor  
chore

Examples:

feat: add test run workflow  
fix: resolve tcid uniqueness validation  
docs: update project rules  
test: add tcid generator tests

---

## 8. Gherkin Traceability

All requirement logic must maintain traceability.

Requirement → Gherkin Scenario → TestCase → TestSuite → TestRun → TestResult → Report

Example:

```python
# GHERKIN-ID: TW-XXXX-001
# Given ...
# When ...
# Then ...
```

---

## 9. Testing Rule

Every feature must include tests.

Rules:

- write tests for new behavior
- update tests when behavior changes
- tests must pass before merge

Critical rule:

Tests must be derived from repository documentation and MVP task requirements, not merely from existing implementation behavior.

---

## 10. Review Flow

1. Codex implements a feature slice
2. Codex writes minimum tests
3. Codex updates task status
4. Junie reviews the pull request
5. Junie proposes improvements and missing tests
6. Codex applies fixes
7. pytest runs
8. passing code is submitted for approval
9. user approves merge

If Junie feedback conflicts with documentation, documentation wins.

---

## 11. Safety Rules

Stop and report if:

- documentation conflicts
- required rule is missing
- architecture placement is unclear
- workflow rules would be violated

Do not guess missing behavior.

---

## 12. Final Rule

AI assistants must:

- read documentation before coding
- follow repository structure
- maintain traceability
- write tests
- respect Git workflow
- collaborate using the Codex/Junie model

If instructions conflict with repository documentation, stop and report.

---
© 2026 Willow Company. All rights reserved.

Project: TestWeave  
Document: project_rules.md

Last Updated: 2026-03-15 19:02 KST
Author: Willow Company
---