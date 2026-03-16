---
적용: 항상
---

# TestWeave Project Rules

This file defines the repository-level working rules for AI coding assistants operating inside the TestWeave repository.

TestWeave is a **Manual Test Management Engine**.

AI assistants must follow these rules before generating or modifying code.

---

# Source of Truth

Before coding, AI assistants must read:

1. AGENTS.md
2. docs/README.md
3. docs/AI_CONTEXT.md
4. docs/99_ai_rules/*
5. docs/04_engine/*
6. docs/05_project_process/mvp_tasks.md

Documentation is the source of truth.

If code conflicts with documentation, documentation wins.

---

# AI Collaboration Model

Codex builds.  
Junie doubts.  
pytest decides.  
The user approves.

---

# Task Selection

The canonical backlog is:

docs/05_project_process/mvp_tasks.md

Rules:

- select the highest priority unfinished task
- do not skip earlier tasks
- implement one coherent feature slice at a time

---

# Repository Structure

Follow architecture rules defined in:

docs/04_engine/code_structure.md

Expected structure:

app/
  main.py
  web/
  core/
  models/
  services/
  storage/
  report/

tests/

---

# Git Workflow

Never commit directly to main.

Always work on branch:

codex_working/<feature>

Pull requests must target:

codex_working/* → main

Merge strategy:

merge commit only

---

# Commit Messages

Use Conventional Commits.

Allowed types:

feat  
fix  
docs  
test  
refactor  
chore  

---

# Testing Rules

Every feature must include tests.

Tests must be derived from:

- repository documentation
- domain rules
- MVP task requirements

Tests must not be derived only from current implementation behavior.

Testing tool:

pytest

---

# Traceability

Code implementing requirements must include GHERKIN comments.

Example:

# GHERKIN-ID: TW-XXXX-001

---

# Safety Rules

Stop and report if:

- documentation conflicts
- architecture instructions are ambiguous
- workflow rules would be violated

---

© 2026 Willow Company. All rights reserved.

Project: TestWeave  
Document: project_rules.md

Last Updated: 2026-03-15 19:53 KST  
Author: Willow Company
---